#!/usr/bin/env python3
"""
Script para probar el login después de las correcciones aplicadas
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.supabase_client import supabase_client

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_corrected_login(email, password):
    """
    Prueba el login con la corrección aplicada
    """
    print("🧪 TESTING LOGIN CON CORRECCIÓN APLICADA")
    print("="*50)
    
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {'*' * len(password)}")
    
    if not supabase_client:
        print("❌ Cliente Supabase no disponible")
        return False
    
    print(f"\n✅ Cliente Supabase disponible")
    print(f"📍 Cliente type: {type(supabase_client)}")
    print(f"🔍 Auth client: {hasattr(supabase_client, 'auth')}")
    
    if hasattr(supabase_client, 'auth'):
        auth_client = supabase_client.auth
        print(f"🔍 Auth client type: {type(auth_client)}")
        print(f"🔍 Tiene sign_in: {hasattr(auth_client, 'sign_in')}")
        print(f"🔍 Tiene sign_in_with_password: {hasattr(auth_client, 'sign_in_with_password')}")
        
        # Listar todos los métodos disponibles
        methods = [method for method in dir(auth_client) if not method.startswith('_')]
        print(f"🔍 Métodos disponibles: {methods[:10]}...")  # Solo primeros 10
    
    print(f"\n🔄 Intentando login con sign_in_with_password...")
    
    try:
        # Usar el método corregido
        auth_result = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        print(f"✅ Login exitoso!")
        print(f"📊 Resultado type: {type(auth_result)}")
        
        if hasattr(auth_result, 'user') and auth_result.user:
            user = auth_result.user
            print(f"👤 Usuario autenticado:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Email verified: {getattr(user, 'email_confirmed_at', 'N/A')}")
        
        if hasattr(auth_result, 'session') and auth_result.session:
            session = auth_result.session
            print(f"🔐 Sesión creada:")
            print(f"   Access token: {session.access_token[:20]}...")
            print(f"   Expires: {session.expires_at}")
        
        return True
        
    except AttributeError as e:
        print(f"❌ Error de atributo: {str(e)}")
        print(f"🔍 Esto indica que el método sign_in_with_password no existe")
        
        # Intentar con el método anterior
        print(f"\n🔄 Intentando con sign_in...")
        try:
            auth_result = supabase_client.auth.sign_in(
                email=email,
                password=password
            )
            print(f"✅ Login con sign_in exitoso!")
            return True
        except Exception as e2:
            print(f"❌ Error con sign_in también: {str(e2)}")
            return False
    
    except Exception as e:
        print(f"❌ Error durante login: {str(e)}")
        logger.error(f"Error en login: {str(e)}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/test_corrected_login.py <email> <password>")
        print("Ejemplo: python scripts/test_corrected_login.py resto@vivacom.com.ar mipassword")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    success = test_corrected_login(email, password)
    
    if success:
        print(f"\n🎉 LOGIN EXITOSO")
        print(f"✅ El método de autenticación funciona correctamente")
        print(f"🚀 Listo para deployment en producción")
    else:
        print(f"\n❌ LOGIN FALLÓ")
        print(f"🔧 Revisar configuración o método de autenticación")

if __name__ == "__main__":
    main()
