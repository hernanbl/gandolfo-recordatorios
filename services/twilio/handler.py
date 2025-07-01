
import logging
import traceback
import asyncio
import re
import random
from utils.session_manager import get_session, save_session, get_or_create_session
from services.twilio.reservation_handler import RESERVATION_STATES, handle_reservation_flow
from services.twilio.messaging import send_whatsapp_message, send_whatsapp_message_async
from services.twilio.utils import get_or_create_session
from services.twilio.menu_service import get_menu_for_day
from datetime import datetime, timedelta

# Configuración de logging
logger = logging.getLogger(__name__)

async def handle_whatsapp_message(message, from_number, restaurant_config, message_sid=None):
    """Procesa mensajes de WhatsApp entrantes - Versión simplificada para testing"""
    try:
        mensaje_normalizado = message.lower().strip()
        logger.info(f"🔍 Procesando mensaje: '{message}' de {from_number}")
        
        if not restaurant_config:
            logger.error("❌ Restaurant config missing")
            return "Error de configuración del restaurante."

        restaurant_id = restaurant_config.get('id')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        
        # Comandos básicos
        if any(keyword in mensaje_normalizado for keyword in ['menu', 'menú', 'carta', 'platos', 'comer', 'hoy', 'mañana', 'dia', 'día']):
            logger.info(f"📋 Comando MENU detectado de {from_number}")
            
            target_date = datetime.now()
            day_name = "hoy"
            
            if "mañana" in mensaje_normalizado:
                target_date += timedelta(days=1)
                day_name = "mañana"
            
            # Obtener el nombre del día de la semana en español
            dias_semana = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
            day_of_week_spanish = dias_semana[target_date.weekday()]

            daily_menu = get_menu_for_day(restaurant_id, day_of_week_spanish)
            
            if daily_menu:
                menu_text = f"¡Claro! 😊 Aquí tienes el menú para {day_name} ({day_of_week_spanish.capitalize()}):\n\n"
                
                if daily_menu.get('almuerzo'):
                    menu_text += "🍽️ *Almuerzo*:\n"
                    for item in daily_menu['almuerzo']:
                        menu_text += f"• {item.get('name')} {f"(${item.get('price')})" if item.get('price') else ''}\n"
                
                if daily_menu.get('cena'):
                    if daily_menu.get('almuerzo'):
                        menu_text += "\n" # Add a newline for separation if both exist
                    menu_text += "🌙 *Cena*:\n"
                    for item in daily_menu['cena']:
                        menu_text += f"• {item.get('name')} {f"(${item.get('price')})" if item.get('price') else ''}\n"
                
                if not daily_menu.get('almuerzo') and not daily_menu.get('cena'):
                    menu_text += "No tenemos un menú específico para este día. Por favor, consulta nuestra carta general en el restaurante o pregunta por nuestras especialidades del día.\n"
                
                menu_text += """
¿Puedo ayudarte con algo más? 😊"""
                send_whatsapp_message(from_number, menu_text, restaurant_config)
            else:
                menu_response = f"Lo siento, no pude encontrar el menú para {day_name} en este momento. ¿Puedo ayudarte con algo más? 😊"
                send_whatsapp_message(from_number, menu_response, restaurant_config)
            return None
            
        elif mensaje_normalizado in ['reservar', 'reserva']:
            logger.info(f"� Comando RESERVAR detectado de {from_number}")
            reserva_response = f"""📅 *Hacer una Reserva en {restaurant_name}*

¡Perfecto! Te ayudo a hacer tu reserva.

Para continuar, necesito que me proporciones:

1️⃣ **Fecha**: ¿Para qué día quieres reservar?
   Ejemplo: "Para mañana" o "Para el sábado"

2️⃣ **Cantidad de personas**: ¿Para cuántas personas?
   Ejemplo: "Para 4 personas"

3️⃣ **Horario preferido**: ¿A qué hora?
   Ejemplo: "A las 20:00"

Escribe la fecha que prefieres y comenzamos 😊"""

            send_whatsapp_message(from_number, reserva_response, restaurant_config)
            return None
            
        elif mensaje_normalizado in ['ubicacion', 'ubicación', 'direccion', 'dirección']:
            logger.info(f"📍 Comando UBICACION detectado de {from_number}")
            
            contact_info = restaurant_config.get('info_json', {}).get('contact', {})
            direccion = contact_info.get('address', 'Consultar dirección')
            telefono = contact_info.get('phone', 'Consultar teléfono')
            
            ubicacion_response = f"""¡Claro! 😊 Aquí te comparto la información de {restaurant_name}:

📍 *Ubicación*

🏠 **Dirección**: {direccion}

📞 **Teléfono**: {telefono}

🕒 **Horarios**:
• Lunes a Viernes: 12:00 - 15:00 y 19:00 - 23:00
• Sábados: 12:00 - 16:00 y 19:00 - 00:00
• Domingos: 12:00 - 16:00

🚗 **Cómo llegar**:
• En auto: Estacionamiento disponible
• En transporte público: Líneas 123, 456

¿Puedo ayudarte con algo más? 😊"""

            send_whatsapp_message(from_number, ubicacion_response, restaurant_config)
            return None
            
        elif mensaje_normalizado in ['hola', 'hi', 'hello']:
            logger.info(f"👋 Comando SALUDO detectado de {from_number}")
            
            saludo_response = f"""👋 ¡Hola! Bienvenido a *{restaurant_name}*

¿En qué puedo ayudarte hoy?

Puedes escribir:
➡️ *Reservar* - para hacer una reserva
➡️ *Menu* - para ver nuestro menú  
➡️ *Ubicacion* - para saber dónde encontrarnos

¡Estamos aquí para ayudarte! 😊"""

            send_whatsapp_message(from_number, saludo_response, restaurant_config)
            return None
            
        else:
            logger.info(f"❓ Mensaje no reconocido de {from_number}: '{message}'")
            
            help_response = f"""❓ No entiendo tu mensaje, pero puedo ayudarte con:

➡️ *Reservar* - para hacer una reserva
➡️ *Menu* - para ver nuestro menú  
➡️ *Ubicacion* - para saber dónde encontrarnos
➡️ *Hola* - para saludar

¿Qué te gustaría hacer? 😊"""

            send_whatsapp_message(from_number, help_response, restaurant_config)
            return None
            
    except Exception as e:
        logger.error(f"❌ Error en handle_whatsapp_message: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error procesando mensaje: {str(e)}"
            'vegetariano', 'vegano', 'celico', 'celiaco', 'gluten', 'tacc', 'alergias', 'alergia', 'sin gluten',
            # Estacionamiento
            'estacionamiento', 'parking', 'aparcar', 'auto', 'coche', 'estacionar',
            # Espacios
            'terraza', 'patio', 'afuera', 'exterior', 'adentro', 'interior', 'salon', 'salón',
            # Vestimenta
            'vestimenta', 'dress code', 'como vestirse', 'que ropa', 'formal', 'casual', 'vestir', 'como hay que vestirse',
            # Cancelación
            'cancelacion', 'cancelar', 'cambiar reserva', 'modificar reserva', 'política', 'politica',
            'politica de cancelacion', 'política de cancelación',
            # Horarios y servicios (específicos)
            'wifi', 'internet',
            # Pagos
            'pago', 'tarjeta', 'efectivo', 'mercado pago', 'transferencia', 'débito', 'crédito',
            # Ruido/ambiente
            'ruido', 'silencioso', 'tranquilo', 'ambiente'
        ]
        is_policy_query = any(keyword in mensaje_normalizado for keyword in policy_keywords)
        
        # Si es una consulta de política, actúa como comando de interrupción
        if is_policy_query:
            is_interrupt_command = True
            logger.info(f"📋 POLÍTICA DETECTADA: '{message}' será tratada como comando de interrupción")
        
        # DETECCIÓN Y LIMPIEZA DE ESTADOS PROBLEMÁTICOS
        reservation_state = session.get('reservation_state')
        is_problematic_state = False
        
        # Detectar si el bot está trabado esperando cantidad de personas
        if reservation_state == RESERVATION_STATES['ESPERANDO_PERSONAS'] and is_interrupt_command:
            logger.warning(f"🚨 ESTADO PROBLEMÁTICO DETECTADO: Bot trabado esperando personas, usuario dice '{message}'")
            is_problematic_state = True
        
        # Detectar otros estados problemáticos donde el usuario claramente quiere otra cosa
        problematic_states = [
            RESERVATION_STATES['ESPERANDO_FECHA'],
            RESERVATION_STATES['ESPERANDO_PERSONAS'],
            RESERVATION_STATES['ESPERANDO_NOMBRE'],
            RESERVATION_STATES['ESPERANDO_TELEFONO']
        ]
        
        if reservation_state in problematic_states and is_interrupt_command:
            logger.warning(f"🚨 LIMPIANDO ESTADO PROBLEMÁTICO: {reservation_state} interrumpido por '{message}'")
            is_problematic_state = True
        
        # Limpiar estados problemáticos
        if is_problematic_state:
            session['reservation_state'] = RESERVATION_STATES['COMPLETADA']
            session['reservation_data'] = {}
            save_session(from_number, session, restaurant_id)
            logger.info(f"✅ Estado de reserva limpiado para {from_number}")
        
        # PRIORIDAD 1: Detección de Feedback (MÁXIMA PRIORIDAD - antes que cualquier otra lógica)
        # ¡CRÍTICO! El feedback debe detectarse ANTES que el flujo de reserva activo
        if detect_and_save_feedback(from_number, message, restaurant_config):
            logger.info(f"🌟 FEEDBACK: Feedback detectado y guardado para {from_number}")
            return None  # Ya se envió respuesta en la función
        
        # PRIORIDAD 2: Verificar si hay un flujo de reserva activo (SOLO si no es un comando de interrupción)
        if reservation_state and reservation_state != RESERVATION_STATES['COMPLETADA'] and not is_interrupt_command and not is_problematic_state:
            logger.info(f"Continuando flujo de reserva activo: {reservation_state}")
            return handle_reservation_flow(from_number, message, restaurant_config, session, mensaje_normalizado)
        elif reservation_state and (is_interrupt_command or is_problematic_state):
            logger.info(f"🔄 Comando de interrupción detectado: '{message}' - Estado anterior: {reservation_state}")
            session['reservation_state'] = RESERVATION_STATES['COMPLETADA']
            session['reservation_data'] = {}
            save_session(from_number, session, restaurant_id)
        
        def get_first_name(full_name):
            if not full_name or not isinstance(full_name, str):
                return ""
            return full_name.split(' ')[0]

        def should_use_name():
            return True

        # PRIORIDAD 1: Despedidas y agradecimientos (MÁXIMA PRIORIDAD - antes que cualquier otra lógica)
        farewell_keywords = [
            'gracias', 'chau', 'adios', 'adiós', 'hasta luego', 'nos vemos', 'bye', 'goodbye',
            'hasta la vista', 'que tengas', 'buen dia', 'buena tarde', 'buena noche',
            'muchas gracias', 'te agradezco', 'perfecto gracias', 'listo gracias',
            'ok gracias', 'genial gracias', 'excelente gracias', 'barbaro gracias'
        ]
        
        is_farewell = False
        # IMPORTANTE: No detectar como despedida si el mensaje contiene una calificación numérica (1-5)
        # ya que puede ser feedback que incluye "gracias"
        tiene_calificacion = re.search(r'^[1-5]\b', mensaje_normalizado)
        
        if not tiene_calificacion:  # Solo verificar despedidas si NO hay calificación
            for keyword in farewell_keywords:
                if keyword in mensaje_normalizado:
                    # Verificar que sea realmente una despedida y no parte de otra consulta
                    # Si el mensaje es corto y contiene una palabra clave de despedida, asumimos que es una despedida
                    if len(mensaje_normalizado.split()) <= 5 or any(word in mensaje_normalizado for word in ['gracias', 'chau', 'adios', 'adiós', 'bye']):
                        is_farewell = True
                        break
        
        if is_farewell:
            logger.info(f"👋 DESPEDIDA: Detectada despedida en: '{message}'")
            
            # Limpiar el estado de la sesión al detectar una despedida
            session['reservation_state'] = RESERVATION_STATES['COMPLETADA']
            session['reservation_data'] = {}
            save_session(from_number, session, restaurant_id)
            logger.info(f"✅ Estado de reserva limpiado para {from_number} debido a despedida.")

            # Intentar obtener nombre desde la sesión actual primero
            nombre_usuario = get_first_name(session.get('nombre_cliente', ''))
            
            # Si no hay nombre en sesión, buscar en reservas previas
            if not nombre_usuario:
                nombre_usuario = get_known_user_name(from_number)
            
            # Respuestas de despedida variadas y cálidas
            if nombre_usuario and should_use_name():
                # Despedidas personalizadas para usuarios conocidos
                despedidas = [
                    f"¡Gracias {nombre_usuario}! Que tengas un hermoso día 😊",
                    f"¡Un placer haberte ayudado, {nombre_usuario}! Que disfrutes mucho 🌟",
                    f"¡Hasta pronto {nombre_usuario}! Esperamos verte en {restaurant_name} 😊",
                    f"¡Gracias por escribirnos, {nombre_usuario}! Que tengas un excelente día ✨",
                    f"¡Nos vemos pronto, {nombre_usuario}! Cualquier cosa que necesites, acá estamos 🤗"
                ]
            else:
                # Despedidas estándar para usuarios nuevos
                despedidas = [
                    f"¡Gracias! Que tengas un hermoso día 😊",
                    f"¡Un placer haberte ayudado! Que disfrutes mucho 🌟",
                    f"¡Hasta pronto! Esperamos verte en {restaurant_name} 😊",
                    f"¡Gracias por escribirnos! Que tengas un excelente día ✨",
                    f"¡Nos vemos! Cualquier cosa que necesites, acá estamos 🤗"
                ]
            
            despedida_personal = random.choice(despedidas)
            send_whatsapp_message(from_number, despedida_personal, restaurant_config)
            logger.info(f"✅ Despedida {'personalizada' if nombre_usuario else 'estándar'} enviada a {from_number}")
            return None

        # PRIORIDAD 3: Manejar saludos (SOLO si no hay otras intenciones específicas)
        saludos = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'que tal', 'como estas', 'hello', 'hi']
        es_solo_saludo = mensaje_normalizado in saludos or any(saludo in mensaje_normalizado for saludo in saludos)

        if es_solo_saludo:
            logger.info(f"👋 SALUDO: Detectado saludo simple '{message}' de {from_number}")
            
            # Intentar obtener nombre desde la sesión actual primero
            nombre_usuario = get_first_name(session.get('nombre_cliente', ''))
            
            # Si no hay nombre en sesión, buscar en reservas previas
            if not nombre_usuario:
                nombre_usuario = get_known_user_name(from_number)
            
            # Crear saludo personalizado según si el usuario es conocido o no
            if nombre_usuario and should_use_name():
                # Usuario conocido - saludo más cálido y personal
                saludo_personalizado = f"¡Hola {nombre_usuario}! Bienvenido a {restaurant_name}. 😊 Qué bueno saber de vos nuevamente."
                bienvenida = f"{saludo_personalizado} ¿En qué podemos ayudarte hoy?"
            else:
                # Usuario nuevo - saludo estándar
                bienvenida = f"¡Hola! Bienvenido a {restaurant_name}. 😊 ¿En qué podemos ayudarte hoy?"
            
            send_whatsapp_message(from_number, bienvenida, restaurant_config)
            logger.info(f"✅ Saludo {'personalizado' if nombre_usuario else 'estándar'} respondido a {from_number}")
            return None

        # PRIORIDAD 5: Consultas sobre Políticas del Restaurante (ANTES que menú y reservas)
        policy_keywords = [
            # Mascotas
            'mascota', 'mascotas', 'perro', 'perros', 'gato', 'gatos', 'animal', 'animales', 'pet', 'pets',
            # Niños
            'ninos', 'niños', 'bebe', 'bebé', 'chico', 'chicos', 'children', 'kids', 'menores', 'familia', 'familiar',
            # Fumar
            'fumar', 'fumo', 'cigarro', 'cigarrillo', 'tabaco', 'smoke', 'smoking', 'puedo fumar', 'se puede fumar',
            'fumadores', 'zona fumadores', 'zona de fumadores',
            # Accesibilidad
            'accesibilidad', 'silla de ruedas', 'discapacidad', 'wheelchair', 'accesible',
            # Dietas (solo palabras específicas, no genéricas)
            'vegetariano', 'vegano', 'celico', 'celiaco', 'gluten', 'tacc', 'alergias', 'alergia', 'sin gluten',
            # Estacionamiento
            'estacionamiento', 'parking', 'aparcar', 'auto', 'coche', 'estacionar',
            # Espacios
            'terraza', 'patio', 'afuera', 'exterior', 'adentro', 'interior', 'salon', 'salón',
            # Vestimenta
            'vestimenta', 'dress code', 'como vestirse', 'que ropa', 'formal', 'casual', 'vestir', 'como hay que vestirse',
            # Cancelación
            'cancelacion', 'cancelar', 'cambiar reserva', 'modificar reserva', 'política', 'politica',
            'politica de cancelacion', 'política de cancelación',
            # Horarios y servicios (específicos)
            'wifi', 'internet',
            # Pagos
            'pago', 'tarjeta', 'efectivo', 'mercado pago', 'transferencia', 'débito', 'crédito',
            # Ruido/ambiente
            'ruido', 'silencioso', 'tranquilo', 'ambiente'
        ]
        
        if any(keyword in mensaje_normalizado for keyword in policy_keywords):
            logger.info(f"📋 POLÍTICAS: Detectada consulta sobre políticas: '{message}'")
            return handle_policy_query(from_number, message, restaurant_config)

        # PRIORIDAD 6: Consultas sobre Menú (después de políticas, palabras más específicas)
        menu_keywords = [
            'menu', 'carta', 'comida', 'platos', 'especialidades', 'precios', 'desayuno', 'almuerzo', 'cena',
            'platillos', 'cocina', 'gastronomia', 'comidas',
            'recomendacion', 'suggestions', 'que recomiendan',
            'ver menu', 'mostrar menu', 'quiero ver el menu', 'para comer',
            'pasas el menu', 'pasar menu', 'muestrame el menu'
        ]
        if any(keyword in mensaje_normalizado for keyword in menu_keywords):
            logger.info(f"🍽️ MENÚ: Detectada consulta de menú: '{message}'")
            return handle_menu_query(from_number, message, restaurant_config, session)

        # PRIORIDAD 7: Consultas sobre Ubicación (específicas)
        location_keywords = ['ubicacion', 'direccion', 'donde estan', 'como llego', 'localizacion', 'mapa', 'coordenadas', 'dónde están', 'cómo llego', 'donde se encuentran']
        if any(keyword in mensaje_normalizado for keyword in location_keywords):
            logger.info(f"📍 UBICACIÓN: Detectada consulta de ubicación: '{message}'")
            # Llamada a la función handle_location_query que ahora incluirá la intro cálida
            return handle_location_query(from_number, message, restaurant_config)

        # PRIORIDAD 8: Sistema de Reservas Inteligente (MÁS ESPECÍFICO)
        # Ahora requerimos palabras explícitas de reserva, no solo números
        palabras_reserva_exactas = ['reservar', 'reserva', 'mesa', 'lugar', 'quiero reservar', 'necesito reservar', 'hacer reserva']
        tiene_intencion_reserva_explicita = any(palabra in mensaje_normalizado for palabra in palabras_reserva_exactas)

        # Solo detectar datos de reserva si hay intención explícita OR si es un flujo de reserva activo
        en_flujo_reserva = session.get('reservation_state', RESERVATION_STATES['INICIO']) != RESERVATION_STATES['INICIO']
        
        if tiene_intencion_reserva_explicita or en_flujo_reserva:
            logger.info(f"🎯 RESERVA: Detectada intención explícita o flujo activo: '{message}'")
            # Limpiar estado anterior solo si no está en flujo activo
            if not en_flujo_reserva:
                session['reservation_state'] = RESERVATION_STATES['INICIO']
                save_session(from_number, session, restaurant_id)
            return handle_reservation_flow(from_number, message, restaurant_config, session, mensaje_normalizado)

        # PRIORIDAD 9: IA Conversacional para Todo lo Demás
        return handle_ai_conversation(from_number, message, restaurant_config, session)

    except Exception as e:
        logger.error(f"❌ Error en handle_whatsapp_message para {from_number}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def request_feedback_after_reservation(from_number, restaurant_config, delay_minutes=2):
    """
    Solicita feedback al cliente después de un tiempo de la reserva confirmada.
    
    Args:
        from_number (str): Número de WhatsApp del cliente
        restaurant_config (dict): Configuración del restaurante
        delay_minutes (int): Minutos a esperar antes de solicitar feedback
    """
    import threading
    import time
    
    def delayed_feedback_request():
        try:
            # Esperar el tiempo especificado
            time.sleep(delay_minutes * 60)
            
            restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
            
            mensaje_feedback = f"¡Hola! 😊\n\n"
            mensaje_feedback += f"Esperamos que hayas disfrutado de tu experiencia en {restaurant_name}.\n\n"
            mensaje_feedback += f"¿Te gustaría dejarnos tu opinión? Nos ayuda mucho a mejorar:\n\n"
            mensaje_feedback += f"• Puedes calificarnos del 1 al 5 (donde 5 es excelente)\n"
            mensaje_feedback += f"• O simplemente contarnos cómo te pareció todo\n\n"
            mensaje_feedback += f"¡Tu opinión es muy valiosa para nosotros! ⭐"
            
            send_whatsapp_message(from_number, mensaje_feedback, restaurant_config)
            logger.info(f"✅ Solicitud de feedback enviada a {from_number} para restaurante {restaurant_name}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando solicitud de feedback a {from_number}: {str(e)}")
    
    # Ejecutar en un hilo separado para no bloquear el flujo principal
    feedback_thread = threading.Thread(target=delayed_feedback_request)
    feedback_thread.daemon = True
    feedback_thread.start()

def detect_and_save_feedback(from_number, message, restaurant_config, calificacion=None):
    """
    Detecta si un mensaje contiene feedback y lo guarda en Supabase.
    
    Args:
        from_number (str): Número de WhatsApp del cliente
        message (str): Mensaje del usuario
        restaurant_config (dict): Configuración del restaurante
        calificacion (int, optional): Calificación numérica del 1-5
        
    Returns:
        bool: True si se detectó y guardó feedback, False si no
    """
    try:
        message_lower = message.lower().strip()
        logger.info(f"🔍 FEEDBACK DETECTION: Analizando mensaje: '{message}'")
        
        # Detectar calificación numérica (1-5) 
        import re
        # Buscar números del 1-5 al inicio del mensaje o cerca de palabras de calificación
        calificacion_patterns = [
            r'^([1-5])\b',  # Al inicio del mensaje
            r'^([1-5])\s',  # Al inicio seguido de espacio
            r'([1-5])\s*(?:estrellas?|puntos?|sobre\s*5|de\s*5)',  # Con contexto de calificación
            r'(?:califico|calificación|rating|nota|puntaje|puntúo).*?([1-5])',  # Después de palabras de calificación
            r'([1-5])\s*(?:muy|me|te|le|nos|les|ha|he|hemos|han)',  # Números seguidos de palabras comunes en feedback
        ]
        
        calificacion = None
        for pattern in calificacion_patterns:
            match = re.search(pattern, message_lower)
            if match:
                calificacion = int(match.group(1))
                logger.info(f"✅ FEEDBACK: Calificación detectada con patrón '{pattern}': {calificacion}")
                break
        
        # Palabras clave FUERTES que indican feedback (más específicas)
        feedback_keywords_strong = [
            'me ha gustado', 'me gusto', 'me encanto', 'me fascino', 'me parecio',
            'excelente', 'muy bueno', 'genial', 'perfecto', 'increible', 'fantastico',
            'malo', 'pesimo', 'horrible', 'terrible', 'espantoso',
            'recomiendo', 'no recomiendo', 'volveria', 'no volveria',
            'satisfecho', 'contento', 'decepcionado', 'encantado',
            'gracias por', 'muchas gracias', 'muy agradecido', 'te agradezco',
            'opinion', 'calificacion', 'estrellas', 'puntos', 'calificar',
            'servicio', 'experiencia', 'sistema', 'plataforma', 'app', 'aplicacion',
            'funciona', 'funcionó', 'funciono', 'me sirvio', 'me sirve',
            'esta bueno', 'esta malo', 'esta bien', 'esta genial',
            'gustado mucho', 'gustó mucho', 'parecido bien', 'parecio bien'
        ]
        
        # Palabras clave DÉBILES (solo si van con calificación o contexto fuerte)
        feedback_keywords_weak = [
            'bueno', 'regular', 'bien', 'mal', 'estuvo', 'fue'
        ]
        
        # Verificar palabras fuertes
        tiene_feedback_fuerte = any(keyword in message_lower for keyword in feedback_keywords_strong)
        
        # Verificar palabras débiles (solo si hay calificación o mensaje largo)
        tiene_feedback_debil = any(keyword in message_lower for keyword in feedback_keywords_weak)
        
        # Lógica de detección mejorada
        es_feedback = False
        
        if calificacion is not None:
            # Si tiene calificación numérica, es muy probable que sea feedback
            if tiene_feedback_fuerte or tiene_feedback_debil or len(message.strip()) >= 5:
                es_feedback = True
                logger.info(f"✅ FEEDBACK: Detectado por calificación + contexto (calificación: {calificacion})")
        elif tiene_feedback_fuerte:
            # Palabras fuertes son suficientes
            es_feedback = True
            logger.info(f"✅ FEEDBACK: Detectado por palabras fuertes")
        elif tiene_feedback_debil and len(message.strip()) >= 15:
            # Palabras débiles solo si el mensaje es suficientemente largo
            es_feedback = True
            logger.info(f"✅ FEEDBACK: Detectado por palabras débiles + longitud")
        
        # Caso especial: mensaje que empieza con número 1-5 seguido de texto descriptivo
        if not es_feedback and re.match(r'^[1-5]\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]', message):
            es_feedback = True
            logger.info(f"✅ FEEDBACK: Detectado por patrón 'número + texto descriptivo'")
        
        # Excluir falsos positivos comunes (pero ser menos estricto si hay calificación)
        false_positives = [
            'reservar', 'reserva', 'mesa', 'ubicacion', 'direccion',
            'menu', 'carta', 'hola', 'buenos dias', 'como estas',
            'personas', 'para mañana', 'para hoy', 'para el', 'quiero', 'necesito'
        ]
        
        # Palabras específicas de reserva que indican que NO es feedback
        reservation_indicators = [
            'personas', 'mañana', 'hoy', 'fecha', 'reservar', 'reserva', 'mesa', 'lugar',
            'hora', 'quiero', 'necesito', 'para el', 'para hoy', 'para mañana'
        ]
        
        tiene_falso_positivo = any(fp in message_lower for fp in false_positives)
        tiene_indicador_reserva = any(ri in message_lower for ri in reservation_indicators)
        
        if tiene_falso_positivo or tiene_indicador_reserva:
            # Si contiene palabras de falsos positivos o indicadores de reserva, ser MUY estricto
            if not (calificacion is not None and tiene_feedback_fuerte and len(message.strip()) >= 20):
                es_feedback = False
                logger.info(f"❌ FEEDBACK: Descartado por falso positivo/reserva (fp: {tiene_falso_positivo}, res: {tiene_indicador_reserva}, cal: {calificacion})")
        
        if es_feedback:
            logger.info(f"🌟 FEEDBACK: ¡Feedback válido detectado! Guardando...")
            # Guardar el feedback
            success = save_feedback(from_number, message, restaurant_config, calificacion)
            
            if success:
                restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
                
                # Respuesta personalizada según el tipo de feedback
                if calificacion:
                    if calificacion >= 4:
                        respuesta = f"¡Muchas gracias por tu calificación de {calificacion}/5! 🌟\n\n"
                        respuesta += f"Nos alegra saber que tuviste una buena experiencia en {restaurant_name}. ¡Esperamos verte pronto de nuevo! 😊"
                    elif calificacion == 3:
                        respuesta = f"Gracias por tu calificación de {calificacion}/5. 📝\n\n"
                        respuesta += f"Valoramos tu opinión y trabajamos constantemente para mejorar. ¡Esperamos ofrecerte una mejor experiencia la próxima vez!"
                    else:
                        respuesta = f"Gracias por tu sincera calificación de {calificacion}/5. 🙏\n\n"
                        respuesta += f"Lamentamos que tu experiencia no haya sido la esperada. Tu feedback nos ayuda a mejorar. ¡Esperamos poder sorprenderte positivamente en el futuro!"
                else:
                    respuesta = f"¡Muchas gracias por tomarte el tiempo de dejarnos tu opinión! 🙏\n\n"
                    respuesta += f"Tu feedback es muy valioso para {restaurant_name} y nos ayuda a seguir mejorando. ¡Esperamos verte pronto!"
                
                send_whatsapp_message(from_number, respuesta, restaurant_config)
                logger.info(f"✅ Feedback guardado y respuesta enviada a {from_number}")
                return True
            else:
                logger.error(f"❌ FEEDBACK: Error guardando feedback para {from_number}")
                return False
        else:
            logger.info(f"❌ FEEDBACK: No se detectó feedback válido en: '{message}'")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error detectando/guardando feedback de {from_number}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False