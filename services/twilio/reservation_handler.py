import asyncio
import re
import traceback
from datetime import datetime, date, timedelta
from routes.bot import validar_fecha_reserva, verificar_capacidad_disponible
from services.twilio.messaging import send_whatsapp_message
from utils.session_manager import save_session
from db.supabase_client import supabase_client
from services.twilio.intelligent_parser import intelligent_parser
import logging
import locale

logger = logging.getLogger(__name__)

# Mapeo de días de la semana en español
DIAS_SEMANA = {
    'Monday': 'lunes',
    'Tuesday': 'martes', 
    'Wednesday': 'miércoles',
    'Thursday': 'jueves',
    'Friday': 'viernes',
    'Saturday': 'sábado',
    'Sunday': 'domingo'
}

# Mapeo de meses en español
MESES = {
    'January': 'enero',
    'February': 'febrero',
    'March': 'marzo',
    'April': 'abril',
    'May': 'mayo',
    'June': 'junio',
    'July': 'julio',
    'August': 'agosto',
    'September': 'septiembre',
    'October': 'octubre',
    'November': 'noviembre',
    'December': 'diciembre'
}

def format_date_spanish(fecha_obj):
    """Formatea una fecha en español"""
    try:
        # Obtener día de la semana en inglés
        dia_semana_en = fecha_obj.strftime("%A")
        # Obtener mes en inglés
        mes_en = fecha_obj.strftime("%B")
        # Obtener día y año
        dia = fecha_obj.strftime("%d")
        año = fecha_obj.strftime("%Y")
        
        # Traducir al español
        dia_semana_es = DIAS_SEMANA.get(dia_semana_en, dia_semana_en.lower())
        mes_es = MESES.get(mes_en, mes_en.lower())
        
        return f"{dia_semana_es} {dia} de {mes_es} de {año}"
    except Exception as e:
        logger.error(f"Error formateando fecha en español: {str(e)}")
        return fecha_obj.strftime("%d/%m/%Y")

# Estados del flujo de reserva
RESERVATION_STATES = {
    'INICIO': 'inicio',
    'ESPERANDO_FECHA': 'esperando_fecha', 
    'ESPERANDO_PERSONAS': 'esperando_personas',
    'ESPERANDO_CONFIRMACION_INICIAL': 'esperando_confirmacion_inicial',  # Nuevo estado
    'ESPERANDO_NOMBRE': 'esperando_nombre',
    'ESPERANDO_TELEFONO': 'esperando_telefono',
    'ESPERANDO_EMAIL': 'esperando_email',
    'ESPERANDO_CONFIRMACION': 'esperando_confirmacion',
    'COMPLETADA': 'completada'
}

