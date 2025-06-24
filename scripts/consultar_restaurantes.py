"""
Script para consultar restaurantes de Supabase sin modificar ningún dato.
Este script SOLO CONSULTA (SELECT) y no modifica nada en la base de datos.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Añadir la ruta raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cargar variables de entorno
load_dotenv()

# Importar el cliente de Supabase
from db.supabase_client import get_supabase_client

def consultar_restaurantes():
    """
    Función que SOLO consulta (SELECT) los restaurantes existentes en Supabase.
    No realiza modificaciones de ningún tipo.
    """
    print("Consultando restaurantes en Supabase...")
    
    try:
        # Obtener cliente de Supabase
        supabase = get_supabase_client()
        
        if not supabase:
            print("Error: No se pudo conectar a Supabase")
            return
        
        # Consultar todos los restaurantes (SELECT - solo lectura)
        print("Ejecutando consulta SELECT (solo lectura)...")
        response = supabase.table('restaurantes').select('*').execute()
        
        # Mostrar resultado
        if hasattr(response, 'data') and response.data:
            print(f"\nSe encontraron {len(response.data)} restaurantes:")
            for idx, restaurante in enumerate(response.data, 1):
                print(f"\n{idx}. ID: {restaurante.get('id')}")
                print(f"   Nombre: {restaurante.get('nombre', 'Sin nombre')}")
                print(f"   Dirección: {restaurante.get('direccion', 'Sin dirección')}")
                print(f"   Teléfono: {restaurante.get('telefono', 'Sin teléfono')}")
                print(f"   Activo: {restaurante.get('activo', False)}")
        else:
            print("No se encontraron restaurantes o la respuesta no tiene el formato esperado.")
            
        # Consultar usuarios para verificar relación con restaurantes
        print("\nConsultando usuarios (solo para verificar si existe relación con restaurantes)...")
        users_response = supabase.table('perfiles').select('*').execute()
        
        if hasattr(users_response, 'data') and users_response.data:
            print(f"\nSe encontraron {len(users_response.data)} perfiles de usuario:")
            for idx, user in enumerate(users_response.data, 1):
                print(f"\n{idx}. ID: {user.get('id')}")
                print(f"   Email: {user.get('email', 'Sin email')}")
                print(f"   Nombre: {user.get('nombre', 'Sin nombre')}")
                # Si existe campo de relación con restaurante, mostrarlo
                if 'restaurant_id' in user:
                    print(f"   Restaurant ID: {user.get('restaurant_id')}")
                
        else:
            print("No se encontró la tabla 'perfiles' o no hay usuarios registrados.")
            
            # Intentar otra tabla común de usuarios
            print("\nBuscando en tabla 'usuarios'...")
            users_alt_response = supabase.table('usuarios').select('*').execute()
            if hasattr(users_alt_response, 'data') and users_alt_response.data:
                print(f"\nSe encontraron {len(users_alt_response.data)} usuarios:")
                for idx, user in enumerate(users_alt_response.data, 1):
                    print(f"\n{idx}. ID: {user.get('id')}")
                    print(f"   Email: {user.get('email', 'Sin email')}")
                    print(f"   Nombre: {user.get('nombre', 'Sin nombre')}")
                    # Si existe campo de relación con restaurante, mostrarlo
                    if 'restaurant_id' in user:
                        print(f"   Restaurant ID: {user.get('restaurant_id')}")
                        
            else:
                print("No se encontró la tabla 'usuarios'.")
                
    except Exception as e:
        print(f"Error al consultar datos: {e}")
        
    print("\nConsulta finalizada. No se ha realizado ninguna modificación en la base de datos.")

if __name__ == "__main__":
    consultar_restaurantes()
