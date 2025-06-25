#!/usr/bin/env python3
"""
Script para probar login en producción
Usar: python scripts/test_login_production.py email password
"""

import sys
import os
from dotenv import load_dotenv

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")

def test_login(email, password):
    print(f"🔐 PROBANDO LOGIN EN PRODUCCIÓN")
    print(f"Email: {email}")
    print("=" * 50)
    
    try:
        print("1. Verificando variables de entorno...")
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        print(f"SUPABASE_URL: {'✅ SET' if supabase_url else '❌ NOT SET'}")
        print(f"SUPABASE_KEY: {'✅ SET' if supabase_key else '❌ NOT SET'}")
        
        if not supabase_url or not supabase_key:
            print("❌ ERROR: Variables de entorno faltantes")
            return False
        
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}...")
        
        print("\n2. Importando cliente Supabase...")
        try:
            from db.supabase_client import supabase
            if not supabase:
                print("❌ Cliente desde db.supabase_client es None")
                # Intentar crear cliente directamente
                print("   Intentando crear cliente directamente...")
                from supabase import create_client
                supabase = create_client(supabase_url, supabase_key)
            
            print(f"✅ Cliente disponible: {supabase}")
            print(f"   Tiene auth: {hasattr(supabase, 'auth')}")
        except Exception as e:
            print(f"❌ Error importando cliente: {e}")
            return False
        
        print("\n3. Probando autenticación...")
        try:
            auth_result = supabase.auth.sign_in(
                email=email,
                password=password
            )
            
            print(f"Auth result: {auth_result}")
            print(f"Auth result type: {type(auth_result)}")
            
            # Verificar si tenemos un usuario
            if hasattr(auth_result, 'user') and auth_result.user:
                print(f"✅ LOGIN EXITOSO!")
                print(f"   User ID: {auth_result.user.id}")
                print(f"   Email: {auth_result.user.email}")
                user_id = auth_result.user.id
                user_email = auth_result.user.email
            elif hasattr(auth_result, 'id'):
                # Tal vez el resultado es el usuario directamente
                print(f"✅ LOGIN EXITOSO (usuario directo)!")
                print(f"   User ID: {auth_result.id}")
                print(f"   Email: {getattr(auth_result, 'email', 'N/A')}")
                user_id = auth_result.id
                user_email = getattr(auth_result, 'email', email)
            else:
                print(f"⚠️  Auth result no contiene usuario esperado")
                print(f"   Attributes: {dir(auth_result)}")
                return False
                
                # Buscar en tabla usuarios
                print("\n4. Buscando en tabla usuarios...")
                try:
                    result = supabase.table('usuarios').select('*').eq('auth_user_id', user_id).execute()
                    if result.data:
                        user = result.data[0]
                        print(f"✅ Usuario encontrado en tabla:")
                        print(f"   ID: {user['id']}")
                        print(f"   Email: {user['email']}")
                        print(f"   Role: {user.get('role', 'N/A')}")
                        print(f"   Activo: {user.get('activo', 'N/A')}")
                        return True
                    else:
                        print(f"⚠️  Usuario autenticado pero no encontrado en tabla usuarios")
                        return False
                except Exception as e:
                    print(f"❌ Error buscando en tabla usuarios: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ ERROR EN AUTENTICACIÓN: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python scripts/test_login_production.py <email> <password>")
        print("Ejemplo: python scripts/test_login_production.py usuario@ejemplo.com mipassword")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    success = test_login(email, password)
    print(f"\n🏁 Resultado: {'✅ ÉXITO' if success else '❌ FALLO'}")
    sys.exit(0 if success else 1)
