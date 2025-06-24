#!/usr/bin/env python
"""
Script de diagnóstico para verificar la tabla reservas_prod.
"""
import sys
import os
import traceback
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    from config import SUPABASE_ENABLED, RESERVAS_TABLE, USE_PROD_TABLES
    
    print(f"Configuración del sistema:")
    print(f"- SUPABASE_ENABLED: {SUPABASE_ENABLED}")
    print(f"- USE_PROD_TABLES: {USE_PROD_TABLES}")
    print(f"- RESERVAS_TABLE: {RESERVAS_TABLE}")
    
    # Obtener cliente Supabase
    print("\nIntentando conectar con Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("Error: No se pudo obtener el cliente Supabase")
        sys.exit(1)
    
    print("✓ Cliente Supabase obtenido correctamente")
    
    # Verificar si la tabla existe
    print("\nVerificando si la tabla 'reservas_prod' existe...")
    try:
        # Intentar hacer una consulta simple para verificar si la tabla existe
        response = supabase.table('reservas_prod').select('id').limit(1).execute()
        print(f"✓ La tabla 'reservas_prod' existe y se puede consultar")
    except Exception as e:
        print(f"Error al consultar la tabla 'reservas_prod': {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    
    # Verificar estructura de la tabla
    print("\nVerificando estructura de la tabla 'reservas_prod'...")
    try:
        # Esta consulta SQL obtiene información sobre las columnas de la tabla
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reservas_prod'
        ORDER BY ordinal_position;
        """
        
        response = supabase.rpc('pgrest_sql', {'query': query}).execute()
        
        if response.data:
            print("Estructura de la tabla 'reservas_prod':")
            print("{:<20} {:<15} {:<10}".format("Columna", "Tipo", "Nullable"))
            print("-" * 50)
            
            for col in response.data:
                print("{:<20} {:<15} {:<10}".format(
                    col['column_name'], 
                    col['data_type'], 
                    col['is_nullable']
                ))
        else:
            print("No se pudo obtener la estructura de la tabla")
    except Exception as e:
        print(f"Error al obtener la estructura de la tabla: {str(e)}")
        print("Intentando método alternativo...")
        
        try:
            # Método alternativo: intentar insertar un registro de prueba con datos mínimos
            print("\nIntentando crear una reserva de prueba para diagnosticar la estructura requerida...")
            
            # Datos mínimos para una reserva
            test_data = {
                'nombre': 'TEST DIAGNÓSTICO',
                'fecha': datetime.now().date().isoformat(),
                'hora': '12:00',
                'personas': 2,
                'telefono': '1122334455',
                'email': 'test@example.com',
                'comentarios': 'Reserva de prueba para diagnóstico',
                'estado': 'Test',
                'origen': 'script_diagnostico',
                'restaurante_id': '6a117059-4c96-4e48-8fba-a59c71fd37cf'  # Gandolfo
            }
            
            # Intentar insertar
            response = supabase.table('reservas_prod').insert(test_data).execute()
            
            if response.data and len(response.data) > 0:
                print("✓ Reserva de prueba creada correctamente")
                print(f"ID de la reserva: {response.data[0].get('id')}")
                
                # Borrar la reserva de prueba
                delete_response = supabase.table('reservas_prod').delete().eq('id', response.data[0].get('id')).execute()
                print("✓ Reserva de prueba eliminada correctamente")
            else:
                print("No se pudo crear la reserva de prueba")
                if hasattr(response, 'error') and response.error:
                    print(f"Error: {response.error}")
        except Exception as inner_e:
            print(f"Error al crear reserva de prueba: {str(inner_e)}")
            traceback.print_exc()
    
    # Verificar existencia del restaurante
    print("\nVerificando existencia del restaurante Gandolfo...")
    try:
        restaurant_id = '6a117059-4c96-4e48-8fba-a59c71fd37cf'  # ID de Gandolfo
        response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✓ Restaurante encontrado:")
            restaurant = response.data[0]
            print(f"  - ID: {restaurant.get('id')}")
            print(f"  - Nombre: {restaurant.get('nombre_restaurante') or restaurant.get('nombre')}")
            print(f"  - Activo: {restaurant.get('activo')}")
        else:
            print(f"✕ El restaurante con ID '{restaurant_id}' no existe en la tabla 'restaurantes'")
            print("Esto podría causar problemas al crear reservas")
    except Exception as e:
        print(f"Error al verificar el restaurante: {str(e)}")
    
    print("\nDiagnóstico completo.")

except ImportError as e:
    print(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"Error general: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
