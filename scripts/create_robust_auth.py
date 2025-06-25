#!/usr/bin/env python3
"""
Script para crear una función de autenticación robusta que funcione en ambos entornos
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_robust_auth_function():
    """
    Crea una función que maneje ambos métodos de auth según disponibilidad
    """
    
    auth_function = '''
def robust_supabase_auth(supabase_client, email, password):
    """
    Función robusta que funciona tanto en local (0.7.1) como en producción
    Intenta primero sign_in, luego sign_in_with_password
    """
    try:
        # OPCIÓN 1: Método que funciona en local (0.7.1)
        if hasattr(supabase_client.auth, 'sign_in'):
            print("🔧 Usando sign_in (versión 0.7.1)")
            return supabase_client.auth.sign_in(
                email=email,
                password=password
            )
    except Exception as e:
        print(f"⚠️ sign_in falló: {str(e)}")
    
    try:
        # OPCIÓN 2: Método alternativo para versiones más nuevas
        if hasattr(supabase_client.auth, 'sign_in_with_password'):
            print("🔧 Usando sign_in_with_password (versión nueva)")
            return supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
    except Exception as e:
        print(f"⚠️ sign_in_with_password falló: {str(e)}")
    
    # OPCIÓN 3: Método para versiones muy antiguas
    try:
        if hasattr(supabase_client.auth, 'sign_in_with_email'):
            print("🔧 Usando sign_in_with_email (versión antigua)")
            return supabase_client.auth.sign_in_with_email(email, password)
    except Exception as e:
        print(f"⚠️ sign_in_with_email falló: {str(e)}")
    
    raise Exception("Ningún método de autenticación disponible")
'''
    
    print("🔧 FUNCIÓN DE AUTENTICACIÓN ROBUSTA:")
    print("="*60)
    print(auth_function)
    
    # Guardar en un archivo utilitario
    utils_path = Path(__file__).parent.parent / 'utils'
    utils_path.mkdir(exist_ok=True)
    
    auth_utils_path = utils_path / 'auth_utils.py'
    
    with open(auth_utils_path, 'w') as f:
        f.write(f'''"""
Utilidades de autenticación robustas para Supabase
Manejan diferencias entre versiones de la librería
"""

{auth_function}
''')
    
    print(f"✅ Función guardada en: {auth_utils_path}")
    print(f"\n📝 INSTRUCCIONES:")
    print(f"1. Importar: from utils.auth_utils import robust_supabase_auth")
    print(f"2. Usar: auth_result = robust_supabase_auth(supabase_client, email, password)")
    print(f"3. Esta función detectará automáticamente qué método usar")

if __name__ == "__main__":
    create_robust_auth_function()
