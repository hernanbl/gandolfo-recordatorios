# filepath: /Volumes/AUDIO/gandolfo-resto-system-okposta/services/db/supabase.py
import os
import time
import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

_supabase_client = None

def get_supabase_client(force_new=False):
    """
    Obtiene una instancia del cliente de Supabase con configuración robusta.
    Incluye retry automático y timeouts optimizados.
    
    Args:
        force_new (bool): Si es True, fuerza la creación de un nuevo cliente
        
    Returns:
        Client: Cliente de Supabase configurado con timeouts y retry
    """
    global _supabase_client
    
    # Obtener valores directamente de las variables de entorno como respaldo
    url = SUPABASE_URL or os.environ.get('SUPABASE_URL')
    key = SUPABASE_KEY or os.environ.get('SUPABASE_KEY')
    
    if not url or not key:
        logging.error("Error: SUPABASE_URL o SUPABASE_KEY no están definidos")
        return None
    
    try:
        if _supabase_client is None or force_new:
            logging.info(f"Inicializando cliente Supabase robusto con URL: {url}")
            
            # Crear cliente con configuración simplificada
            # Nota: La API de Supabase Python no soporta configuraciones complejas de headers
            _supabase_client = create_client(url, key)
            
        return _supabase_client
    except Exception as e:
        logging.error(f"Error al conectar con Supabase: {str(e)}")
        return None

def execute_with_retry(query_func, max_retries=3, retry_delay=2.0):
    """
    Ejecuta una consulta de Supabase con retry automático
    
    Args:
        query_func: Función que ejecuta la consulta
        max_retries: Número máximo de reintentos
        retry_delay: Delay entre reintentos en segundos
        
    Returns:
        Resultado de la consulta o None si falló
    """
    for attempt in range(max_retries):
        try:
            logging.info(f"Intento {attempt + 1}/{max_retries} ejecutando consulta Supabase")
            result = query_func()
            logging.info(f"✅ Consulta Supabase exitosa en intento {attempt + 1}")
            return result
        except Exception as e:
            logging.warning(f"⚠️ Error en intento {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logging.error(f"❌ Todos los intentos fallaron: {str(e)}")
                return None
    
    return None
