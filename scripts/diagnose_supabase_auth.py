#!/usr/bin/env python3
"""
Script para diagnosticar problemas de autenticación con Supabase
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("🔍 DIAGNÓSTICO DE SUPABASE AUTH")
    print("=" * 50)
    
    # Cargar variables de entorno
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    print(f"📁 Archivo .env: {dotenv_path}")
    print(f"📁 Existe .env: {os.path.exists(dotenv_path)}")
    print()
    
    # Verificar variables de entorno
    print("🔐 VARIABLES DE ENTORNO:")
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {'✅ SET' if supabase_url else '❌ NOT SET'}")
    if supabase_url:
        print(f"  URL: {supabase_url}")
    
    print(f"SUPABASE_KEY: {'✅ SET' if supabase_key else '❌ NOT SET'}")
    if supabase_key:
        print(f"  Key (first 20 chars): {supabase_key[:20]}...")
    print()
    
    # Verificar importación de supabase
    print("📦 IMPORTACIÓN DE SUPABASE:")
    try:
        from supabase import create_client
        print("✅ Módulo supabase importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando supabase: {e}")
        return
    print()
    
    # Verificar inicialización del cliente
    print("🔧 INICIALIZACIÓN DEL CLIENTE:")
    if not supabase_url or not supabase_key:
        print("❌ No se puede inicializar: faltan credenciales")
        return
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Cliente Supabase creado correctamente")
        print(f"  Cliente: {client}")
        print(f"  Tiene auth: {hasattr(client, 'auth')}")
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        return
    print()
    
    # Verificar importación desde db.supabase_client
    print("🔌 IMPORTACIÓN DESDE DB.SUPABASE_CLIENT:")
    try:
        from db.supabase_client import supabase
        print(f"✅ Importado correctamente: {supabase}")
        if supabase:
            print(f"  Tiene auth: {hasattr(supabase, 'auth')}")
        else:
            print("❌ Cliente es None")
    except Exception as e:
        print(f"❌ Error importando: {e}")
    print()
    
    # Test de autenticación básica
    print("🔑 TEST DE AUTENTICACIÓN:")
    try:
        if supabase and hasattr(supabase, 'auth'):
            # Intentar obtener información del usuario actual (sin login)
            user = supabase.auth.get_user()
            print(f"✅ Auth funciona, usuario actual: {user}")
        else:
            print("❌ No se puede probar auth: cliente no disponible")
    except Exception as e:
        print(f"⚠️  Error en test de auth (normal si no hay sesión): {e}")
    
    print("\n🏁 DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    main()
