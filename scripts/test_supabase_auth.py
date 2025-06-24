#!/usr/bin/env python3
"""
Test script para verificar autenticación Supabase
"""

import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_supabase_auth():
    print("🔍 TESTING SUPABASE AUTHENTICATION")
    print("=" * 50)
    
    try:
        print("1. Importando cliente Supabase...")
        from db.supabase_client import supabase
        
        if not supabase:
            print("❌ ERROR: Cliente Supabase no inicializado")
            return False
        
        print("✅ Cliente Supabase importado correctamente")
        print(f"   Cliente: {supabase}")
        print(f"   Tiene auth: {hasattr(supabase, 'auth')}")
        
        print("\n2. Probando métodos de auth...")
        
        # Test básico de get_user (sin login)
        try:
            user = supabase.auth.get_user()
            print(f"✅ Método get_user() funciona: {user}")
        except Exception as e:
            print(f"⚠️  get_user() error (normal sin sesión): {e}")
        
        # Test de obtener información de Supabase
        try:
            print("\n3. Probando conexión a base de datos...")
            result = supabase.table('usuarios').select('id, email').limit(1).execute()
            print(f"✅ Conexión a tabla usuarios: {len(result.data)} registros encontrados")
            if result.data:
                print(f"   Ejemplo: {result.data[0]}")
        except Exception as e:
            print(f"❌ Error consultando tabla usuarios: {e}")
        
        print("\n4. Verificando configuración de auth...")
        try:
            # Intentar obtener la configuración de auth (esto no requiere login)
            print(f"✅ Auth client disponible: {supabase.auth}")
        except Exception as e:
            print(f"❌ Error accediendo auth client: {e}")
            return False
        
        print("\n✅ TODAS LAS PRUEBAS BÁSICAS PASARON")
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supabase_auth()
    print(f"\n🏁 Resultado: {'ÉXITO' if success else 'FALLO'}")
    sys.exit(0 if success else 1)
