#!/usr/bin/env python
"""
Script simple para consultar las últimas reservas en reservas_prod.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    
    # Obtener cliente Supabase
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo obtener el cliente Supabase")
        sys.exit(1)
    
    # Consultar las últimas 10 reservas en reservas_prod
    tabla = 'reservas_prod'
    print(f"Consultando últimas reservas en {tabla}...")
    
    response = supabase.table(tabla).select('*').order('created_at', desc=True).limit(10).execute()
    
    if not hasattr(response, 'data') or not response.data:
        print(f"No se encontraron reservas en la tabla '{tabla}'")
        sys.exit(0)
    
    # Mostrar las reservas
    print(f"\nÚltimas {len(response.data)} reservas en {tabla}:")
    print("-" * 80)
    
    for i, reserva in enumerate(response.data, 1):
        # Datos principales
        restaurant_id = reserva.get('restaurante_id', 'Desconocido')
        nombre_restaurante = {
            '6a117059-4c96-4e48-8fba-a59c71fd37cf': 'Gandolfo',
            'e0f20795-d325-4af1-8603-1c52050048db': 'Ostende'
        }.get(restaurant_id, 'Otro')
        
        fecha = reserva.get('fecha', 'Sin fecha')
        if fecha and len(fecha) == 10:  # Formato YYYY-MM-DD
            fecha = f"{fecha[8:10]}/{fecha[5:7]}/{fecha[0:4]}"  # Convertir a DD/MM/YYYY
            
        print(f"Reserva #{i}:")
        print(f"  ID: {reserva.get('id', 'N/A')}")
        print(f"  Restaurante: {nombre_restaurante} ({restaurant_id[:8]}...)")
        print(f"  Nombre: {reserva.get('nombre', 'N/A')}")
        print(f"  Fecha/Hora: {fecha} - {reserva.get('hora', 'N/A')}")
        print(f"  Personas: {reserva.get('personas', 'N/A')}")
        print(f"  Estado: {reserva.get('estado', 'N/A')}")
        print(f"  Creada: {reserva.get('created_at', 'N/A')}")
        print("-" * 80)
    
except Exception as e:
    print(f"Error al consultar reservas: {str(e)}")
    sys.exit(1)
