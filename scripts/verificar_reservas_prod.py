#!/usr/bin/env python
"""
Script para verificar la correcta creación de reservas en la tabla reservas_prod.
Este script muestra las reservas en la tabla reservas_prod y puede ayudar a verificar
que las reservas se están creando correctamente después de la migración.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('verificar_reservas_prod')

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client, supabase_client
    from config import RESERVAS_TABLE, USE_PROD_TABLES, SUPABASE_ENABLED
    from utils.demo_utils import get_reservas_table
except ImportError as e:
    logger.error(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)

def verificar_configuracion():
    """Verifica la configuración actual del sistema relacionada con las tablas de reservas"""
    
    logger.info("== VERIFICACIÓN DE CONFIGURACIÓN ==")
    logger.info(f"USE_PROD_TABLES: {USE_PROD_TABLES}")
    logger.info(f"RESERVAS_TABLE configurado como: {RESERVAS_TABLE}")
    logger.info(f"SUPABASE_ENABLED: {SUPABASE_ENABLED}")
    
    # Verificar configuración para diferentes IDs de restaurantes
    restaurantes = {
        'gandolfo': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'ostende': 'e0f20795-d325-4af1-8603-1c52050048db'
    }
    
    for nombre, id in restaurantes.items():
        tabla, usa_restaurante_id = get_reservas_table(id)
        logger.info(f"Restaurante {nombre} ({id}): usa tabla '{tabla}' con campo {'restaurante_id' if usa_restaurante_id else 'restaurant_id'}")

    return True

def contar_reservas_por_tabla():
    """Muestra la cantidad de reservas en cada tabla"""
    
    if not SUPABASE_ENABLED or not supabase_client:
        logger.error("Supabase no está habilitado o el cliente no está disponible")
        return False
    
    try:
        logger.info("== CONTEO DE RESERVAS POR TABLA ==")
        
        # Contar reservas en la tabla legacy
        response_legacy = supabase_client.table('reservas').select('id', count='exact').execute()
        count_legacy = response_legacy.count if hasattr(response_legacy, 'count') and response_legacy.count is not None else 0
        
        # Contar reservas en la tabla nueva
        response_prod = supabase_client.table('reservas_prod').select('id', count='exact').execute()
        count_prod = response_prod.count if hasattr(response_prod, 'count') and response_prod.count is not None else 0
        
        logger.info(f"Tabla 'reservas' (legacy): {count_legacy} reservas")
        logger.info(f"Tabla 'reservas_prod' (nueva): {count_prod} reservas")
        
        return True
    
    except Exception as e:
        logger.error(f"Error al contar reservas: {str(e)}")
        return False

def mostrar_ultimas_reservas(tabla='reservas_prod', limite=10):
    """Muestra las últimas reservas realizadas en la tabla especificada"""
    
    if not SUPABASE_ENABLED or not supabase_client:
        logger.error("Supabase no está habilitado o el cliente no está disponible")
        return False
    
    try:
        logger.info(f"== ÚLTIMAS {limite} RESERVAS EN TABLA '{tabla}' ==")
        
        response = supabase_client.table(tabla).select('*').order('created_at', desc=True).limit(limite).execute()
        
        if not hasattr(response, 'data') or not response.data:
            logger.info(f"No se encontraron reservas en la tabla '{tabla}'")
            return True
        
        for i, reserva in enumerate(response.data, 1):
            # Extraer y formatear fecha/hora de creación
            created_at = reserva.get('created_at', 'Desconocido')
            if isinstance(created_at, str) and 'T' in created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            # Formatear fecha de reserva
            fecha = reserva.get('fecha', 'Desconocido')
            if isinstance(fecha, str) and '-' in fecha and len(fecha) == 10:
                try:
                    dt = datetime.strptime(fecha, '%Y-%m-%d')
                    fecha = dt.strftime('%d/%m/%Y')
                except:
                    pass
            
            # Imprimir detalles de la reserva
            logger.info(f"\n[{i}] ID: {reserva.get('id')}")
            logger.info(f"    Creada: {created_at}")
            logger.info(f"    Restaurante: {reserva.get('restaurante_id', reserva.get('restaurant_id', 'No especificado'))}")
            logger.info(f"    Nombre: {reserva.get('nombre', 'No especificado')}")
            logger.info(f"    Fecha: {fecha}")
            logger.info(f"    Hora: {reserva.get('hora', 'No especificado')}")
            logger.info(f"    Personas: {reserva.get('personas', 'No especificado')}")
            logger.info(f"    Teléfono: {reserva.get('telefono', 'No especificado')}")
            logger.info(f"    Email: {reserva.get('email', 'No especificado')}")
            logger.info(f"    Estado: {reserva.get('estado', 'No especificado')}")
            logger.info(f"    Origen: {reserva.get('origen', 'No especificado')}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error al mostrar reservas: {str(e)}")
        return False

def verificar_conversion_campos():
    """Compara los campos entre reservas en ambas tablas"""
    
    if not SUPABASE_ENABLED or not supabase_client:
        logger.error("Supabase no está habilitado o el cliente no está disponible")
        return False
    
    try:
        logger.info("== VERIFICACIÓN DE CONVERSIÓN DE CAMPOS ==")
        
        # Estructura esperada de cada tabla
        estructura_legacy = {
            'id': 'UUID',
            'nombre': 'String',
            'fecha': 'Date (YYYY-MM-DD)',
            'hora': 'String (HH:MM)',
            'personas': 'Number',
            'telefono': 'String',
            'email': 'String',
            'comentarios': 'String',
            'estado': 'String',
            'origen': 'String',
            'restaurant_id': 'UUID', # Campo legacy
            'created_at': 'Timestamp'
        }
        
        estructura_prod = {
            'id': 'UUID',
            'nombre': 'String',
            'fecha': 'Date (YYYY-MM-DD)',
            'hora': 'String (HH:MM)',
            'personas': 'Number',
            'telefono': 'String',
            'email': 'String',
            'comentarios': 'String',
            'estado': 'String',
            'origen': 'String',
            'restaurante_id': 'UUID', # Campo nuevo
            'created_at': 'Timestamp'
        }
        
        logger.info("Estructura de tabla legacy (reservas):")
        for campo, tipo in estructura_legacy.items():
            logger.info(f"  - {campo}: {tipo}")
        
        logger.info("\nEstructura de tabla nueva (reservas_prod):")
        for campo, tipo in estructura_prod.items():
            logger.info(f"  - {campo}: {tipo}")
        
        logger.info("\nPrincipal diferencia: 'restaurant_id' -> 'restaurante_id'")
        
        return True
    
    except Exception as e:
        logger.error(f"Error al verificar conversión de campos: {str(e)}")
        return False

def mostrar_ayuda():
    """Muestra las opciones disponibles para el script"""
    
    print("""
