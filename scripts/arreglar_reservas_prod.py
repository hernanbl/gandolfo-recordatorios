#!/usr/bin/env python
"""
Script simple para verificar y corregir la tabla reservas_prod
"""
import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    from config import SUPABASE_ENABLED, RESERVAS_TABLE, USE_PROD_TABLES
    
    print(f"CONFIGURACIÓN DEL SISTEMA:")
    print(f"- SUPABASE_ENABLED: {SUPABASE_ENABLED}")
    print(f"- USE_PROD_TABLES: {USE_PROD_TABLES}")
    print(f"- RESERVAS_TABLE: {RESERVAS_TABLE}")
    
    if not SUPABASE_ENABLED:
        print("ERROR: Supabase no está habilitado. Habilítalo en la configuración.")
        sys.exit(1)

    # Obtener cliente Supabase
    print("\nIntentando conectar con Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("ERROR: No se pudo obtener el cliente Supabase")
        sys.exit(1)
        
    print("✓ Conexión a Supabase establecida")
    
    # Verificar columna restaurante_id
    print("\nVerificando columna 'restaurante_id' en la tabla...")
    try:
        check_column_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'reservas_prod' AND column_name = 'restaurante_id'
        );
        """
        result = supabase.rpc('exec_sql', {'query': check_column_query}).execute()
        columna_existe = result.data[0]['exists'] if result.data else False
        
        if columna_existe:
            print("✓ La columna 'restaurante_id' existe en la tabla 'reservas_prod'")
        else:
            print("! La columna 'restaurante_id' NO existe en la tabla 'reservas_prod'")
            print("- Agregando la columna 'restaurante_id'...")
            
            add_column_query = """
            ALTER TABLE reservas_prod 
            ADD COLUMN restaurante_id UUID REFERENCES restaurantes(id);
            """
            supabase.rpc('exec_sql', {'query': add_column_query}).execute()
            print("✓ Columna 'restaurante_id' agregada correctamente")
    except Exception as e:
        print(f"ERROR al verificar o agregar columna: {str(e)}")
    
    # Probar inserción
    print("\nRealizando inserción de prueba...")
    try:
        # Datos de prueba
        datos_prueba = {
            'nombre': 'Test Script Simple',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'hora': '20:00',
            'personas': 2,
            'telefono': '1166686255',
            'email': 'test@example.com',
            'comentarios': 'Reserva de prueba desde script simple',
            'estado': 'Prueba',
            'origen': 'script_simple',
            'restaurante_id': '6a117059-4c96-4e48-8fba-a59c71fd37cf'  # ID de Gandolfo
        }
        
        response = supabase.table('reservas_prod').insert(datos_prueba).execute()
        
        if response.data:
            reserva_id = response.data[0].get('id')
            print(f"✓ Inserción exitosa! ID generado: {reserva_id}")
            
            # Eliminar la reserva de prueba
            supabase.table('reservas_prod').delete().eq('id', reserva_id).execute()
            print(f"✓ Reserva de prueba #{reserva_id} eliminada.")
        else:
            print(f"! La inserción falló: {response}")
    except Exception as e:
        print(f"ERROR en la inserción de prueba: {str(e)}")
    
    print("\nVERIFICACIÓN COMPLETADA")

except ImportError as e:
    print(f"ERROR de importación: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR general: {str(e)}")
    sys.exit(1)
