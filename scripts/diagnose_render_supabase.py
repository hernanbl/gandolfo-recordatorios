#!/usr/bin/env python3
"""
Script para diagnosticar la versión de Supabase en Render vs Local
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def diagnose_supabase():
    """
    Diagnostica las diferencias de Supabase entre local y producción
    """
    print("🔍 DIAGNÓSTICO DE SUPABASE - LOCAL vs RENDER")
    print("="*60)
    
    try:
        import supabase
        print(f"✅ Supabase importado exitosamente")
        print(f"📦 Versión de supabase: {supabase.__version__}")
        print(f"📂 Ubicación del módulo: {supabase.__file__}")
        
        from supabase import create_client
        print(f"✅ create_client importado exitosamente")
        
        # Crear cliente de prueba
        try:
            client = create_client('https://test.supabase.co', 'test-key')
            print(f"✅ Cliente creado exitosamente")
            print(f"🔧 Tipo de cliente: {type(client)}")
            print(f"🔧 Tipo de auth: {type(client.auth)}")
            
            # Verificar métodos disponibles
            auth_methods = [m for m in dir(client.auth) if not m.startswith('_')]
            print(f"📋 Métodos disponibles en auth: {auth_methods}")
            
            # Verificar métodos específicos
            has_sign_in = hasattr(client.auth, 'sign_in')
            has_sign_in_with_password = hasattr(client.auth, 'sign_in_with_password')
            
            print(f"🔑 Tiene sign_in: {has_sign_in}")
            print(f"🔑 Tiene sign_in_with_password: {has_sign_in_with_password}")
            
            if has_sign_in:
                print(f"✅ El método sign_in está disponible - CÓDIGO ACTUAL DEBERÍA FUNCIONAR")
            else:
                print(f"❌ El método sign_in NO está disponible - NECESITA CORRECCIÓN")
                
            if has_sign_in_with_password:
                print(f"✅ El método sign_in_with_password está disponible como alternativa")
            else:
                print(f"❌ El método sign_in_with_password tampoco está disponible")
            
        except Exception as e:
            print(f"❌ Error creando cliente: {str(e)}")
            
    except ImportError as e:
        print(f"❌ Error importando supabase: {str(e)}")
        
    # Verificar variables de entorno
    print(f"\n🌍 VARIABLES DE ENTORNO:")
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'SET' if supabase_key else 'NOT SET'}")
    
    if supabase_url:
        print(f"URL: {supabase_url}")
        
    # Verificar Python y pip
    print(f"\n🐍 INFORMACIÓN DEL ENTORNO:")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    try:
        import pip
        print(f"Pip version: {pip.__version__}")
    except:
        print("Pip version: No disponible")
        
    # Verificar requirements.txt
    requirements_path = Path(__file__).parent.parent / 'requirements.txt'
    if requirements_path.exists():
        print(f"\n📄 REQUIREMENTS.TXT:")
        with open(requirements_path, 'r') as f:
            for line in f:
                if 'supabase' in line.lower():
                    print(f"  {line.strip()}")
    
    print(f"\n🚀 RECOMENDACIONES:")
    print(f"1. En Render, verificar que se esté instalando supabase==0.7.1")
    print(f"2. En Render, limpiar caché de pip si es necesario")
    print(f"3. Verificar que las variables de entorno estén configuradas")
    print(f"4. Si el método sign_in no está disponible, usar sign_in_with_password")

if __name__ == "__main__":
    diagnose_supabase()
