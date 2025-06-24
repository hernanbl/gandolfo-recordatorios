#!/usr/bin/env python
"""
Script para probar la creación directa de una reserva en la tabla reservas_prod.
Este script crea una reserva de prueba en la tabla correcta para verificar el proceso 
sin necesidad de usar el chatbot.
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
logger = logging.getLogger('crear_reserva_test')

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    from config import SUPABASE_ENABLED
    from utils.demo_utils import get_reservas_table
except ImportError as e:
    logger.error(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)

def crear_reserva_test():
    """
    Crea una reserva de prueba directamente en la base de datos.
    Simula el proceso que ocurriría cuando un usuario hace una reserva a través del chatbot.
    """

    logger.info("Iniciando proceso de creación de reserva de prueba...")

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
    
    # Datos de ejemplo para la reserva
    reserva = {
        'restaurante_id': restaurantes['gandolfo'],  # Puedes cambiar a 'ostende' si lo prefieres
        'nombre': 'Cliente de Prueba',
        'fecha': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),  # 3 días en el futuro
        'hora': '20:30',
        'personas': 4,
        'telefono': '1123456789',
        'email': 'cliente@example.com',
        'comentarios': 'Reserva de prueba creada con script',
        'estado': 'Confirmada',
        'origen': 'script_test'
    }
    
    logger.info("Creando reserva con los siguientes datos:")
    logger.info(f"  Restaurante: {'Gandolfo' if reserva['restaurante_id'] == restaurantes['gandolfo'] else 'Ostende'}")
    logger.info(f"  Nombre: {reserva['nombre']}")
    logger.info(f"  Fecha/Hora: {reserva['fecha']} a las {reserva['hora']}")
    logger.info(f"  Personas: {reserva['personas']}")
    
    # Confirmar antes de insertar
    confirmacion = input("\n¿Proceder con la creación de esta reserva? (s/n): ")
    if confirmacion.lower() != 's':
        logger.info("Operación cancelada.")
        return False
    
    # Determinar la tabla correcta a usar
    tabla, usa_restaurante_id = get_reservas_table(reserva['restaurante_id'])
    logger.info(f"Usando tabla: {tabla} (usa_restaurante_id={usa_restaurante_id})")
    
    try:
        # Insertar en Supabase
        response = supabase.table(tabla).insert(reserva).execute()
        
        if response.data and len(response.data) > 0:
            reserva_id = response.data[0].get('id')
            logger.info(f"¡Reserva creada exitosamente!")
            logger.info(f"ID de reserva: {reserva_id}")
            
            # Mostrar datos de la reserva creada
            logger.info("\nDatos de la reserva creada:")
            for key, value in response.data[0].items():
                logger.info(f"  {key}: {value}")
            
            return True
        else:
            logger.error(f"Error al crear la reserva: {response.error if hasattr(response, 'error') else 'Error desconocido'}")
            return False
    
    except Exception as e:
        logger.error(f"Error al crear la reserva: {str(e)}")
        return False

def main():
    """Función principal"""
    print("\n===== CREADOR DE RESERVA DE PRUEBA =====\n")
    
    resultado = crear_reserva_test()
    
    if resultado:
        print("\n✅ Reserva creada exitosamente. Para verificarla, ejecuta:")
        print("   python scripts/verificar_reservas_prod.py prod")
    else:
        print("\n❌ No se pudo crear la reserva.")
    
    print("\n===== FIN DEL PROCESO =====")

if __name__ == "__main__":
    main()
