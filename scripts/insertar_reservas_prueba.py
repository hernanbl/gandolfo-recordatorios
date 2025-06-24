#!/usr/bin/env python
"""
Script para crear reservas de prueba en la tabla reservas_prod para ambos restaurantes.
Este script inserta reservas directamente en la tabla reservas_prod tanto para Gandolfo como para Ostende
y verifica que se hayan creado correctamente.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import traceback
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('insertar_reservas_prueba')

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    from config import SUPABASE_ENABLED, USE_PROD_TABLES, RESERVAS_TABLE
    from utils.demo_utils import get_reservas_table
except ImportError as e:
    logger.error(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)

def insertar_reservas_prueba():
    """
    Crea reservas de prueba directamente en la tabla reservas_prod para ambos restaurantes.
    """
    logger.info("Iniciando creación de reservas de prueba...")

    # Verificar configuración
    logger.info(f"USE_PROD_TABLES: {USE_PROD_TABLES}")
    logger.info(f"RESERVAS_TABLE configurado como: {RESERVAS_TABLE}")
    
    if not SUPABASE_ENABLED:
        logger.error("Error: Supabase no está habilitado en la configuración")
        return False
    
    # Obtener cliente Supabase
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Error: No se pudo obtener el cliente Supabase")
        return False
    
    # IDs de los restaurantes
    restaurantes = {
        'gandolfo': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'ostende': 'e0f20795-d325-4af1-8603-1c52050048db'
    }
    
    # Lista de reservas a crear (una para cada restaurante)
    reservas = [
        {
            'restaurante_id': restaurantes['gandolfo'],
            'nombre': 'Cliente Test Gandolfo',
            'fecha': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'hora': '20:30',
            'personas': 4,
            'telefono': '1123456789',
            'email': 'test.gandolfo@example.com',
            'comentarios': 'Reserva de prueba para Gandolfo',
            'estado': 'Pendiente',
            'origen': 'script_test'
        },
        {
            'restaurante_id': restaurantes['ostende'],
            'nombre': 'Cliente Test Ostende',
            'fecha': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'hora': '13:00',
            'personas': 2,
            'telefono': '1198765432',
            'email': 'test.ostende@example.com',
            'comentarios': 'Reserva de prueba para Ostende',
            'estado': 'Pendiente',
            'origen': 'script_test'
        }
    ]
    
    ids_creados = []
    
    for reserva in reservas:
        # Determinar el restaurante
        restaurante_nombre = "Gandolfo" if reserva['restaurante_id'] == restaurantes['gandolfo'] else "Ostende"
        
        logger.info(f"\n== Creando reserva para {restaurante_nombre} ==")
        logger.info(f"Nombre: {reserva['nombre']}")
        logger.info(f"Fecha/Hora: {reserva['fecha']} a las {reserva['hora']}")
        logger.info(f"Personas: {reserva['personas']}")
        
        # Determinar la tabla correcta a usar
        tabla, usa_restaurante_id = get_reservas_table(reserva['restaurante_id'])
        logger.info(f"Usando tabla: {tabla} (usa_restaurante_id={usa_restaurante_id})")
        
        if tabla != 'reservas_prod':
            logger.warning(f"¡Advertencia! Se detectó que usaría la tabla '{tabla}' en lugar de 'reservas_prod'.")
            tabla_original = tabla
            tabla = 'reservas_prod'
            logger.info(f"Forzando uso de tabla 'reservas_prod' para esta prueba")
        
        try:
            # Insertar en Supabase
            response = supabase.table(tabla).insert(reserva).execute()
            
            if response.data and len(response.data) > 0:
                reserva_id = response.data[0].get('id')
                logger.info(f"✅ Reserva creada exitosamente para {restaurante_nombre}!")
                logger.info(f"ID de reserva: {reserva_id}")
                ids_creados.append(reserva_id)
                
                # Mostrar datos de la reserva creada
                logger.info(f"Datos de la reserva creada:")
                for key, value in response.data[0].items():
                    if key not in ['id', 'restaurante_id']:  # Omitir ID por brevedad
                        logger.info(f"  {key}: {value}")
            else:
                logger.error(f"❌ Error al crear la reserva para {restaurante_nombre}: {response.error if hasattr(response, 'error') else 'Error desconocido'}")
        
        except Exception as e:
            logger.error(f"❌ Error al crear la reserva para {restaurante_nombre}: {str(e)}")
            logger.error(traceback.format_exc())
    
    if ids_creados:
        logger.info(f"\n✅ Se crearon exitosamente {len(ids_creados)} reservas de prueba")
        return True
    else:
        logger.error("❌ No se pudo crear ninguna reserva de prueba")
        return False

def confirmar_con_usuario():
    """
    Solicita confirmación al usuario antes de proceder.
    """
    print("\n¡ATENCIÓN!")
    print("Este script creará reservas de prueba en la tabla 'reservas_prod' para los restaurantes Gandolfo y Ostende.")
    print("Esta acción no puede deshacerse automáticamente.")
    
    while True:
        respuesta = input("\n¿Desea continuar? (s/n): ").strip().lower()
        if respuesta == 's':
            return True
        elif respuesta == 'n':
            return False
        else:
            print("Por favor, ingrese 's' para sí o 'n' para no.")

def main():
    """Función principal"""
    print("\n===== CREADOR DE RESERVAS DE PRUEBA =====\n")
    
    # Verificar la configuración actual
    logger.info("Verificando configuración del sistema...")
    logger.info(f"USE_PROD_TABLES: {USE_PROD_TABLES}")
    logger.info(f"RESERVAS_TABLE configurado como: {RESERVAS_TABLE}")
    
    if not confirmar_con_usuario():
        print("Operación cancelada por el usuario.")
        return
    
    resultado = insertar_reservas_prueba()
    
    if resultado:
        print("\n✅ Reservas de prueba creadas exitosamente. Para verificarlas, ejecuta:")
        print("   python scripts/verificar_reservas_prod.py prod")
    else:
        print("\n❌ No se pudieron crear las reservas de prueba.")
    
    print("\n===== FIN DEL PROCESO =====")

if __name__ == "__main__":
    main()