Script para verificar la correcta creación de reservas en la tabla reservas_prod.

Uso:
    python verificar_reservas_prod.py [opción]

Opciones:
    config      - Verificar configuración actual
    contar      - Contar reservas en ambas tablas
    legacy      - Mostrar últimas reservas en tabla legacy (reservas)
    prod        - Mostrar últimas reservas en tabla nueva (reservas_prod)
    all         - Ejecutar todas las verificaciones
    ayuda       - Mostrar esta ayuda
    
Por defecto (sin argumentos) muestra las últimas reservas en la tabla nueva.
""")

def main():
    """Función principal"""
    
    print("\n===== VERIFICADOR DE RESERVAS EN RESERVAS_PROD =====\n")
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        opcion = sys.argv[1].lower()
        
        if opcion == 'config':
            verificar_configuracion()
        elif opcion == 'contar':
            contar_reservas_por_tabla()
        elif opcion == 'legacy':
            mostrar_ultimas_reservas(tabla='reservas')
        elif opcion == 'prod':
            mostrar_ultimas_reservas()
        elif opcion == 'all':
            verificar_configuracion()
            contar_reservas_por_tabla()
            mostrar_ultimas_reservas(tabla='reservas')
            mostrar_ultimas_reservas()
            verificar_conversion_campos()
        elif opcion in ['help', 'ayuda', '--help', '-h']:
            mostrar_ayuda()
        else:
            print(f"Opción desconocida: {opcion}")
            mostrar_ayuda()
    else:
        # Sin argumentos, mostrar últimas reservas en la tabla nueva
        verificar_configuracion()
        mostrar_ultimas_reservas()
    
    print("\n===== FIN DEL VERIFICADOR =====")

if __name__ == "__main__":
    main()
