import traceback
import asyncio
from datetime import datetime, timedelta
import re
import json
import random
import time
import os
from services.twilio.messaging import send_whatsapp_message
from services.twilio.utils import es_consulta_relevante, get_or_create_session, validar_paso_reserva, get_day_name
from services.twilio.reservation_handler import handle_reservation_flow, RESERVATION_STATES
from services.ai.deepseek_service import DeepSeekService
from utils.session_manager import save_session
from routes.bot import verificar_capacidad_disponible
from db.supabase_client import supabase_client
from services.reservas.db import buscar_reserva_por_telefono
import logging

logger = logging.getLogger(__name__)

# Inicializar servicio de IA
deepseek_service = DeepSeekService()

def load_restaurant_menu_json(restaurant_id):
    """Carga el menú desde el archivo JSON específico del restaurante"""
    try:
        base_dir = os.path.join(os.getcwd(), 'data', 'menus')
        menu_file_path = os.path.join(base_dir, f"{restaurant_id}_menu.json")
        
        logger.info(f"MENU_LOADER: Intentando cargar menú desde: {menu_file_path}")
        
        if os.path.exists(menu_file_path):
            with open(menu_file_path, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
            logger.info(f"MENU_LOADER: Menú cargado exitosamente para restaurante {restaurant_id}")
            return menu_data
        else:
            logger.warning(f"MENU_LOADER: Archivo de menú no encontrado: {menu_file_path}")
            return None
    except Exception as e:
        logger.error(f"MENU_LOADER: Error al cargar menú para restaurante {restaurant_id}: {str(e)}")
        return None

def load_restaurant_info_json(restaurant_id):
    """Carga la información desde el archivo JSON específico del restaurante"""
    try:
        base_dir = os.path.join(os.getcwd(), 'data', 'info')
        info_file_path = os.path.join(base_dir, f"{restaurant_id}_info.json")
        
        logger.info(f"INFO_LOADER: Intentando cargar información desde: {info_file_path}")
        
        if os.path.exists(info_file_path):
            with open(info_file_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            logger.info(f"INFO_LOADER: Información cargada exitosamente para restaurante {restaurant_id}")
            return info_data
        else:
            logger.warning(f"INFO_LOADER: Archivo de información no encontrado: {info_file_path}")
            return None
    except Exception as e:
        logger.error(f"INFO_LOADER: Error al cargar información para restaurante {restaurant_id}: {str(e)}")
        return None

def ensure_restaurant_data_loaded(restaurant_config):
    """Asegura que los datos JSON del restaurante estén cargados en la configuración"""
    restaurant_id = restaurant_config.get('id')
    if not restaurant_id:
        logger.error("CONFIG_LOADER: No se puede cargar datos - ID de restaurante faltante")
        return restaurant_config
    
    logger.info(f"CONFIG_LOADER: Asegurando datos cargados para restaurante {restaurant_id}")
    
    # Cargar menú si no está presente o está vacío
    menu_json = restaurant_config.get('menu_json')
    if not menu_json:
        logger.info(f"CONFIG_LOADER: Cargando menú desde archivo para {restaurant_id}")
        menu_json = load_restaurant_menu_json(restaurant_id)
        if menu_json:
            restaurant_config['menu_json'] = menu_json
            logger.info(f"CONFIG_LOADER: Menú cargado y agregado a config para {restaurant_id}")
    
    # Cargar información si no está presente o está vacía
    info_json = restaurant_config.get('info_json')
    if not info_json:
        logger.info(f"CONFIG_LOADER: Cargando información desde archivo para {restaurant_id}")
        info_json = load_restaurant_info_json(restaurant_id)
        if info_json:
            restaurant_config['info_json'] = info_json
            logger.info(f"CONFIG_LOADER: Información cargada y agregada a config para {restaurant_id}")
    
    return restaurant_config

def _get_nested_value(data_dict, keys, default=None):
    """Helper para obtener valores anidados de forma segura."""
    temp_dict = data_dict
    for key in keys:
        if isinstance(temp_dict, dict):
            temp_dict = temp_dict.get(key)
        else:
            return default
    return temp_dict if temp_dict is not None else default

def get_known_user_name(from_number):
    """
    Obtiene el nombre de un usuario conocido desde sus reservas previas en Supabase.
    
    Args:
        from_number (str): Número de teléfono del usuario
        
    Returns:
        str: Primer nombre del usuario si es conocido, None si no
    """
    try:
        logger.info(f"🔍 USUARIO LOOKUP: Buscando usuario para número: '{from_number}'")
        
        # Normalizar número para búsqueda más efectiva
        # Remover prefijos y caracteres especiales
        clean_number = from_number.replace('whatsapp:', '').replace('+', '').replace(' ', '').replace('-', '')
        
        # Extraer los últimos 10 dígitos (número local argentino)
        if len(clean_number) >= 10:
            local_number = clean_number[-10:]  # Últimos 10 dígitos
            logger.info(f"🔍 USUARIO LOOKUP: Número local extraído: '{local_number}'")
        else:
            local_number = clean_number
        
        # Intentar búsqueda con diferentes formatos
        search_formats = [
            from_number,           # Formato original
            clean_number,          # Sin prefijos
            local_number,          # Solo número local
            f"+54{local_number}",  # Con código de país argentino
            f"549{local_number}",  # Con código móvil argentino
        ]
        
        ultima_reserva = None
        format_found = None
        
        for search_format in search_formats:
            logger.info(f"🔍 USUARIO LOOKUP: Probando formato: '{search_format}'")
            ultima_reserva = buscar_reserva_por_telefono(search_format)
            if ultima_reserva:
                format_found = search_format
                logger.info(f"✅ USUARIO LOOKUP: Encontrado con formato: '{format_found}'")
                break
        
        if ultima_reserva and ultima_reserva.get('nombre_cliente'):
            nombre_completo = ultima_reserva.get('nombre_cliente', '').strip()
            if nombre_completo:
                # Extraer el primer nombre
                primer_nombre = nombre_completo.split(' ')[0]
                logger.info(f"👤 USUARIO CONOCIDO: {from_number} (formato: {format_found}) identificado como '{primer_nombre}' desde reservas previas")
                return primer_nombre
        
        logger.info(f"👤 USUARIO NUEVO: {from_number} no tiene reservas previas en ningún formato")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo nombre de usuario conocido para {from_number}: {str(e)}")
        return None

def handle_policy_query(from_number, message, restaurant_config):
    """Función específica para manejar consultas sobre políticas del restaurante - lee dinámicamente desde JSON"""
    restaurant_id = restaurant_config.get('id')
    logger.info(f"📋 POLÍTICAS: Procesando consulta sobre políticas: '{message}' para restaurante {restaurant_id}")
    
    # Asegurar que los datos JSON estén cargados
    restaurant_config = ensure_restaurant_data_loaded(restaurant_config)
    
    info = restaurant_config.get('info_json', {})
    policies = info.get('policies', {})
    restaurant_name = restaurant_config.get('nombre_restaurante', 'nuestro restaurante')
    mensaje_normalizado = message.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    try:
        response = f"*Información sobre {restaurant_name}* 📋\n\n"
        policy_found = False
        
        # Consultas sobre mascotas
        if any(word in mensaje_normalizado for word in ['mascota', 'mascotas', 'perro', 'perros', 'gato', 'gatos', 'animal', 'animales', 'pet', 'pets']):
            pets_policy = policies.get('pets', {})
            if pets_policy:
                policy_found = True
                response += f"🐕 *Política de mascotas:*\n"
                if pets_policy.get('allowed', False):
                    restrictions = pets_policy.get('restrictions', '')
                    if restrictions:
                        response += f"Permitidas con restricciones: {restrictions}\n"
                    else:
                        response += f"Las mascotas son bienvenidas\n"
                else:
                    response += f"No se permiten mascotas\n"
                
                description = pets_policy.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre niños
        elif any(word in mensaje_normalizado for word in ['ninos', 'niños', 'bebe', 'bebé', 'chico', 'chicos', 'children', 'kids']):
            children_policy = policies.get('children', {})
            if children_policy:
                policy_found = True
                response += f"👶 *Política para niños:*\n"
                if children_policy.get('allowed', True):
                    description = children_policy.get('description', 'Los niños son bienvenidos')
                    response += f"{description}\n"
                    amenities = children_policy.get('amenities', [])
                    if amenities:
                        response += f"Contamos con: {', '.join(amenities)}\n"
                else:
                    response += f"Restaurante orientado a adultos\n"
                response += "\n"
        
        # Consultas sobre accesibilidad
        elif any(word in mensaje_normalizado for word in ['accesibilidad', 'silla de ruedas', 'discapacidad', 'wheelchair']):
            accessibility = policies.get('accessibility', {})
            if accessibility:
                policy_found = True
                response += f"♿ *Accesibilidad:*\n"
                wheelchair = accessibility.get('wheelchair_accessible', False)
                braille = accessibility.get('braille_menu', False)
                response += f"• Acceso para sillas de ruedas: {'Sí' if wheelchair else 'No disponible'}\n"
                response += f"• Menú en braille: {'Disponible' if braille else 'No disponible'}\n"
                description = accessibility.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre dietas especiales
        elif any(word in mensaje_normalizado for word in ['vegetariano', 'vegano', 'celico', 'celiaco', 'gluten', 'tacc', 'alergias']):
            dietary = policies.get('dietary_options', {})
            if dietary:
                policy_found = True
                response += f"🌱 *Opciones dietéticas:*\n"
                options = []
                if dietary.get('vegetarian', False):
                    options.append("vegetarianas")
                if dietary.get('vegan', False):
                    options.append("veganas")
                if dietary.get('gluten_free', False):
                    options.append("sin gluten (sin TACC)")
                
                if options:
                    response += f"Contamos con opciones {', '.join(options)}.\n"
                
                description = dietary.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre estacionamiento
        elif any(word in mensaje_normalizado for word in ['estacionamiento', 'parking', 'aparcar', 'auto', 'coche']):
            parking = policies.get('parking', {})
            if parking:
                policy_found = True
                response += f"🚗 *Estacionamiento:*\n"
                if parking.get('available', False):
                    parking_type = parking.get('type', '')
                    if parking_type:
                        response += f"Tipo: {parking_type}\n"
                    description = parking.get('description', 'Estacionamiento disponible')
                    response += f"{description}\n"
                else:
                    response += f"No contamos con estacionamiento propio\n"
                response += "\n"
        
        # Consultas sobre vestimenta
        elif any(word in mensaje_normalizado for word in ['vestimenta', 'dress code', 'como vestirse', 'que ropa']):
            dress_code = policies.get('dress_code', {})
            if dress_code:
                policy_found = True
                response += f"👔 *Código de vestimenta:*\n"
                if dress_code.get('required', False):
                    style = dress_code.get('style', 'formal')
                    response += f"Se requiere vestimenta {style}\n"
                else:
                    style = dress_code.get('style', 'casual')
                    response += f"Ambiente {style}\n"
                
                description = dress_code.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre fumar
        elif any(word in mensaje_normalizado for word in ['fumar', 'fumo', 'cigarrillo', 'smoke', 'smoking', 'tabaco']):
            smoking = policies.get('smoking', {})
            if smoking:
                policy_found = True
                response += f"� *Política de fumadores:*\n"
                if smoking.get('allowed', False):
                    response += f"Se permite fumar\n"
                elif smoking.get('outdoor_allowed', False):
                    response += f"Se permite fumar solo en áreas exteriores\n"
                else:
                    response += f"No se permite fumar\n"
                
                description = smoking.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre cancelación
        elif any(word in mensaje_normalizado for word in ['cancelacion', 'cancelar', 'cambiar reserva', 'modificar reserva']):
            cancellation = policies.get('cancellation', {})
            if cancellation:
                policy_found = True
                response += f"📅 *Política de cancelación:*\n"
                hours = cancellation.get('advance_notice_hours', 24)
                policy_text = cancellation.get('policy', f'Las reservas pueden cancelarse hasta {hours} horas antes')
                response += f"{policy_text}\n"
                description = cancellation.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre grupos
        elif any(word in mensaje_normalizado for word in ['grupo', 'grupos', 'evento', 'eventos', 'celebracion', 'fiesta']):
            groups = policies.get('group_reservations', {})
            if groups:
                policy_found = True
                response += f"� *Reservas para grupos:*\n"
                max_size = groups.get('max_size', 'sin límite específico')
                response += f"Tamaño máximo: {max_size} personas\n"
                if groups.get('advance_booking_required', False):
                    response += f"Se requiere reserva anticipada\n"
                description = groups.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Consultas sobre ruido/ambiente
        elif any(word in mensaje_normalizado for word in ['ruido', 'ambiente', 'silencioso', 'tranquilo', 'noise']):
            noise = policies.get('noise_level', {})
            if noise:
                policy_found = True
                response += f"🔊 *Ambiente del lugar:*\n"
                level = noise.get('level', 'moderado')
                response += f"Nivel de ruido: {level}\n"
                description = noise.get('description', '')
                if description:
                    response += f"{description}\n"
                response += "\n"
        
        # Si no se encontró una política específica, mostrar resumen general
        if not policy_found:
            response += f"Te ayudo con cualquier consulta sobre nuestras políticas y servicios:\n\n"
            
            # Mostrar resumen de políticas disponibles
            if policies.get('pets', {}).get('allowed', False):
                response += f"🐕 Mascotas: {policies['pets'].get('restrictions', 'Permitidas')}\n"
            
            if policies.get('children', {}).get('allowed', True):
                response += f"👶 Niños: Bienvenidos\n"
            
            if policies.get('dietary_options', {}):
                dietary = policies['dietary_options']
                options = []
                if dietary.get('vegetarian'): options.append("vegetarianas")
                if dietary.get('vegan'): options.append("veganas") 
                if dietary.get('gluten_free'): options.append("sin gluten")
                if options:
                    response += f"🌱 Dietas especiales: {', '.join(options)}\n"
            
            if policies.get('parking', {}).get('available', False):
                response += f"🚗 Estacionamiento: Disponible\n"
            
            response += "\n"
        
        response += f"¿Te gustaría hacer una reserva? Responde 'Reservar' para comenzar. 📅"
        
        send_whatsapp_message(from_number, response, restaurant_config)
        logger.info(f"✅ Consulta sobre políticas respondida para {from_number} - Política encontrada: {policy_found}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error al procesar consulta de políticas para {from_number}: {str(e)}")
        logger.error(traceback.format_exc())
        fallback_response = f"Gracias por tu consulta. Para información específica sobre nuestras políticas, no dudes en preguntarnos directamente. ¿Te gustaría hacer una reserva?"
        send_whatsapp_message(from_number, fallback_response, restaurant_config)
        return None

def handle_location_query(from_number, message, restaurant_config):
    """Función específica para manejar consultas sobre ubicación"""
    restaurant_id = restaurant_config.get('id')
    logger.info(f"UBICACIÓN: Procesando consulta sobre ubicación: '{message}' para restaurante {restaurant_id}")
    
    # Asegurar que los datos JSON estén cargados
    restaurant_config = ensure_restaurant_data_loaded(restaurant_config)
    
    info = restaurant_config.get('info_json', {})
    location_info = info.get('location', {})
    contact_info = info.get('contact', {})
    restaurant_name = restaurant_config.get('nombre_restaurante', 'nuestro restaurante')
    default_phone = contact_info.get('phone', 'nuestro número de contacto')

    try:
        address = location_info.get('address')
        if not address:
            error_response = f"""*Información de ubicación* 📍\n\nNo pudimos encontrar la dirección detallada para {restaurant_name} en este momento. Por favor, contáctanos directamente llamando al {default_phone} para más detalles.\n\n¿Te gustaría hacer una reserva? Responde 'Reservar'."""
            send_whatsapp_message(from_number, error_response, restaurant_config)
            logger.error(f"❌ Error al procesar consulta de ubicación para {from_number}: datos faltantes")
            return None

        google_maps = location_info.get('google_maps_link', '')
        google_reviews = location_info.get('google_reviews_link', '')
        parking = location_info.get('parking', '')
        reference_points = location_info.get('reference_points', [])
        
        response = f"""*¡Hola! Gracias por tu interés en {restaurant_name}* 🍽️\n\n*Nuestra ubicación:*\n📍 {address}\n"""
        if parking:
            response += f"🚗 {parking}\n"
        if reference_points:
            response += "\n*Puntos de referencia:*\n"
            for point in reference_points:
                response += f"• {point}\n"
        
        directions = info.get('directions', {})
        if directions:
            if 'auto' in directions and directions['auto']:
                response += "\n*Cómo llegar en auto:*\n"
                for step in directions['auto']:
                    response += f"• {step}\n"
            if 'transporte_publico' in directions and directions['transporte_publico']:
                response += "\n*Cómo llegar en transporte público:*\n"
                for step in directions['transporte_publico']:
                    response += f"• {step}\n"
        
        if google_maps:
            response += f"\n🗺️ *Google Maps:* {google_maps}\n"
        if google_reviews:
            response += f"\n⭐ *Reseñas en Google:* {google_reviews}\n"
        
        response += f"""
¿Te gustaría hacer una reserva? Responde "Reservar" para comenzar el proceso.

Para cualquier otra consulta, estamos a tu disposición. Puedes contactarnos al {default_phone}."""
        logger.info(f"✅ Consulta sobre ubicación respondida para {from_number}")
        send_whatsapp_message(from_number, response, restaurant_config)
        return None
    except Exception as e:
        logger.error(f"❌ Error al procesar consulta de ubicación para {from_number}: {str(e)}")
        logger.error(traceback.format_exc())
        error_response = f"""*Gracias por tu consulta sobre nuestra ubicación* 📍\n\nEstamos ubicados en {location_info.get('address', 'nuestra dirección principal')}.\n\nPara indicaciones más detalladas, por favor llámanos al {default_phone}.\n\n¿Te gustaría hacer una reserva? Responde 'Reservar' para comenzar el proceso."""
        send_whatsapp_message(from_number, error_response, restaurant_config)
        return None

def get_restaurant_uuid(restaurant_id_string):
    """
    Convierte un restaurant_id string a UUID real de Supabase
    
    Args:
        restaurant_id_string (str): ID string del restaurante (ej: 'ostende', 'gandolfo')
        
    Returns:
        str: UUID real del restaurante en Supabase
    """
    # Mapeo hardcoded de IDs string a UUIDs reales
    uuid_mapping = {
        'ostende': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'gandolfo': 'e0f20795-d325-4af1-8603-1c52050048db',
        'elsie': '4a6f6088-61a6-44a2-aa75-5161e1f3cad1'
    }
    
    # Si ya es un UUID (contiene guiones), devolverlo tal como está
    if '-' in restaurant_id_string:
        return restaurant_id_string
    
    # Buscar el UUID correspondiente al ID string
    uuid_real = uuid_mapping.get(restaurant_id_string.lower())
    
    if not uuid_real:
        logger.warning(f"⚠️ UUID MAPPING: No se encontró UUID para restaurant_id '{restaurant_id_string}', usando ID tal como está")
        return restaurant_id_string
    
    logger.info(f"✅ UUID MAPPING: '{restaurant_id_string}' -> {uuid_real}")
    return uuid_real

def save_feedback(from_number, message, restaurant_config, calificacion=None):
    """
    Guarda feedback del cliente en la tabla feedback de Supabase
    
    Args:
        from_number (str): Número de WhatsApp del cliente
        message (str): Mensaje de feedback del usuario
        restaurant_config (dict): Configuración del restaurante
        calificacion (int, optional): Calificación numérica del 1-5
        
    Returns:
        bool: True si se guardó exitosamente, False si hubo error
    """
    try:
        logger.info(f"💾 SAVE FEEDBACK: Guardando feedback de {from_number}")
        logger.info(f"📝 SAVE FEEDBACK: Mensaje: '{message}'")
        logger.info(f"⭐ SAVE FEEDBACK: Calificación: {calificacion}")
        
        restaurant_id_string = restaurant_config.get('id')
        if not restaurant_id_string:
            logger.error("❌ SAVE FEEDBACK: ID de restaurante faltante")
            return False
        
        # Convertir ID string a UUID real
        restaurant_uuid = get_restaurant_uuid(restaurant_id_string)
        
        # Limpiar número de teléfono (quitar prefijo whatsapp:)
        clean_phone = from_number.replace('whatsapp:', '')
        
        # 🆔 BUSCAR ID DE RESERVA RECIENTE EN LA SESIÓN
        reserva_id = None
        try:
            from utils.session_manager import get_session
            session = get_session(clean_phone, restaurant_uuid)
            if session and 'last_reservation_id' in session:
                potential_reserva_id = session['last_reservation_id']
                
                # 🔍 VERIFICAR QUE LA RESERVA EXISTE EN LA BASE DE DATOS
                try:
                    verify_result = supabase_client.table("reservas_prod").select("id").eq("id", potential_reserva_id).execute()
                    if verify_result.data:
                        reserva_id = potential_reserva_id
                        logger.info(f"🆔 FEEDBACK: Reserva verificada y vinculada: {reserva_id}")
                    else:
                        logger.warning(f"⚠️ FEEDBACK: Reserva {potential_reserva_id} no existe en BD, guardando feedback sin vincular")
                except Exception as verify_error:
                    logger.warning(f"⚠️ FEEDBACK: Error verificando reserva: {str(verify_error)}")
                
        except Exception as session_error:
            logger.warning(f"⚠️ FEEDBACK: Error buscando reserva_id en sesión: {str(session_error)}")
        
        # Preparar datos para Supabase (usando nombres de columnas correctos)
        feedback_data = {
            'restaurante_id': restaurant_uuid,  # ✅ Ahora usa el UUID real
            'cliente_telefono': clean_phone,    # ✅ Nombre correcto
            'comentario': message.strip(),      # ✅ Nombre correcto (no 'mensaje')
            'puntuacion': calificacion,
            'fecha_feedback': datetime.now().isoformat()
        }
        
        # 🆔 AGREGAR RESERVA_ID SOLO SI EXISTE Y ES VÁLIDO
        if reserva_id:
            feedback_data['reserva_id'] = reserva_id
        
        logger.info(f"🗃️ SAVE FEEDBACK: Datos para Supabase: {feedback_data}")
        
        # Guardar en Supabase
        supabase = supabase_client
        if not supabase:
            logger.error("❌ SAVE FEEDBACK: Cliente Supabase no disponible")
            return False
        
        result = supabase.table("feedback").insert(feedback_data).execute()
        
        if result.data:
            logger.info(f"✅ SAVE FEEDBACK: Feedback guardado exitosamente para {from_number}")
            logger.info(f"📊 SAVE FEEDBACK: Resultado Supabase: {result.data}")
            
            # 🧹 LIMPIAR RESERVA_ID DE LA SESIÓN (una vez usado, no reutilizar)
            if reserva_id:
                try:
                    from utils.session_manager import save_session
                    session = get_session(clean_phone, restaurant_uuid)
                    if session and 'last_reservation_id' in session:
                        del session['last_reservation_id']
                        save_session(clean_phone, session, restaurant_uuid)
                        logger.info(f"🧹 FEEDBACK: Reserva_id limpiado de la sesión")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ FEEDBACK: Error limpiando reserva_id de sesión: {str(cleanup_error)}")
            
            return True
        else:
            logger.error(f"❌ SAVE FEEDBACK: No se obtuvieron datos en la respuesta de Supabase")
            return False
        
    except Exception as e:
        logger.error(f"❌ SAVE FEEDBACK: Error guardando feedback para {from_number}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def get_menu_from_config(restaurant_config):
    """Extrae el menú del restaurant_config en formato legible"""
    try:
        restaurant_name = restaurant_config.get('nombre', 'el restaurante')
        restaurant_id = restaurant_config.get('id')
        
        logger.info(f"MENÚ: Extrayendo menú para {restaurant_name} (ID: {restaurant_id})")
        
        # Primero intentar obtener el menú desde menu_json (datos reales)
        menu_data = restaurant_config.get('menu_json')
        
        # Si no está disponible, intentar cargarlo desde archivo
        if not menu_data and restaurant_id:
            logger.info(f"MENÚ: menu_json no disponible, cargando desde archivo para {restaurant_id}")
            menu_data = load_restaurant_menu_json(restaurant_id)
            if menu_data:
                restaurant_config['menu_json'] = menu_data  # Cachear para próximas consultas
        
        # Fallback al método anterior como último recurso
        if not menu_data:
            logger.warning(f"MENÚ: No se pudo cargar desde archivo, intentando config.menu")
            config = restaurant_config.get('config', {})
            menu_data = config.get('menu', {})
        
        logger.info(f"MENÚ: Menu data source: {'menu_json' if restaurant_config.get('menu_json') else 'config.menu'}")
        logger.info(f"MENÚ: Menu data available: {bool(menu_data)}")
        
        if not menu_data:
            logger.warning(f"MENÚ: No hay datos de menú disponibles para {restaurant_name}")
            return None
            
        menu_text = f"*🍽️ Menú de {restaurant_name}*\n\n"
        
        # Obtener días de la semana
        dias_semana = menu_data.get('dias_semana', {})
        logger.info(f"MENÚ: Días de semana disponibles: {list(dias_semana.keys())}")
        
        # Mostrar algunos platos destacados de diferentes días
        platos_destacados = []
        for dia, comidas in dias_semana.items():
            if isinstance(comidas, dict):
                for momento, platos in comidas.items():
                    if isinstance(platos, list):
                        for plato in platos[:2]:  # Solo los primeros 2 platos por momento
                            if isinstance(plato, dict) and 'name' in plato and 'price' in plato:
                                platos_destacados.append(f"• {plato['name']} - ${plato['price']}")
        
        logger.info(f"MENÚ: Encontrados {len(platos_destacados)} platos destacados")
        
        if platos_destacados:
            menu_text += "*🌟 Algunos de nuestros platos destacados:*\n"
            menu_text += "\n".join(platos_destacados[:8])  # Máximo 8 platos
            menu_text += "\n\n"
        
        # Agregar información sobre menú especial para celíacos si existe
        menu_especial = menu_data.get('menu_especial', {})
        celiaco = menu_especial.get('celiaco', {})
        if celiaco:
            logger.info(f"MENÚ: Agregando opciones sin TACC")
            menu_text += "*🌾 Opciones sin TACC disponibles*\n"
            platos_principales = celiaco.get('platos_principales', [])
            if platos_principales:
                menu_text += "Platos principales sin gluten:\n"
                for plato in platos_principales[:3]:
                    menu_text += f"• {plato}\n"
            menu_text += "\n"
            
            nota = celiaco.get('nota', '')
            if nota:
                menu_text += f"ℹ️ *Nota:* {nota}\n\n"
        
        menu_text += "Para consultas específicas sobre ingredientes o disponibilidad, no dudes en preguntar.\n\n"
        menu_text += "¿Te gustaría hacer una reserva? Responde 'Reservar' 📅"
        
        logger.info(f"MENÚ: Menú generado exitosamente - longitud final: {len(menu_text)} caracteres")
        return menu_text
        
    except Exception as e:
        logger.error(f"Error al extraer menú del config: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def handle_menu_query(from_number, message, restaurant_config, session):
    """Maneja consultas sobre el menú usando el JSON del restaurante"""
    try:
        restaurant_name = restaurant_config.get('nombre', 'el restaurante')
        restaurant_id = restaurant_config.get('id')
        logger.info(f"MENÚ: Procesando consulta de menú para {restaurant_name} (ID: {restaurant_id}): '{message}'")
        
        # Asegurar que los datos JSON estén cargados
        restaurant_config = ensure_restaurant_data_loaded(restaurant_config)
        
        # Intentar obtener el menú del config JSON del restaurante
        menu_response = get_menu_from_config(restaurant_config)
        
        if menu_response:
            logger.info(f"MENÚ: Enviando menú desde config JSON - longitud: {len(menu_response)} caracteres")
            send_whatsapp_message(from_number, menu_response, restaurant_config)
            logger.info(f"✅ Consulta de menú respondida desde config JSON para {from_number}")
            return None
        else:
            logger.warning(f"MENÚ: No se encontró menú en config para {restaurant_name}, usando fallback")
            # Fallback si no hay menú en el config
            fallback_response = f"""*Menú de {restaurant_name}* 🍽️\n\nGracias por tu interés en nuestro menú. Por el momento, te recomiendo contactarnos directamente para conocer todos los detalles de nuestros deliciosos platos.\n\n📞 Llámanos o visítanos para más información.\n\n¿Te gustaría hacer una reserva? Responde 'Reservar'."""
            send_whatsapp_message(from_number, fallback_response, restaurant_config)
            logger.info(f"✅ Consulta de menú respondida con fallback para {from_number}")
            return None
    except Exception as e:
        logger.error(f"Error en handle_menu_query: {str(e)}")
        logger.error(traceback.format_exc())
        fallback_response = f"Gracias por preguntar sobre nuestro menú. Para información detallada, por favor contáctanos directamente. ¿Te gustaría hacer una reserva?"
        send_whatsapp_message(from_number, fallback_response, restaurant_config)
        logger.error(f"❌ Error en consulta de menú para {from_number}: {str(e)}")
        return None

def handle_ai_conversation(from_number, message, restaurant_config, session):
    """Maneja conversación general usando IA"""
    try:
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        info_json = restaurant_config.get('info_json', {})
        
        # PRIMERA VERIFICACIÓN: Detectar si es consulta de menú que se escapó del filtro principal
        mensaje_normalizado = message.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Palabras clave adicionales para detectar consultas de menú
        menu_phrases = [
            'que tienen para', 'que hay de', 'cuales son los', 'me gustaria ver', 'quiero ver el',
            'muestrame el', 'pueden mostrarme', 'tienen algo', 'que me recomiendan', 'que ofrecen',
            'cual es su', 'como es su', 'tienen disponible', 'que platillos', 'que comidas',
            'me pueden decir que', 'quisiera saber que', 'me interesa el', 'informacion del menu'
        ]
        
        if any(phrase in mensaje_normalizado for phrase in menu_phrases):
            logger.info(f"MENÚ: IA redirigiendo consulta de menú detectada tardíamente: {message}")
            return handle_menu_query(from_number, message, restaurant_config, session)
        
        # Ejecutar de forma síncrona la función async
        response = asyncio.run(deepseek_service.handle_general_conversation(message, info_json, restaurant_name))
        
        if response:
            # VERIFICAR si la IA está generando contenido de menú (prevenir respuestas inventadas)
            response_lower = response.lower()
            menu_generation_indicators = [
                'nuestro menu', 'tenemos platos', 'ofrecemos', 'nuestras especialidades',
                'contamos con', 'puedes elegir', 'disponemos de', '$', 'precio', 'cuesta'
            ]
            
            if any(indicator in response_lower for indicator in menu_generation_indicators):
                logger.warning(f"MENÚ: IA intentó generar menú falso, redirigiendo: {response[:100]}...")
                return handle_menu_query(from_number, message, restaurant_config, session)
            
            send_whatsapp_message(from_number, response, restaurant_config)
            logger.info(f"✅ Conversación general respondida con IA para {from_number}")
            return None
        else:
            contact_info = info_json.get('contact', {})
            restaurant_phone = contact_info.get('phone', 'nuestro número de contacto')
            fallback_response = f"""Gracias por tu mensaje. No estoy seguro de cómo ayudarte con eso específicamente, pero estaré encantado de asistirte con:\n\n🍽️ *Reservas* - Escribe 'Reservar'\n📋 *Menú* - Escribe 'Menu'\n📍 *Ubicación* - Escribe 'Ubicacion'\n\nPara otras consultas, puedes llamarnos al {restaurant_phone}."""
            send_whatsapp_message(from_number, fallback_response, restaurant_config)
            logger.info(f"✅ Conversación general respondida con fallback para {from_number}")
            return None
    except Exception as e:
        logger.error(f"❌ Error en conversación general para {from_number}: {str(e)}")
        contact_info = info_json.get('contact', {})
        restaurant_phone = contact_info.get('phone', 'nuestro número de contacto')
        fallback_response = f"Gracias por tu mensaje. Para asistencia personalizada, por favor llámanos al {restaurant_phone}."
        send_whatsapp_message(from_number, fallback_response, restaurant_config)
        return None

def handle_whatsapp_message(message, from_number, restaurant_config, message_sid=None):
    """Procesa mensajes de WhatsApp entrantes con sistema híbrido (estructurado + IA)"""
    try:
        mensaje_normalizado = message.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        if not restaurant_config:
            logger.error("❌ Restaurant config missing in handle_whatsapp_message")
            return None

        # CRÍTICO: Asegurar que los datos JSON estén cargados antes de procesar
        restaurant_config = ensure_restaurant_data_loaded(restaurant_config)

        restaurant_id = restaurant_config.get('id')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        info_json = restaurant_config.get('info_json', {})
        contact_info = info_json.get('contact', {})
        restaurant_phone = contact_info.get('phone', 'nuestro número de contacto')

        session = get_or_create_session(from_number, restaurant_id)
        
        # LOGGING DETALLADO PARA DEBUGGING
        logger.info(f"🔍 HANDLER DEBUG para {from_number}:")
        logger.info(f"  📨 Mensaje: '{message}'")
        logger.info(f"  🔄 Mensaje normalizado: '{mensaje_normalizado}'")
        logger.info(f"  🏪 Restaurante: {restaurant_name} (ID: {restaurant_id})")
        logger.info(f"  📊 Datos disponibles: menu_json={bool(restaurant_config.get('menu_json'))}, info_json={bool(restaurant_config.get('info_json'))}")
        logger.info(f"  📊 Estado sesión: {session.get('reservation_state', 'no definido')}")
        logger.info(f"  📝 Datos reserva: {session.get('reservation_data', {})}")
        logger.info(f"  ⏰ Timestamp sesión: {session.get('timestamp', 'no definido')}") 
        
        # PRIORIDAD MÁXIMA: Comandos que interrumpen cualquier flujo activo
        interrupt_commands = ['hola', 'hello', 'hi', 'menu', 'ubicacion', 'help', 'ayuda']
        # ✅ FIX: Usar palabras completas para evitar falsos positivos como "hi" en "jose marchiore"
        mensaje_words = mensaje_normalizado.split()
        is_interrupt_command = mensaje_normalizado in interrupt_commands or any(cmd in mensaje_words for cmd in interrupt_commands)
        
        # ✅ CRÍTICO: Detectar consultas de políticas como comando de interrupción
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

        # PRIORIDAD 2: Despedidas y agradecimientos (ANTES que cualquier otra lógica)
        farewell_keywords = [
            'gracias', 'chau', 'adios', 'adiós', 'hasta luego', 'nos vemos', 'bye', 'goodbye',
            'hasta la vista', 'que tengas', 'buen dia', 'buena tarde', 'buena noche',
            'muchas gracias', 'te agradezco', 'perfecto gracias', 'listo gracias',
            'ok gracias', 'genial gracias', 'excelente gracias', 'barbaro gracias'
        ]
        
        # Detectar despedidas con mayor precisión
        is_farewell = False
        
        # IMPORTANTE: No detectar como despedida si el mensaje contiene una calificación numérica (1-5)
        # ya que puede ser feedback que incluye "gracias"
        import re
        tiene_calificacion = re.search(r'^([1-5])\b', mensaje_normalizado)
        
        if not tiene_calificacion:  # Solo verificar despedidas si NO hay calificación
            for keyword in farewell_keywords:
                if keyword in mensaje_normalizado:
                    # Verificar que sea realmente una despedida y no parte de otra consulta
                    if any(word in mensaje_normalizado for word in ['gracias', 'chau', 'adios', 'adiós', 'bye']):
                        # Verificar que no sea un feedback con palabras positivas
                        feedback_indicators = ['sistema', 'gustado', 'bueno', 'excelente', 'malo', 'regular']
                        if not any(indicator in mensaje_normalizado for indicator in feedback_indicators):
                            is_farewell = True
                            break
        
        if is_farewell:
            logger.info(f"👋 DESPEDIDA: Detectada despedida en: '{message}'")
            
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
                saludos_conocidos = [
                    f"¡Hola {nombre_usuario}! Qué bueno saber de ti nuevamente 😊",
                    f"¡{nombre_usuario}! Me alegra verte por aquí otra vez 🌟",
                    f"¡Hola {nombre_usuario}! Bienvenido de vuelta a {restaurant_name} 😊",
                    f"¡{nombre_usuario}! Qué placer tenerte nuevamente con nosotros 🤗"
                ]
                saludo_personalizado = random.choice(saludos_conocidos)
                bienvenida = f"{saludo_personalizado}\n\n¿En qué podemos ayudarte hoy?\n\nPuedes escribir:\n➡️ *Reservar* - para hacer una nueva reserva\n➡️ *Menu* - para ver nuestro menú\n➡️ *Ubicacion* - para saber dónde encontrarnos"
            else:
                # Usuario nuevo - saludo estándar
                saludo_personalizado = "¡Hola! "
                bienvenida = f"{saludo_personalizado}Bienvenido a {restaurant_name}. 😊\n\n¿Cómo podemos ayudarte hoy?\n\nEscribe:\n➡️ *Reservar* - para hacer una reserva\n➡️ *Menu* - para ver nuestro menú\n➡️ *Ubicacion* - para saber dónde encontrarnos"
            
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
        location_keywords = ['ubicacion', 'direccion', 'donde estan', 'como llego', 'localizacion', 'mapa', 'coordenadas']
        if any(keyword in mensaje_normalizado for keyword in location_keywords):
            logger.info(f"📍 UBICACIÓN: Detectada consulta de ubicación: '{message}'")
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

def detect_and_save_feedback(from_number, message, restaurant_config):
    """
    Detecta si un mensaje contiene feedback y lo guarda en Supabase.
    
    Args:
        from_number (str): Número de WhatsApp del cliente
        message (str): Mensaje del usuario
        restaurant_config (dict): Configuración del restaurante
        
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
        return False