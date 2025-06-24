import uuid
from config import DEMO_RESTAURANT_ID, DEMO_RESTAURANT_NAME, DEMO_MODE_ENABLED

def is_demo_mode_enabled():
    """
    Verifica si el modo de demostración está habilitado en la configuración.
    """
    return DEMO_MODE_ENABLED

def is_demo_restaurant(restaurant_id):
    """
    Verifica si el restaurante proporcionado es el restaurante de demostración.
    
    Args:
        restaurant_id: ID del restaurante a verificar
        
    Returns:
        bool: True si es el restaurante de demostración, False en caso contrario
    """
    return restaurant_id == DEMO_RESTAURANT_ID

def get_demo_restaurant_info():
    """
    Retorna la información básica del restaurante de demostración.
    
    Returns:
        dict: Información del restaurante de demostración
    """
    return {
        "id": DEMO_RESTAURANT_ID,
        "name": DEMO_RESTAURANT_NAME,
        "is_demo": True
    }

def initialize_demo_restaurant_if_needed():
    """
    Inicializa el restaurante de demostración si está habilitado y no existe.
    Esta función debería ser llamada al inicio de la aplicación.
    
    Returns:
        bool: True si se inicializó el restaurante demo, False en caso contrario
    """
    if not is_demo_mode_enabled():
        return False
    
    import logging
    import hashlib
    from db.supabase_client import supabase_client
    from config import DEMO_RESTAURANT_ID, DEMO_RESTAURANT_NAME
    
    logger = logging.getLogger('utils.demo_utils')
    logger.info(f"Verificando si el restaurante de demostración existe: {DEMO_RESTAURANT_ID}")
    
    # Verificar si el restaurante ya existe en Supabase
    try:
        response = supabase_client.table('restaurantes').select('*').eq('id', DEMO_RESTAURANT_ID).execute()
        restaurant_exists = response.data and len(response.data) > 0
        
        if restaurant_exists:
            logger.info(f"Restaurante de demostración ya existe: {DEMO_RESTAURANT_NAME}")
        else:
            # Si no existe, crear el restaurante demo
            logger.info(f"Creando restaurante de demostración: {DEMO_RESTAURANT_NAME}")
            restaurant_data = {
                'id': DEMO_RESTAURANT_ID,
                'nombre': DEMO_RESTAURANT_NAME,
                'activo': True,
                'created_at': 'now()',
                'es_demo': True
            }
            
            insert_response = supabase_client.table('restaurantes').insert(restaurant_data).execute()
            if insert_response.data and len(insert_response.data) > 0:
                logger.info(f"Restaurante de demostración creado con éxito: {DEMO_RESTAURANT_ID}")
                restaurant_exists = True
            else:
                logger.error(f"Error al crear el restaurante de demostración: {insert_response.error}")
                return False
        
        # Verificar si existe un usuario administrador para el restaurante demo
        user_response = supabase_client.table('usuarios').select('*').eq('restaurante_id', DEMO_RESTAURANT_ID).execute()
        if user_response.data and len(user_response.data) > 0:
            logger.info(f"Usuario administrador para el restaurante demo ya existe")
        else:
            # Crear un usuario administrador para el restaurante demo
            logger.info(f"Creando usuario administrador para el restaurante demo")
            
            # Generar hash para la contraseña "demo123"
            password = "demo123"
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            user_data = {
                'id': str(uuid.uuid4()),
                'username': 'demo',
                'email': 'demo@gandolforesto.com',
                'password': password_hash,
                'nombre': 'Usuario Demo',
                'restaurante_id': DEMO_RESTAURANT_ID,
                'activo': True,
                'created_at': 'now()',
                'rol': 'admin'
            }
            
            user_insert_response = supabase_client.table('usuarios').insert(user_data).execute()
            if user_insert_response.data and len(user_insert_response.data) > 0:
                logger.info(f"Usuario administrador para el restaurante demo creado con éxito")
                logger.info(f"Credenciales: usuario='demo', contraseña='demo123'")
            else:
                logger.error(f"Error al crear usuario administrador para el restaurante demo: {user_insert_response.error}")
        
        # Añadir datos de muestra para el restaurante de demostración
        if restaurant_exists:
            logger.info("Verificando si se necesitan datos de muestra para el restaurante demo...")
            # Verificar si ya existen reservas
            reservas_response = supabase_client.table('reservas_prod').select('id').limit(1).execute()
            if not reservas_response.data or len(reservas_response.data) == 0:
                logger.info("No se encontraron reservas. Generando datos de muestra...")
                add_demo_sample_data()
            else:
                logger.info(f"Ya existen {len(reservas_response.data)} reservas en la tabla. No se generarán datos de muestra.")
        
        return restaurant_exists
            
    except Exception as e:
        logger.error(f"Error al inicializar restaurante de demostración: {str(e)}")
        return False

