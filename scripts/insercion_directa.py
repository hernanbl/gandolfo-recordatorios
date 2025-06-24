#!/usr/bin/env python
"""
Script extremadamente simple para probar una inserción en reservas_prod
"""
import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client

    # Conectar a Supabase
    print("Conectando a Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("Error: No se pudo conectar a Supabase")
        sys.exit(1)
    
    print("Conexión exitosa!")
    
    # Datos para la reserva de prueba
    reserva_test = {
        'nombre': 'Test Directo',
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'hora': '19:30',
        'personas': 4,
        'telefono': '1166686255',
        'email': 'test@example.com',
        'comentarios': 'Prueba directa',
        'estado': 'Prueba',
        'origen': 'script_directo',
        'restaurante_id': '6a117059-4c96-4e48-8fba-a59c71fd37cf'  # ID de Gandolfo
    }
    
    # Intento de inserción
    print(f"Intentando insertar en reservas_prod: {reserva_test}")
    response = supabase.table('reservas_prod').insert(reserva_test).execute()
    
    # Procesar resultado
    if hasattr(response, 'data') and response.data:
        reserva_id = response.data[0].get('id')
        print(f"¡Inserción exitosa! ID: {reserva_id}")
        print(f"Datos insertados: {response.data[0]}")
    else:
        print(f"Error en la inserción: {response}")
        if hasattr(response, 'error'):
            print(f"Detalles del error: {response.error}")
    
    print("Script finalizado.")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
