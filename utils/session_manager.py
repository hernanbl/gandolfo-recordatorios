import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Simple file-based session storage
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sessions')
# Tiempo máximo de una sesión (30 minutos)
SESSION_TIMEOUT = timedelta(minutes=30)

def get_session_file_path(phone_number, restaurant_id):
    """
    Obtiene la ruta del archivo de sesión para un número de teléfono y un ID de restaurante.
    Maneja diferentes formatos de número y asegura que el ID del restaurante sea parte del path.
    """
    if not restaurant_id:
        logger.warning("get_session_file_path llamado sin restaurant_id. Usando directorio 'global_sessions'.")
        restaurant_specific_dir = os.path.join(SESSIONS_DIR, 'global_sessions')
    else:
        restaurant_specific_dir = os.path.join(SESSIONS_DIR, str(restaurant_id))

    # Asegurar que el directorio específico del restaurante (o global) existe
    try:
        if not os.path.exists(restaurant_specific_dir):
            os.makedirs(restaurant_specific_dir)
    except Exception as e:
        logger.error(f"Error al crear directorio de sesiones: {str(e)}")
        return None
        
    # Normalizar el número de teléfono para el nombre del archivo
    try:
        phone_clean = phone_number.replace('whatsapp:', '').replace('+', '_')
        
        if not phone_clean.startswith('_'):
            phone_clean = f"_{phone_clean}"
            
        filename = f"{phone_clean}.json"
        
        return os.path.join(restaurant_specific_dir, filename)
    except Exception as e:
        logger.error(f"Error al generar ruta de sesión: {str(e)}")
        return None

def is_session_expired(session_data):
    """
    Verifica si una sesión ha expirado basado en su última actualización.
    """
    if not session_data or 'timestamp' not in session_data:
        return True
        
    try:
        last_update = datetime.fromisoformat(session_data['timestamp'])
        return datetime.now() - last_update > SESSION_TIMEOUT
    except Exception as e:
        logger.error(f"Error al verificar expiración de sesión: {str(e)}")
        return True

def get_session(phone_number, restaurant_id):
    """
    Obtiene los datos de sesión para un número de teléfono y un ID de restaurante.
    """
    try:
        session_file = get_session_file_path(phone_number, restaurant_id)
        if not session_file:
            return None
            
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
                # Verificar si la sesión ha expirado
                if is_session_expired(session_data):
                    logger.info(f"Sesión expirada para {phone_number} en R:{restaurant_id}")
                    delete_session(phone_number, restaurant_id)
                    return None
                    
                return session_data
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar sesión para {phone_number} R:{restaurant_id}: {str(e)}")
        # Si el archivo está corrupto, intentar eliminarlo
        delete_session(phone_number, restaurant_id)
        return None
    except Exception as e:
        logger.error(f"Error al obtener sesión para {phone_number} R:{restaurant_id}: {str(e)}")
        return None

def save_session(phone_number, session_data, restaurant_id):
    """
    Guarda los datos de sesión para un número de teléfono y un ID de restaurante.
    """
    try:
        session_file = get_session_file_path(phone_number, restaurant_id)
        if not session_file:
            return False
        
        # Asegurar que el directorio (base y específico del restaurante) existe
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        
        session_data['timestamp'] = datetime.now().isoformat()
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Sesión guardada para {phone_number} (Restaurante: {restaurant_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar sesión para {phone_number} (Restaurante: {restaurant_id}): {str(e)}")
        return False

def delete_session(phone_number, restaurant_id):
    """
    Elimina los datos de sesión para un número de teléfono y un ID de restaurante.
    """
    try:
        session_file = get_session_file_path(phone_number, restaurant_id)
        if not session_file:
            return False
        
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"Sesión eliminada para {phone_number} (Restaurante: {restaurant_id})")
            return True
        logger.info(f"No se encontró sesión para eliminar para {phone_number} (Restaurante: {restaurant_id})")
        return False
        
    except Exception as e:
        logger.error(f"Error al eliminar sesión para {phone_number} (Restaurante: {restaurant_id}): {str(e)}")
        return False

def clear_all_sessions_for_restaurant(restaurant_id):
    """
    Elimina todos los archivos de sesión para un ID de restaurante específico.
    ¡Usar con precaución!
    """
    if not restaurant_id:
        logger.error("clear_all_sessions_for_restaurant llamado sin restaurant_id. Operación cancelada.")
        return False
        
    restaurant_specific_dir = os.path.join(SESSIONS_DIR, str(restaurant_id))
    count = 0
    if os.path.exists(restaurant_specific_dir):
        try:
            for filename in os.listdir(restaurant_specific_dir):
                file_path = os.path.join(restaurant_specific_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.json'):
                    os.remove(file_path)
                    count += 1
            logger.info(f"Se eliminaron {count} sesiones para el restaurante {restaurant_id}.")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar todas las sesiones para el restaurante {restaurant_id}: {str(e)}")
            return False
    else:
        logger.info(f"No se encontró directorio de sesiones para el restaurante {restaurant_id}. No hay sesiones que eliminar.")
        return True

def clear_all_sessions():
    """
    Elimina TODOS los archivos de sesión de TODOS los restaurantes.
    ¡USAR CON EXTREMA PRECAUCIÓN! Ideal para desarrollo o reseteos completos.
    """
    count = 0
    if os.path.exists(SESSIONS_DIR):
        try:
            for item_name in os.listdir(SESSIONS_DIR):
                item_path = os.path.join(SESSIONS_DIR, item_name)
                if os.path.isdir(item_path):
                    for filename in os.listdir(item_path):
                        file_path = os.path.join(item_path, filename)
                        if os.path.isfile(file_path) and filename.endswith('.json'):
                            os.remove(file_path)
                            count += 1
            logger.info(f"Se eliminaron {count} sesiones de todos los directorios.")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar todas las sesiones: {str(e)}")
            return False
    else:
        logger.info("El directorio principal de sesiones no existe. No hay sesiones que eliminar.")
        return True

def clear_session(phone_number, restaurant_id=None):
    """
    Elimina la sesión de un número específico
    """
    if restaurant_id is None:
        restaurant_id = "global_sessions"
    
    session_file = get_session_file_path(phone_number, restaurant_id)
    if session_file and os.path.exists(session_file):
        try:
            os.remove(session_file)
            logger.info(f"Sesión eliminada para {phone_number} en restaurante {restaurant_id}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando sesión: {str(e)}")
            return False
    return True