def handle_reservation_flow(from_number, message, restaurant_config, session, mensaje_normalizado):
    """
    Maneja el flujo completo de reservas para WhatsApp
    """
    try:
        restaurant_name = restaurant_config.get('nombre', 'el restaurante')
        reservation_state = session.get('reservation_state', RESERVATION_STATES['INICIO'])
        reservation_data = session.get('reservation_data', {})
        
        # LOGGING CRÍTICO PARA DEBUG
        logger.info(f"🔄 FLUJO RESERVA: {from_number} | Estado: {reservation_state} | Mensaje: '{message}'")
        logger.info(f"📊 DATOS ACTUALES: {reservation_data}")
        
        # INICIO DEL FLUJO DE RESERVA - CON PARSING INTELIGENTE
        if reservation_state == RESERVATION_STATES['INICIO']:
            logger.info(f"🚀 INICIANDO FLUJO para {from_number}")
            return start_reservation_flow_intelligent(from_number, message, restaurant_config, session)
        
        # PROCESANDO FECHA
        elif reservation_state == RESERVATION_STATES['ESPERANDO_FECHA']:
            logger.info(f"📅 PROCESANDO FECHA para {from_number}")
            return asyncio.run(process_date_input(from_number, message, restaurant_config, session, reservation_data))
        
        # PROCESANDO CANTIDAD DE PERSONAS
        elif reservation_state == RESERVATION_STATES['ESPERANDO_PERSONAS']:
            logger.info(f"👥 PROCESANDO PERSONAS para {from_number}")
            return asyncio.run(process_persons_input(from_number, message, restaurant_config, session, reservation_data))
        
        # PROCESANDO NOMBRE
        elif reservation_state == RESERVATION_STATES['ESPERANDO_NOMBRE']:
            logger.info(f"👤 PROCESANDO NOMBRE para {from_number}")
            return process_name_input(from_number, message, restaurant_config, session, reservation_data)
        
        # PROCESANDO TELÉFONO
        elif reservation_state == RESERVATION_STATES['ESPERANDO_TELEFONO']:
            logger.info(f"📱 PROCESANDO TELÉFONO para {from_number}")
            return process_phone_input(from_number, message, restaurant_config, session, reservation_data)
        
        # CONFIRMACIÓN INICIAL - Después del parsing inteligente
        elif reservation_state == RESERVATION_STATES['ESPERANDO_CONFIRMACION_INICIAL']:
            logger.info(f"🤖 PROCESANDO CONFIRMACIÓN INICIAL para {from_number}")
            return process_initial_confirmation(from_number, message, restaurant_config, session, reservation_data)
        
        # PROCESANDO EMAIL - CRÍTICO
        elif reservation_state == RESERVATION_STATES['ESPERANDO_EMAIL']:
            logger.info(f"📧 PROCESANDO EMAIL para {from_number} - FLUJO CRÍTICO")
            return process_email_input(from_number, message, restaurant_config, session, reservation_data)
        
        # CONFIRMACIÓN FINAL
        elif reservation_state == RESERVATION_STATES['ESPERANDO_CONFIRMACION']:
            logger.info(f"✅ PROCESANDO CONFIRMACIÓN para {from_number}")
            return asyncio.run(process_confirmation(from_number, message, restaurant_config, session, reservation_data))
        
        else:
            logger.warning(f"⚠️ ESTADO NO RECONOCIDO: {reservation_state} para {from_number}")
            return start_reservation_flow(from_number, restaurant_config, session)
            
    except Exception as e:
        logger.error(f"💥 ERROR EN FLUJO DE RESERVA para {from_number}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return reset_reservation_flow(from_number, restaurant_config, session, "Hubo un error. Iniciemos el proceso de reserva nuevamente.")

def start_reservation_flow(from_number, restaurant_config, session):
    """Inicia el flujo de reserva"""
    restaurant_name = restaurant_config.get('nombre', 'el restaurante')
    restaurant_id = restaurant_config.get('id')
    
    # Actualizar estado de la sesión
    session['reservation_state'] = RESERVATION_STATES['ESPERANDO_FECHA']
    session['reservation_data'] = {}
    
    # Guardar sesión
    save_session(from_number, session, restaurant_id)
    
    mensaje = f"¡Perfecto! Te ayudo a hacer una reserva en {restaurant_name}. 📅\n\n"
    mensaje += "Por favor, dime para qué **fecha** quieres hacer la reserva.\n\n"
    mensaje += "Puedes escribir:\n"
    mensaje += "• **Hoy** o **mañana**\n"
    mensaje += "• **DD/MM/YYYY** (ej: 25/05/2025)\n"
    mensaje += "• **25 de mayo** o **viernes**"
    
    send_whatsapp_message(from_number, mensaje, restaurant_config)
    return None  # No enviar mensaje de debug al cliente

def start_reservation_flow_intelligent(from_number, message, restaurant_config, session):
    """Inicia el flujo de reserva con parsing inteligente del mensaje completo"""
    restaurant_name = restaurant_config.get('nombre', 'el restaurante')
    restaurant_id = restaurant_config.get('id')
    
    logger.info(f"🔍 INTELLIGENT START: Analizando mensaje inicial: '{message}'")
    
    try:
        # Usar parser inteligente para extraer información completa
        parsed_data = intelligent_parser.parse_complete_message(message)
        
        logger.info(f"📊 PARSING RESULT: {parsed_data}")
        
        # Inicializar datos de reserva
        reservation_data = {}
        next_state = None
        
        # Procesar la información extraída
        if parsed_data['confidence'] >= 0.3:  # Si encontró algo útil
            if parsed_data['fecha']:
                reservation_data['fecha'] = parsed_data['fecha']
                logger.info(f"✅ Fecha extraída: {parsed_data['fecha']}")
            
            if parsed_data['hora']:
                reservation_data['hora'] = parsed_data['hora']
                logger.info(f"✅ Hora extraída: {parsed_data['hora']}")
                
            if parsed_data['personas']:
                reservation_data['personas'] = parsed_data['personas']
                logger.info(f"✅ Personas extraídas: {parsed_data['personas']}")
        
        # Determinar próximo estado basado en qué información falta
        if not reservation_data.get('fecha'):
            next_state = RESERVATION_STATES['ESPERANDO_FECHA']
        elif not reservation_data.get('personas'):
            next_state = RESERVATION_STATES['ESPERANDO_PERSONAS']
        else:
            # Tenemos fecha y personas, pero necesitamos confirmación antes de continuar
            if parsed_data['confidence'] >= 0.7 and len(parsed_data['extracted_info']) >= 2:
                # Información suficiente, solicitar confirmación inicial
                next_state = RESERVATION_STATES['ESPERANDO_CONFIRMACION_INICIAL']
            else:
                # Información insuficiente, pedir más datos
                next_state = RESERVATION_STATES['ESPERANDO_FECHA']
        
        # Actualizar sesión
        session['reservation_state'] = next_state
        session['reservation_data'] = reservation_data
        save_session(from_number, session, restaurant_id)
        
        # Generar mensaje de respuesta inteligente
        mensaje = intelligent_parser.generate_confirmation_message(parsed_data, restaurant_name)
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        logger.info(f"🚀 INTELLIGENT START COMPLETE: Próximo estado: {next_state}")
        
        return None  # No enviar mensaje de debug al cliente
        
    except Exception as e:
        logger.error(f"❌ ERROR in intelligent parsing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback al flujo tradicional si el parser inteligente falla
        logger.info("🔄 Fallback: usando flujo de reserva tradicional")
        return start_reservation_flow(from_number, restaurant_config, session)

async def process_date_input(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la entrada de fecha con parsing inteligente mejorado"""
    restaurant_name = restaurant_config.get('nombre', 'el restaurante')
    
    logger.info(f"🔍 DATE INPUT: Procesando fecha: '{message}'")
    
    fecha_str = None
    
    try:
        # Usar parser inteligente para extraer fecha del mensaje
        parsed_data = intelligent_parser.parse_complete_message(message)
        
        # Si el parser inteligente encontró una fecha, usarla
        if parsed_data['fecha']:
            fecha_str = parsed_data['fecha']
            logger.info(f"✅ Fecha extraída por parser inteligente: {fecha_str}")
        else:
            # Fallback al método manual existente
            message_lower = message.lower()
            hoy = date.today()
            
            if any(word in message_lower for word in ['hoy', 'today']):
                fecha_str = hoy.strftime("%d/%m/%Y")
            elif any(word in message_lower for word in ['mañana', 'tomorrow']):
                tomorrow = hoy + timedelta(days=1)
                fecha_str = tomorrow.strftime("%d/%m/%Y")
            else:
                # Buscar patrón de fecha tradicional
                date_pattern = r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b'
                match = re.search(date_pattern, message)
                if match:
                    day, month, year = match.groups()
                    fecha_str = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    logger.info(f"✅ Fecha extraída por regex: {fecha_str}")
        
        if not fecha_str:
            mensaje = f"No pude entender la fecha. 📅\n\n"
            mensaje += "Por favor, dime la fecha de otra manera:\n"
            mensaje += "• **Hoy** o **mañana**\n"
            mensaje += "• **DD/MM/YYYY** (ej: 25/05/2025)\n"
            mensaje += "• **25 de mayo**"
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return None
        
        # Validar fecha
        fecha_valida, mensaje_error = await validar_fecha_reserva(fecha_str)
        
        if not fecha_valida:
            send_whatsapp_message(from_number, mensaje_error, restaurant_config)
            return None  # No enviar mensaje de debug al cliente
        
        # Guardar fecha y pasar al siguiente paso
        reservation_data['fecha'] = fecha_str
        session['reservation_data'] = reservation_data
        session['reservation_state'] = RESERVATION_STATES['ESPERANDO_PERSONAS']
        
        # Guardar sesión
        restaurant_id = restaurant_config.get('id')
        save_session(from_number, session, restaurant_id)
        
        try:
            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
            fecha_formateada = format_date_spanish(fecha_obj)
        except:
            fecha_formateada = fecha_str
        
        mensaje = f"¡Excelente! Reserva para el {fecha_formateada}. 👥\n\n"
        mensaje += "¿Para cuántas **personas** será la reserva?\n\n"
        mensaje += "Ejemplo: 4 personas"
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente
        
    except Exception as e:
        logger.error(f"❌ ERROR in process_date_input: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback con mensaje genérico
        mensaje = f"Hubo un problema procesando la fecha. 📅\n\n"
        mensaje += "Por favor, intenta escribir la fecha nuevamente:\n"
        mensaje += "• **Hoy** o **mañana**\n"
        mensaje += "• **DD/MM/YYYY** (ej: 25/05/2025)"
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None

async def interpret_date_with_ai(message):
    """Usa IA para interpretar fechas en lenguaje natural"""
    try:
        from services.ai.deepseek_service import interpret_natural_date
        return await interpret_natural_date(message)
    except Exception as e:
        logger.error(f"Error interpretando fecha con IA: {str(e)}")
        return None

async def process_persons_input(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la entrada de cantidad de personas con parsing inteligente"""
    restaurant_name = restaurant_config.get('nombre', 'el restaurante')
    
    logger.info(f"🔍 PERSONS INPUT: Procesando personas: '{message}'")
    
    personas = None
    
    try:
        # Usar parser inteligente primero
        parsed_data = intelligent_parser.parse_complete_message(message)
        
        if parsed_data['personas']:
            personas = parsed_data['personas']
            logger.info(f"✅ Personas extraídas por parser inteligente: {personas}")
        else:
            # Fallback al método manual existente
            numbers = re.findall(r'\b(\d+)\b', message)
            
            if numbers:
                try:
                    personas = int(numbers[0])
                    logger.info(f"✅ Personas extraídas por regex: {personas}")
                except ValueError:
                    pass
        
        if not personas:
            mensaje = "No pude identificar la cantidad de personas. 👥\n\n"
            mensaje += "Por favor, dime un número.\nEjemplo: 4 personas"
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return None  # No enviar mensaje de debug al cliente
        
        if personas <= 0:
            mensaje = "La cantidad de personas debe ser mayor a 0. 👥\n\n"
            mensaje += "¿Para cuántas personas será la reserva?"
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return None  # No enviar mensaje de debug al cliente
            
        if personas > 20:  # Límite razonable
            mensaje = f"Para reservas de más de 20 personas, por favor contacta directamente con {restaurant_name}.\n\n"
            mensaje += "¿Podrías indicar una cantidad menor o contactarnos por teléfono?"
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return None  # No enviar mensaje de debug al cliente
        
        # Verificar capacidad disponible usando el sistema existente
        fecha_str = reservation_data['fecha']
        hay_capacidad, mensaje_error, capacidad_disponible = await verificar_capacidad_disponible(fecha_str, personas, restaurant_config)
        
        if not hay_capacidad:
            # Ofrecer alternativas inteligentes
            mensaje = f"{mensaje_error}\n\n"
            if capacidad_disponible > 0:
                mensaje += f"💡 **Alternativas disponibles:**\n"
                mensaje += f"• Reducir a {capacidad_disponible} personas\n"
                mensaje += f"• Elegir otra fecha\n\n"
                mensaje += "¿Qué prefieres hacer?"
            else:
                mensaje += "¿Te gustaría elegir otra fecha?"
            
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return None  # No enviar mensaje de debug al cliente
        
        # Guardar personas y continuar
        reservation_data['personas'] = personas
        session['reservation_data'] = reservation_data
        session['reservation_state'] = RESERVATION_STATES['ESPERANDO_NOMBRE']
        
        # Guardar sesión
        restaurant_id = restaurant_config.get('id')
        save_session(from_number, session, restaurant_id)
        
        mensaje = f"¡Perfecto! Reserva para {personas} persona{'s' if personas > 1 else ''} el {reservation_data['fecha']}. ✅\n\n"
        mensaje += "¿Cuál es tu **nombre completo** para la reserva?"
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente
        
    except Exception as e:
        logger.error(f"❌ ERROR in process_persons_input: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback con mensaje genérico
        mensaje = f"Hubo un problema procesando la cantidad de personas. 👥\n\n"
        mensaje += "Por favor, intenta escribir el número de personas nuevamente.\n"
        mensaje += "Ejemplo: 4 personas"
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None

def process_name_input(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la entrada del nombre"""
    
    nombre = message.strip()
    
    if len(nombre) < 2:
        mensaje = "Por favor, proporciona un nombre válido para la reserva. 👤"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente
    
    # Validación adicional: evitar nombres que sean solo comandos comunes
    # EXCLUIR "si" y "sí" porque pueden ser confirmaciones válidas en otros contextos
    nombre_normalizado = nombre.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    comandos_invalidos = ['ok', 'yes', 'hola', 'menu', 'menú', 'reservar', 'no', 'cancelar']
    
    if nombre_normalizado in comandos_invalidos:
        mensaje = f"'{nombre}' parece ser un comando. Por favor, proporciona tu nombre completo para la reserva. 👤\n\n"
        mensaje += "Ejemplo: Juan Pérez"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None
    
    # Guardar nombre y continuar
    reservation_data['nombre'] = nombre
    session['reservation_data'] = reservation_data
    session['reservation_state'] = RESERVATION_STATES['ESPERANDO_TELEFONO']
    session['nombre_completo'] = nombre  # También lo guardamos en la sesión general
    
    # Guardar sesión
    restaurant_id = restaurant_config.get('id')
    save_session(from_number, session, restaurant_id)
    
    mensaje = f"Gracias, {nombre.split()[0]}! 📱\n\n"
    mensaje += "Por favor, ¿cuál es tu **número de teléfono** de contacto?\n\n"
    mensaje += "(Te recordaremos 24 hs antes sobre la reserva)"
    
    send_whatsapp_message(from_number, mensaje, restaurant_config)
    return None  # No enviar mensaje de debug al cliente

def process_phone_input(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la entrada del teléfono"""
    
    logger.info(f"🔍 PHONE INPUT: Procesando teléfono para {from_number}: '{message}'")
    
    # Extraer números del mensaje
    phone_numbers = re.findall(r'[\+]?[\d\s\-\(\)]{8,}', message)
    
    if not phone_numbers:
        mensaje = "Por favor, proporciona un número de teléfono válido. 📱\n\n"
        mensaje += "Ejemplo: +54 11 1234-5678"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        logger.info(f"❌ PHONE INPUT: Número inválido para {from_number}")
        return None  # No enviar mensaje de debug al cliente
    
    telefono = phone_numbers[0].strip()
    logger.info(f"✅ PHONE INPUT: Teléfono extraído: {telefono}")
    
    # Guardar teléfono y continuar al email
    reservation_data['telefono'] = telefono
    session['reservation_data'] = reservation_data
    session['reservation_state'] = RESERVATION_STATES['ESPERANDO_EMAIL']
    
    logger.info(f"📧 PHONE INPUT: Estado cambiado a ESPERANDO_EMAIL para {from_number}")
    logger.info(f"📊 PHONE INPUT: Datos de reserva: {reservation_data}")
    
    # Guardar sesión
    restaurant_id = restaurant_config.get('id')
    save_session(from_number, session, restaurant_id)
    
    mensaje = f"Perfecto! 📧\n\n"
    mensaje += "Por último, necesitamos tu email, ejemplo: juan@email.com, para enviarte la confirmación de la reserva.\n\n"
    mensaje += "Si no encuentras el mail de confirmación en tu inbox no te preocupes. Tu reserva está confirmada."

    
    send_whatsapp_message(from_number, mensaje, restaurant_config)
    logger.info(f"📤 PHONE INPUT: Mensaje de email enviado a {from_number}")
    return None  # No enviar mensaje de debug al cliente

def process_email_input(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la entrada del email"""
    
    logger.info(f"📧 EMAIL INPUT: Procesando email para {from_number}: '{message}'")
    logger.info(f"📊 EMAIL INPUT: Datos antes del email: {reservation_data}")
    
    email = message.strip().lower()
    
    # Validar formato de email básico
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        logger.info(f"❌ EMAIL INPUT: Email inválido para {from_number}: {email}")
        mensaje = "Por favor, proporciona un email válido. 📧\n\n"
        mensaje += "Ejemplo: juan@email.com"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente
    
    logger.info(f"✅ EMAIL INPUT: Email válido extraído: {email}")
    
    # Guardar email y mostrar resumen
    reservation_data['email'] = email
    session['reservation_data'] = reservation_data
    session['reservation_state'] = RESERVATION_STATES['ESPERANDO_CONFIRMACION']
    
    logger.info(f"🔄 EMAIL INPUT: Estado cambiado a ESPERANDO_CONFIRMACION para {from_number}")
    logger.info(f"📊 EMAIL INPUT: Datos finales con email: {reservation_data}")
    
    # Guardar sesión
    restaurant_id = restaurant_config.get('id')
    save_session(from_number, session, restaurant_id)
    
    logger.info(f"💾 EMAIL INPUT: Sesión guardada, mostrando resumen para {from_number}")
    
    return show_reservation_summary(from_number, restaurant_config, session, reservation_data)

def process_initial_confirmation(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la confirmación inicial después del parsing inteligente"""
    
    logger.info(f"🤖 INITIAL CONFIRMATION: Procesando confirmación inicial para {from_number}: '{message}'")
    
    mensaje_normalizado = message.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    # Palabras de confirmación más amplias para el parsing inicial
    confirmaciones = ['si', 'sí', 'yes', 'ok', 'dale', 'perfecto', 'correcto', 'bien', 'confirmo', 'confirmar']
    cancelaciones = ['no', 'cancel', 'cancelar', 'mal', 'incorrecto', 'error']
    
    # Verificar confirmación
    if (mensaje_normalizado in confirmaciones or 
        any(conf in mensaje_normalizado.split() for conf in confirmaciones)):
        
        logger.info(f"✅ INITIAL CONFIRMATION: Confirmación detectada, pasando a pedir nombre para {from_number}")
        
        # El usuario confirma los datos iniciales, pasar a pedir nombre
        session['reservation_state'] = RESERVATION_STATES['ESPERANDO_NOMBRE'] 
        restaurant_id = restaurant_config.get('id')
        save_session(from_number, session, restaurant_id)
        
        mensaje = "¡Perfecto! Para completar tu reserva, necesito que me digas tu **nombre completo**. 👤"
        
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente
        
    # Verificar cancelación
    elif (mensaje_normalizado in cancelaciones or 
          any(canc in mensaje_normalizado.split() for canc in cancelaciones)):
        
        logger.info(f"❌ INITIAL CONFIRMATION: Cancelación detectada para {from_number}")
        return reset_reservation_flow(from_number, restaurant_config, session, "Entendido. Si cambias de opinión, escribe 'reservar' para empezar de nuevo. 😊")
        
    else:
        # Respuesta no clara, pedir aclaración
        logger.info(f"❓ INITIAL CONFIRMATION: Respuesta no clara para {from_number}: '{message}'")
        
        mensaje = "Por favor, responde **SÍ** si los datos están correctos o **NO** si necesitas cambiarlos. ✅❌"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente

def show_reservation_summary(from_number, restaurant_config, session, reservation_data):
    """Muestra el resumen de la reserva para confirmación"""
    restaurant_name = restaurant_config.get('nombre', 'el restaurante')
    
    logger.info(f"📋 SUMMARY: Mostrando resumen para {from_number}")
    logger.info(f"📊 SUMMARY: Datos completos: {reservation_data}")
    
    # Validar que tenemos todos los datos necesarios
    required_fields = ['fecha', 'personas', 'nombre', 'telefono', 'email']
    missing_fields = [field for field in required_fields if not reservation_data.get(field)]
    
    if missing_fields:
        logger.error(f"❌ SUMMARY: Campos faltantes para {from_number}: {missing_fields}")
        mensaje = f"Faltan algunos datos para completar la reserva. Vamos a empezar de nuevo.\n\n"
        mensaje += "Por favor, escribe 'reservar' para comenzar."
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return reset_reservation_flow(from_number, restaurant_config, session, None)
    
    try:
        fecha_obj = datetime.strptime(reservation_data['fecha'], "%d/%m/%Y")
        fecha_formateada = format_date_spanish(fecha_obj)
    except:
        fecha_formateada = reservation_data['fecha']
    
    # FIX: Usar reservation_data['nombre'] en lugar de nombre indefinido
    primer_nombre = reservation_data['nombre'].split()[0]
    mensaje = f"📋 Genial {primer_nombre}! resumen de tu reserva\n\n"
    mensaje += f"🏪 **Restaurante:** {restaurant_name}\n"
    mensaje += f"📅 **Fecha:** {fecha_formateada}\n"
    mensaje += f"👥 **Personas:** {reservation_data['personas']}\n"
    mensaje += f"👤 **Nombre:** {reservation_data['nombre']}\n"
    mensaje += f"📱 **Teléfono:** {reservation_data['telefono']}\n"
    mensaje += f"📧 **Email:** {reservation_data['email']}\n\n"
    mensaje += "¿Confirmas la reserva? ✅\n\n"
    mensaje += "Responde:\n"
    mensaje += "• **SI** para confirmar\n"
    mensaje += "• **NO** para cancelar"
    
    logger.info(f"📤 SUMMARY: Enviando resumen completo a {from_number}")
    send_whatsapp_message(from_number, mensaje, restaurant_config)
    return None  # No enviar mensaje de debug al cliente

async def process_confirmation(from_number, message, restaurant_config, session, reservation_data):
    """Procesa la confirmación final"""
    mensaje_normalizado = message.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    # Verificación más específica para confirmación
    # Buscar palabras completas y formas específicas de confirmación
    palabras_confirmacion = []
    
    # Dividir el mensaje en palabras para análisis más preciso
    palabras = mensaje_normalizado.split()
    
    # Verificar confirmaciones positivas
    if (mensaje_normalizado in ['si', 'sí', 'yes', 'ok', 'vale', 'dale'] or  # Palabras completas
        any(palabra in ['confirmo', 'confirmar', 'perfecto', 'correcto', 'esta', 'bien'] for palabra in palabras) or  # Palabras específicas
        mensaje_normalizado.startswith('si ') or mensaje_normalizado.startswith('sí ') or  # Si seguido de espacio
        mensaje_normalizado.endswith(' si') or mensaje_normalizado.endswith(' sí')):  # Si al final
        return await save_reservation(from_number, restaurant_config, session, reservation_data)
    
    # Verificar cancelaciones
    elif (mensaje_normalizado in ['no', 'cancel', 'cancelar'] or
          any(palabra in ['no', 'cancelar', 'cancel', 'cancelo'] for palabra in palabras)):
        return reset_reservation_flow(from_number, restaurant_config, session, "Reserva cancelada. Si cambias de opinión, escribe 'reservar' para empezar de nuevo. 😊")
    
    else:
        mensaje = "Por favor, responde **SI** para confirmar la reserva o **NO** para cancelar. ✅❌"
        send_whatsapp_message(from_number, mensaje, restaurant_config)
        return None  # No enviar mensaje de debug al cliente

async def save_reservation(from_number, restaurant_config, session, reservation_data):
    """Guarda la reserva en la base de datos"""
    try:
        restaurant_id = restaurant_config.get('id')
        restaurant_name = restaurant_config.get('nombre', 'el restaurante')
        
        logger.info(f"💾 SAVE: Guardando reserva para {from_number}")
        logger.info(f"📊 SAVE: Datos completos a guardar: {reservation_data}")
        
        # Validar que tenemos el email
        if not reservation_data.get('email'):
            logger.error(f"❌ SAVE: Email faltante para {from_number}")
            mensaje = "Error: Email faltante. Por favor, inicia la reserva nuevamente."
            send_whatsapp_message(from_number, mensaje, restaurant_config)
            return reset_reservation_flow(from_number, restaurant_config, session, None)
        
        # Preparar datos para la base de datos
        fecha_obj = datetime.strptime(reservation_data['fecha'], "%d/%m/%Y").date()
        
        reserva_data = {
            'restaurante_id': restaurant_id,
            'fecha': fecha_obj.isoformat(),
            'hora': reservation_data.get('hora', '20:00'),  # Agregar hora requerida
            'personas': reservation_data['personas'],
            'nombre_cliente': reservation_data['nombre'],  # Usar nombre_cliente correcto
            'telefono': reservation_data['telefono'],
            'email': reservation_data['email'],  # CRÍTICO: Asegurar que el email se guarde
            'estado': 'Confirmada',  # Usar formato correcto de estado
            'origen': 'whatsapp',
            'comentarios': f"Reserva desde WhatsApp: {from_number}"  # Incluir info del WhatsApp en comentarios
        }
        
        logger.info(f"🗃️ SAVE: Datos para Supabase: {reserva_data}")
        
        # Guardar en Supabase
        supabase = supabase_client
        if supabase:
            result = supabase.table("reservas_prod").insert(reserva_data).execute()
            
            if result.data:
                logger.info(f"✅ SAVE: Reserva guardada exitosamente para {from_number}")
                logger.info(f"📧 SAVE: Email guardado: {reservation_data['email']}")
                
                # 🔥 CRÍTICO: Enviar confirmación por email - ESTO FALTABA!
                try:
                    from services.email_service import enviar_correo_confirmacion
                    logger.info(f"📤 EMAIL: Intentando enviar confirmación a {reservation_data['email']}")
                    
                    # Preparar datos para el email en el formato correcto
                    email_data = {
                        'nombre': reservation_data['nombre'],
                        'email': reservation_data['email'],
                        'telefono': reservation_data['telefono'],
                        'fecha': reservation_data['fecha'],  # Ya está en formato DD/MM/YYYY
                        'hora': reservation_data.get('hora', '20:00'),
                        'personas': reservation_data['personas'],
                        'comentarios': f"Reserva desde WhatsApp: {from_number}",
                        'restaurante_id': restaurant_id
                    }
                    
                    email_sent = enviar_correo_confirmacion(email_data, reservation_data['email'], restaurant_config)
                    
                    if email_sent:
                        logger.info(f"✅ EMAIL: Confirmación enviada exitosamente a {reservation_data['email']}")
                    else:
                        logger.warning(f"⚠️ EMAIL: No se pudo enviar confirmación a {reservation_data['email']}")
                        
                except Exception as email_error:
                    logger.error(f"❌ EMAIL: Error enviando confirmación: {str(email_error)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Reserva guardada exitosamente
                reset_reservation_flow(from_number, restaurant_config, session, None)
                
                try:
                    fecha_formateada = format_date_spanish(fecha_obj)
                except:
                    fecha_formateada = reservation_data['fecha']
                
                mensaje = f"🎉 **¡RESERVA CONFIRMADA!**\n\n"
                mensaje += f"✅ Tu reserva en {restaurant_name} ha sido confirmada.\n\n"
                mensaje += f"📋 **Detalles:**\n"
                mensaje += f"📅 {fecha_formateada}\n"
                mensaje += f"👥 {reservation_data['personas']} persona{'s' if reservation_data['personas'] > 1 else ''}\n"
                mensaje += f"👤 {reservation_data['nombre']}\n"
                mensaje += f"📧 Te hemos enviado confirmación a : {reservation_data['email']}. Si no lo encuentras revisa la carpeta Spam.\n\n"
                mensaje += f"📱 Te contactaremos al {reservation_data['telefono']} 24 Hs antes para recordarte.\n\n"
                mensaje += f"¡Esperamos verte pronto en {restaurant_name}! 😊"
                
                send_whatsapp_message(from_number, mensaje, restaurant_config)
                return None  # No enviar mensaje de debug al cliente
            
        # Error al guardar
        mensaje = f"Hubo un problema al confirmar tu reserva. 😔\n\n"
        mensaje += f"Por favor, contacta directamente con {restaurant_name} o intenta nuevamente más tarde."
        
        reset_reservation_flow(from_number, restaurant_config, session, mensaje)
        return None  # No enviar mensaje de debug al cliente
        
    except Exception as e:
        logger.error(f"Error al guardar reserva: {str(e)}")
        return reset_reservation_flow(from_number, restaurant_config, session, "Hubo un error al procesar tu reserva. Por favor, intenta nuevamente.")

def reset_reservation_flow(from_number, restaurant_config, session, mensaje):
    """Resetea el flujo de reserva"""
    session['reservation_state'] = RESERVATION_STATES['INICIO']
    session['reservation_data'] = {}
    
    # Guardar sesión
    restaurant_id = restaurant_config.get('id')
    save_session(from_number, session, restaurant_id)
    
    if mensaje:
        send_whatsapp_message(from_number, mensaje, restaurant_config)
    
    return None  # No enviar mensaje de debug al cliente

def is_in_reservation_flow(session):
    """Verifica si el usuario está en medio de un flujo de reserva"""
    return session.get('reservation_state', RESERVATION_STATES['INICIO']) != RESERVATION_STATES['INICIO']