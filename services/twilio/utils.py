import re
from datetime import datetime
# PALABRAS_CLAVE_RESTAURANTE might need to be dynamic or loaded from restaurant_config if they vary per restaurant
from services.twilio.config import PALABRAS_CLAVE_RESTAURANTE # TODO: Review if this should be restaurant-specific
# CONVERSACIONES_ACTIVAS is problematic for multi-restaurant if it's a global dict keyed only by phone_number.
# This needs to be refactored or removed if session management handles activity tracking.
# from services.twilio.config import CONVERSACIONES_ACTIVAS # TODO: Re-evaluate CONVERSACIONES_ACTIVAS for multi-restaurant

# For now, let's assume CONVERSACIONES_ACTIVAS is not used or will be replaced by proper session state.

def es_consulta_relevante(mensaje, from_number=None, restaurant_id=None):
    """
    Verifica si un mensaje es relevante para el contexto del restaurante.
    TODO: Consider if PALABRAS_CLAVE_RESTAURANTE should be loaded from restaurant_config.
    TODO: CONVERSACIONES_ACTIVAS global is not suitable for multi-restaurant. Session state should handle this.
    """
    # Session-based activity check (preferred over global CONVERSACIONES_ACTIVAS)
    # if from_number and restaurant_id:
    #     session = get_or_create_session(from_number, restaurant_id) # Careful with circular dependencies if called from here
    #     if session and session.get('last_interaction_timestamp'):
    #         last_activity = datetime.fromisoformat(session['last_interaction_timestamp'])
    #         if (datetime.now() - last_activity).total_seconds() < 1800: # 30 minutes
    #             print(f"Mensaje considerado relevante por sesión activa para {from_number} en restaurante {restaurant_id}")
    #             return True
    
    mensaje_lower = mensaje.lower().strip()

    # Si el mensaje es muy corto, podría ser parte de un flujo (nombre, hora, etc.)
    if len(mensaje_lower) <= 50:
        if re.fullmatch(r'\d{1,2}:\d{2}', mensaje_lower): # Hora HH:MM
            return True
        if mensaje_lower.isdigit() and 1 <= int(mensaje_lower) <= 20: # Cantidad de personas
            return True
        if len(mensaje_lower.split()) >= 1 and all(palabra.isalpha() or "'" in palabra for palabra in mensaje_lower.split()): # Nombre (simplificado)
            return True
        if re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', mensaje_lower): # Email
            return True
        if re.fullmatch(r'(\+?54)?\d{10,13}', mensaje_lower.replace(' ', '')): # Teléfono (simplificado)
            return True
        respuestas_simples = ['si', 'sí', 'no', 'ok', 'okay', 'vale', 'confirmo', 'confirmar', 'cancelar', 'acepto', 'listo', 'dale']
        if mensaje_lower in respuestas_simples:
            return True
        # Check for simple numbers if a step is expecting one (e.g. option choice)
        if mensaje_lower.isdigit() and len(mensaje_lower) == 1: # e.g. choosing an option 1, 2, 3
            return True

    # TODO: Make PALABRAS_CLAVE_RESTAURANTE potentially restaurant-specific via restaurant_config
    # For example, restaurant_config.get('info_json', {}).get('keywords', PALABRAS_CLAVE_RESTAURANTE_DEFAULT)
    return any(palabra in mensaje_lower for palabra in PALABRAS_CLAVE_RESTAURANTE)

def get_day_name(fecha_str):
    """Obtiene el nombre del día de la semana a partir de una fecha en formato DD/MM/YYYY o YYYY-MM-DD"""
    try:
        if '/' in fecha_str:
            parts = fecha_str.split('/')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                if year < 100: # Handle YY format
                    year += 2000
                dt_obj = datetime(year, month, day)
            else:
                return fecha_str # Return original if not DD/MM/YYYY
        elif '-' in fecha_str:
            parts = fecha_str.split('-')
            if len(parts) == 3:
                year, month, day = map(int, parts)
                dt_obj = datetime(year, month, day)
            else:
                return fecha_str # Return original if not YYYY-MM-DD
        else:
            return fecha_str # Not a recognized format

        dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        return dias[dt_obj.weekday()]
    except ValueError:
        return fecha_str # Return original string if date parsing fails

# Gestión de sesiones para el flujo de reservas
# SESSIONS = {} # This global in-memory dict is removed, using file-based session_manager directly.

def get_or_create_session(phone_number, restaurant_id):
    """Obtiene o crea una sesión para un número de teléfono y restaurante específicos."""
    import logging
    from utils.session_manager import get_session as get_session_from_file, save_session as save_session_to_file
    
    logger = logging.getLogger(__name__)
    
    if not restaurant_id:
        logger.error("restaurant_id es requerido para obtener o crear una sesión.")
        raise ValueError("restaurant_id es requerido para obtener o crear una sesión.")

    # Normalizar el número de teléfono para consistencia antes de buscar/guardar
    normalized_phone = phone_number.replace('whatsapp:', '').replace('+', '')

    session = get_session_from_file(normalized_phone, restaurant_id)
    
    if not session:
        session = {
            'timestamp': datetime.now().isoformat(),
            'restaurant_id': restaurant_id, # Store restaurant_id in session for clarity if needed elsewhere
            'phone_number': normalized_phone, # Store normalized phone number
            'reservation_state': 'completada',  # Estado inicial seguro
            'reservation_data': {}
        }
        logger.info(f"Nueva sesión creada para {normalized_phone} en restaurante {restaurant_id}")
    else:
        session['timestamp'] = datetime.now().isoformat() # Update timestamp on access
        logger.debug(f"Sesión existente obtenida para {normalized_phone} en restaurante {restaurant_id}")
        logger.debug(f"Estado de reserva actual: {session.get('reservation_state', 'no definido')}")
    
    save_session_to_file(normalized_phone, session, restaurant_id)
    return session

# Modified to accept restaurant_config
def validar_paso_reserva(paso, valor, restaurant_config):
    """
    Valida un paso del proceso de reserva, potencialmente usando reglas específicas del restaurante.
    
    Args:
        paso (str): Paso a validar (nombre, fecha, hora, personas, telefono, email)
        valor (str): Valor a validar
        restaurant_config (dict): Configuración del restaurante, que puede contener reglas de validación.
        
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    # La lógica de validación real se delega a reservas_service.py
    # Esto es solo un passthrough, pero ahora incluye restaurant_config
    from services.reservas_service import validar_paso_reserva as validar_paso_especifico
    # validar_paso_especifico en reservas_service.py deberá ser adaptado para usar restaurant_config
    return validar_paso_especifico(paso, valor, restaurant_config)