"""
Script de mantenimiento para corregir la estructura de la tabla de restaurantes

Este script:
1. Asegura que todos los restaurantes tengan los campos 'estado' y 'activo'
2. Verifica que 'activo' sea coherente con el valor de 'estado'
3. Fija el valor de admin_id si falta
"""
from db.supabase_client import supabase
import logging
import sys
import os
from datetime import datetime

# Configuración del logger
log_file = 'logs/restaurantes_normalizacion.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def normalize_restaurant_fields():
    """
    Normaliza los campos de la tabla restaurantes para asegurar consistencia
    """
    try:
        # Obtener todos los restaurantes
        logger.info("Iniciando normalización de la tabla 'restaurantes'...")
        response = supabase.table('restaurantes').select('*').execute()
        
        if not response.data:
            logger.info("No se encontraron restaurantes en la base de datos.")
            return
            
        total_restaurantes = len(response.data)
        logger.info(f"Se encontraron {total_restaurantes} restaurantes para normalizar.")
        
        admin_ids = {}  # Para llevar un registro de los admin_ids por restaurante
        actualizados = 0
        
        for restaurante in response.data:
            restaurant_id = restaurante.get('id')
            if not restaurant_id:
                logger.warning(f"Se encontró un restaurante sin ID, no se puede actualizar.")
                continue
                
            # Verificar los campos estado y activo
            actualizar = False
            datos_actualizacion = {}
            
            # 1. Verificar campo 'estado'
            if 'estado' not in restaurante or not restaurante.get('estado'):
                # Determinar estado basado en el campo 'activo'
                if 'activo' in restaurante:
                    nuevo_estado = 'activo' if restaurante.get('activo') else 'no-activo'
                # O basado en config.activo
                elif restaurante.get('config', {}).get('activo'):
                    nuevo_estado = 'activo'
                else:
                    nuevo_estado = 'no-activo'
                    
                datos_actualizacion['estado'] = nuevo_estado
                actualizar = True
                logger.info(f"Restaurante {restaurant_id}: Asignar estado '{nuevo_estado}'")
            
            # 2. Verificar campo 'activo' sea coherente con 'estado'
            estado_actual = restaurante.get('estado', 'no-activo')
            deberia_activo = estado_actual == 'activo'
            
            if 'activo' not in restaurante or restaurante.get('activo') != deberia_activo:
                datos_actualizacion['activo'] = deberia_activo
                actualizar = True
                logger.info(f"Restaurante {restaurant_id}: Asignar activo={deberia_activo} (estado='{estado_actual}')")
            
            # 3. Verificar admin_id
            if 'admin_id' not in restaurante or not restaurante.get('admin_id'):
                # Si no tiene admin_id, intentar asignarle uno basado en otros restaurantes con el mismo nombre
                nombre = restaurante.get('nombre', '')
                if nombre in admin_ids:
                    datos_actualizacion['admin_id'] = admin_ids[nombre]
                    actualizar = True
                    logger.info(f"Restaurante {restaurant_id}: Asignar admin_id {admin_ids[nombre]} basado en nombre '{nombre}'")
            else:
                # Registrar este admin_id para futuros restaurantes con el mismo nombre
                admin_ids[restaurante.get('nombre', '')] = restaurante.get('admin_id')
            
            # Actualizar el restaurante si es necesario
            if actualizar:
                try:
                    update_response = supabase.table('restaurantes').update(datos_actualizacion).eq('id', restaurant_id).execute()
                    actualizados += 1
                    logger.info(f"Restaurante {restaurant_id} actualizado correctamente con {datos_actualizacion}")
                except Exception as e:
                    logger.error(f"Error al actualizar el restaurante {restaurant_id}: {str(e)}")
        
        logger.info(f"Normalización completa. {actualizados} de {total_restaurantes} restaurantes fueron actualizados.")
        
    except Exception as e:
        logger.error(f"Error durante la normalización de restaurantes: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    logger.info("=== Iniciando script de normalización de restaurantes ===")
    resultado = normalize_restaurant_fields()
    estado = "exitosamente" if resultado else "con errores"
    logger.info(f"Script completado {estado}.")
    sys.exit(0 if resultado else 1)
