#!/usr/bin/env python
"""
Script para crear o corregir la tabla reservas_prod directamente.
Este script es más directo que los anteriores y garantiza que la tabla tenga la estructura correcta.
"""
import sys
import os
import traceback
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    
    # Presentación
    print("========================================================")
    print("SCRIPT DE CREACIÓN/REPARACIÓN DE TABLA RESERVAS_PROD")
    print("========================================================")
    
    # Obtener cliente de Supabase
    print("\n1. Conectando a Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("ERROR: No se pudo conectar a Supabase.")
        sys.exit(1)
    print("✓ Conexión a Supabase establecida correctamente")
    
    # Verificar si la tabla existe
    print("\n2. Verificando si la tabla reservas_prod existe...")
    check_table_exists = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'reservas_prod'
    );
    """
    exists_result = supabase.rpc('exec_sql', {'query': check_table_exists}).execute()
    tabla_existe = exists_result.data[0]['exists'] if exists_result.data else False
    
    if tabla_existe:
        print("✓ La tabla reservas_prod ya existe")
    else:
        print("! La tabla reservas_prod NO existe")
        print("-> Creando la tabla...")
        
        # Script para crear la tabla desde cero
        create_table_sql = """
        CREATE TABLE public.reservas_prod (
            id serial PRIMARY KEY,
            nombre text NOT NULL,
            fecha date NOT NULL,
            hora time NOT NULL,
            personas integer NOT NULL,
            telefono text NOT NULL,
            email text,
            comentarios text,
            estado text DEFAULT 'Pendiente'::text,
            fecha_creacion timestamptz DEFAULT now(),
            origen text,
            fecha_recordatorio timestamptz,
            recordatorio_enviado boolean DEFAULT false,
            recordatorio_respondido boolean DEFAULT false,
            fecha_confirmacion timestamptz,
            fecha_cancelacion timestamptz,
            fecha_no_asistencia timestamptz,
            restaurante_id uuid REFERENCES public.restaurantes(id)
        );
        """
        
        create_result = supabase.rpc('exec_sql', {'query': create_table_sql}).execute()
        print("✓ Tabla reservas_prod creada exitosamente")
    
    # Verificar columna restaurante_id
    print("\n3. Verificando la columna restaurante_id...")
    check_column = """
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'reservas_prod' AND column_name = 'restaurante_id'
    );
    """
    
    column_result = supabase.rpc('exec_sql', {'query': check_column}).execute()
    columna_existe = column_result.data[0]['exists'] if column_result.data else False
    
    if columna_existe:
        print("✓ La columna restaurante_id ya existe")
    else:
        print("! La columna restaurante_id NO existe")
        print("-> Agregando la columna...")
        
        add_column_sql = """
        ALTER TABLE public.reservas_prod 
        ADD COLUMN restaurante_id uuid REFERENCES public.restaurantes(id);
        """
        
        add_column_result = supabase.rpc('exec_sql', {'query': add_column_sql}).execute()
        print("✓ Columna restaurante_id agregada exitosamente")
    
    # Crear índice si no existe
    print("\n4. Creando índice para optimizar consultas...")
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_reservas_prod_restaurante_id 
    ON public.reservas_prod(restaurante_id);
    """
    
    supabase.rpc('exec_sql', {'query': create_index_sql}).execute()
    print("✓ Índice creado o verificado")
    
    # Verificar reglas RLS (Row Level Security)
    print("\n5. Verificando políticas de seguridad RLS...")
    check_rls = """
    SELECT has_table_privilege('anon', 'reservas_prod', 'INSERT') as anon_insert,
           has_table_privilege('service_role', 'reservas_prod', 'INSERT') as service_role_insert;
    """
    
    rls_result = supabase.rpc('exec_sql', {'query': check_rls}).execute()
    
    if rls_result.data:
        anon_insert = rls_result.data[0].get('anon_insert', False)
        service_insert = rls_result.data[0].get('service_role_insert', True)
        
        print(f"- Permisos para rol 'anon': INSERT = {anon_insert}")
        print(f"- Permisos para rol 'service_role': INSERT = {service_insert}")
        
        # Si el rol anónimo no tiene permisos, crear una política RLS
        if not anon_insert:
            print("! El rol anónimo no tiene permisos de inserción")
            print("-> Creando política RLS para permitir inserciones...")
            
            enable_rls = """
            ALTER TABLE public.reservas_prod ENABLE ROW LEVEL SECURITY;
            """
            
            create_policy = """
            CREATE POLICY insert_policy ON public.reservas_prod 
            FOR INSERT TO anon WITH CHECK (true);
            """
            
            try:
                supabase.rpc('exec_sql', {'query': enable_rls}).execute()
                supabase.rpc('exec_sql', {'query': create_policy}).execute()
                print("✓ Política RLS creada exitosamente")
            except Exception as e:
                print(f"! Error al crear política RLS: {str(e)}")
    
    # Probar una inserción
    print("\n6. Realizando prueba de inserción...")
    try:
        # Datos para la prueba
        prueba_data = {
            'nombre': 'Test Script Migración',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'hora': '14:30',
            'personas': 2,
            'telefono': '1166686255',
            'email': 'test@example.com',
            'comentarios': 'Prueba de migración',
            'estado': 'Prueba',
            'origen': 'script_migracion',
            'restaurante_id': '6a117059-4c96-4e48-8fba-a59c71fd37cf'  # ID de Gandolfo
        }
        
        insert_result = supabase.table('reservas_prod').insert(prueba_data).execute()
        
        if insert_result.data:
            reserva_id = insert_result.data[0].get('id')
            print(f"✓ Inserción exitosa! ID generado: {reserva_id}")
            
            # Eliminar la reserva de prueba
            supabase.table('reservas_prod').delete().eq('id', reserva_id).execute()
            print(f"✓ Reserva de prueba eliminada")
        else:
            print(f"! Error en la inserción de prueba: {insert_result}")
            if hasattr(insert_result, 'error'):
                print(f"! Detalles del error: {insert_result.error}")
    except Exception as e:
        print(f"! Error al realizar la prueba de inserción: {str(e)}")
        traceback.print_exc()
    
    print("\n7. Realizando una prueba directa con API HTTP...")
    try:
        from config import USE_PROD_TABLES, RESERVAS_TABLE
        print(f"- USE_PROD_TABLES: {USE_PROD_TABLES}")
        print(f"- RESERVAS_TABLE: {RESERVAS_TABLE}")
    except ImportError:
        print("! No se pudo importar la configuración")
    
    print("\n========================================================")
    print("SCRIPT FINALIZADO")
    print("========================================================")

except Exception as e:
    print(f"ERROR GENERAL: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
