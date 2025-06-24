#!/usr/bin/env python
"""
Script simple para crear una reserva de prueba sin solicitar confirmación.
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    from utils.demo_utils import get_reservas_table
    
    # Obtener cliente Supabase
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo obtener el cliente Supabase")
        sys.exit(1)
    
    # IDs de los restaurantes
    restaurantes = {
        'gandolfo': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'ostende': 'e0f20795-d325-4af1-8603-1c52050048db'
    }
    
    # Datos para la reserva de prueba
    restaurante_id = restaurantes['gandolfo']  # Cambia a 'ostende' para probar con el otro restaurante
    
    # Datos de ejemplo para la reserva
    reserva = {
        'restaurante_id': restaurante_id,
        'nombre': 'Cliente de Prueba Automática',
        'fecha': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'hora': '20:30',
        'personas': 4,
        'telefono': '1123456789',
        'email': 'cliente@example.com',
        'comentarios': 'Reserva de prueba automática',
        'estado': 'Confirmada',
        'origen': 'script_test_auto'
    }
    
    # Determinar la tabla correcta a usar
    tabla, usa_restaurante_id = get_reservas_table(restaurante_id)
    print(f"Usando tabla: {tabla} (usa_restaurante_id={usa_restaurante_id})")
    
    # Insertar en Supabase
    response = supabase.table(tabla).insert(reserva).execute()
    
    if response.data and len(response.data) > 0:
        reserva_id = response.data[0].get('id')
        print(f"¡Reserva creada exitosamente!")
        print(f"ID de reserva: {reserva_id}")
        print(f"Restaurante: {'Gandolfo' if restaurante_id == restaurantes['gandolfo'] else 'Ostende'}")
        print(f"Fecha: {reserva['fecha']}, Hora: {reserva['hora']}")
        print(f"Tabla utilizada: {tabla}")
        sys.exit(0)
    else:
        print("No se pudo crear la reserva. No se recibieron datos de respuesta.")
        sys.exit(1)

except Exception as e:
    print(f"Error al crear la reserva: {str(e)}")
    sys.exit(1)