def get_reservas_table(restaurant_id=None):
    """
    Determina qué tabla de reservas usar basado en el ID del restaurante.
    Para el restaurante demo, siempre usa la tabla 'reservas' (legacy).
    Para otros restaurantes, usa 'reservas_prod'.
    
    Args:
        restaurant_id: ID del restaurante para determinar la tabla
        
    Returns:
        tuple: (nombre_tabla, usa_restaurante_id) donde usa_restaurante_id es un boolean
               que indica si la tabla tiene la columna restaurante_id
               
               Para tablas nuevas (reservas_prod): 
                   - La columna se llama 'restaurante_id'
               Para tablas legacy (reservas):
                   - La columna se llama 'restaurant_id'
    """
    from config import RESERVAS_TABLE
    import logging
    
    logger = logging.getLogger('utils.demo_utils')
    
    if restaurant_id and is_demo_restaurant(restaurant_id):
        logger.info(f"Usando tabla 'reservas' (legacy) para restaurante demo {restaurant_id}")
        return ('reservas', False)  # La tabla legacy usa 'restaurant_id'
    
    logger.info(f"Usando tabla '{RESERVAS_TABLE}' para restaurante {restaurant_id}")
    return (RESERVAS_TABLE, True)  # Las tablas nuevas usan 'restaurante_id'

def add_demo_sample_data():
    """
    Añade datos de muestra para el restaurante de demostración.
    Esta función crea un conjunto de reservas de ejemplo para mostrar la funcionalidad del dashboard.
    
    Returns:
        bool: True si se crearon los datos correctamente, False en caso contrario
    """
    import logging
    import subprocess
    import sys
    import os
    
    logger = logging.getLogger('utils.demo_utils')
    logger.info("Añadiendo datos de muestra para el restaurante de demostración (MODO SEGURO: SOLO AÑADE DATOS)")
    
    try:
        # VERIFICACIÓN DE SEGURIDAD: Comprobar si hay demasiadas reservas existentes antes de añadir más.
        # Esto es una medida general de precaución, aunque el script ya no borra.
        from db.supabase_client import supabase_client
        logger.info("Verificando cantidad de reservas existentes antes de añadir más datos demo...")
        
        reservas_count = 0
        try:
            # Contar solo las reservas de la tabla 'reservas' (legacy, usada por el demo)
            response = supabase_client.table('reservas_prod').select('id', count='exact').execute()
            reservas_count = response.count if response.count is not None else 0
            logger.info(f"Actualmente hay {reservas_count} reservas en la tabla 'reservas'.")
        except Exception as e:
            logger.error(f"Error al verificar reservas existentes: {str(e)}")
            return False
        
        # Límite de seguridad: si hay demasiadas reservas, no añadir más automáticamente.
        # Esto previene que la tabla crezca indefinidamente si el botón se presiona muchas veces.
        MAX_RESERVAS_DEMO_PERMITIDAS = 200  # Ajustar este límite según sea necesario
        if reservas_count > MAX_RESERVAS_DEMO_PERMITIDAS:
            logger.warning(f"Se encontraron {reservas_count} reservas existentes en la tabla 'reservas', que supera el límite de {MAX_RESERVAS_DEMO_PERMITIDAS}.")
            logger.warning("Para evitar una acumulación excesiva de datos de prueba, no se añadirán más reservas automáticamente.")
            return False
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'populate_demo_data.py')
        
        if not os.path.exists(script_path):
            logger.error(f"No se encontró el script para generar datos de muestra en {script_path}")
            return False
        
        logger.info("Todas las verificaciones de seguridad completadas. Ejecutando script de población de datos...")
            
        # Ejecutar el script como un proceso independiente
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, 
                               text=True)
        
        if result.returncode == 0:
            logger.info("Datos de muestra creados correctamente para el restaurante demo")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Error al crear datos de muestra: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error al añadir datos de muestra para el restaurante demo: {str(e)}")
        return False
