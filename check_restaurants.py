#!/usr/bin/env python3
"""
Script para consultar el ID real del restaurante en Supabase
"""
import sys
import os

# Agregar el directorio raíz al path para las importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase_client

def check_restaurant_ids():
    """Consulta los IDs de restaurantes en Supabase"""
    print("🔍 Consultando restaurantes en Supabase...")
    
    try:
        # Consultar todos los restaurantes
        response = supabase_client.table('restaurantes').select('*').execute()
        
        if response.data:
            print(f"\n📋 Encontrados {len(response.data)} restaurantes:")
            for restaurant in response.data:
                print(f"   - ID: {restaurant.get('id')}")
                print(f"     Nombre: {restaurant.get('nombre', 'N/A')}")
                print(f"     Admin ID: {restaurant.get('admin_id', 'N/A')}")
                print(f"     ---")
        else:
            print("❌ No se encontraron restaurantes")
            
    except Exception as e:
        print(f"❌ Error consultando restaurantes: {e}")

if __name__ == "__main__":
    check_restaurant_ids()
