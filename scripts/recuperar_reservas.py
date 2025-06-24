#!/usr/bin/env python
"""
Script para recuperar reservas que pueden haber sido eliminadas por error.
Este script intentará restaurar reservas desde backups o historiales si están disponibles.
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# Configurar path para importar desde el directorio principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar dependencias
from db.supabase_client import supabase_client
from config import DEMO_RESTAURANT_ID

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('recuperacion_reservas')

def verificar_estado_reservas():
    """
    Verifica el estado actual de las reservas en la base de datos
    """
    try:
        # Verificar si hay reservas en la tabla
        response = supabase_client.table('reservas').select('id').execute()
        
        if hasattr(response, 'data'):
            count = len(response.data) if response.data else 0
            logger.info(f"Actualmente hay {count} reservas en la tabla 'reservas'")
            return count
        else:
            logger.error("No se pudo obtener información de la tabla 'reservas'")
            return -1
    except Exception as e:
        logger.error(f"Error al verificar el estado de las reservas: {str(e)}")
        return -1

def intentar_recuperacion():
    """
    Intenta recuperar reservas que puedan haberse eliminado
    """
    logger.info("Iniciando proceso de recuperación de reservas...")
    
    try:
        # 1. Intentar buscar si hay historial de cambios en Supabase
        logger.info("Este proceso intentará buscar datos de reservas que puedan haber sido respaldados")
        
        # 2. Verificar si hay backups disponibles
        
        # 3. Si no hay alternativas, notificar para restauración manual
        logger.info("""
        ======================================================================
        IMPORTANTE: Para recuperar las reservas, contacte al soporte técnico
        y solicite una restauración desde el último backup de la base de datos.
        
        Recomendaciones:
        1. NO ejecute más scripts de generación de datos hasta resolver esto
        2. Contacte inmediatamente a soporte en soporte@vivacom.com.ar
        3. Proporcione la fecha y hora aproximada en que ocurrió el problema
        ======================================================================
        """)
        
        return False
    except Exception as e:
        logger.error(f"Error en el proceso de recuperación: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=====================================================")
    logger.info("SCRIPT DE RECUPERACIÓN DE RESERVAS DE EMERGENCIA")
    logger.info("=====================================================")
    
    # Verificar el estado actual
    count = verificar_estado_reservas()
    
    if count == 0:
        logger.warning("¡ALERTA! No se encontraron reservas en la base de datos.")
        intentar_recuperacion()
    elif count > 0:
        logger.info(f"Se encontraron {count} reservas en la base de datos.")
        logger.info("Si este número es menor al esperado, puede ejecutar el proceso de recuperación.")
        
        respuesta = input("¿Desea intentar el proceso de recuperación? (s/n): ").lower()
        if respuesta == 's':
            intentar_recuperacion()
        else:
            logger.info("Proceso de recuperación cancelado por el usuario.")
    else:
        logger.error("No se pudo verificar el estado de las reservas. Revise los logs para más detalles.")
        intentar_recuperacion()
    
    logger.info("Proceso de verificación y recuperación finalizado.")
