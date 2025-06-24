#!/usr/bin/env python3
"""
Consultar restaurantes para obtener UUIDs correctos
"""
import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.append('/Volumes/AUDIO/gandolfo_now')

from db.supabase_client import supabase_client
import json

def consultar_restaurantes():
    """Consulta todos los restaurantes para ver sus IDs"""
    
    print("🔍 Consultando restaurantes en Supabase...")
    print("=" * 70)
    
    try:
        supabase = supabase_client
        if not supabase:
            print("❌ Error: Cliente Supabase no disponible")
            return
        
        # Consultar tabla de restaurantes
        print("📊 Consultando tabla 'restaurantes'...")
        
        try:
            response = supabase.table('restaurantes').select('*').execute()
            
            if response.data:
                print(f"✅ Encontrados {len(response.data)} restaurantes:")
                print()
                
                for resto in response.data:
                    print(f"📍 RESTAURANTE:")
                    for key, value in resto.items():
                        print(f"   {key}: {value}")
                    print("-" * 50)
                    
                print("\n🎯 MAPEO DE IDs:")
                for resto in response.data:
                    nombre = resto.get('nombre', resto.get('name', 'Sin nombre'))
                    uuid_id = resto.get('id')
                    print(f"   '{nombre}' -> UUID: {uuid_id}")
                    
            else:
                print("📭 No se encontraron restaurantes")
                
        except Exception as query_error:
            print(f"❌ Error consultando restaurantes: {str(query_error)}")
            
            # Intentar con diferentes nombres de tabla
            tablas_posibles = ['restaurante', 'restaurants', 'restaurant_config']
            
            for tabla in tablas_posibles:
                try:
                    print(f"\n🔍 Probando tabla '{tabla}'...")
                    response = supabase.table(tabla).select('*').limit(5).execute()
                    if response.data:
                        print(f"✅ Tabla '{tabla}' existe con {len(response.data)} registros")
                        ejemplo = response.data[0]
                        print(f"   Columnas: {list(ejemplo.keys())}")
                        break
                except Exception as e:
                    print(f"❌ Tabla '{tabla}' no encontrada: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    consultar_restaurantes()
