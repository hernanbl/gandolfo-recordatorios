#!/usr/bin/env python3
"""
Script para verificar que todas las variables de entorno necesarias estén configuradas
Ideal para ejecutar en Render antes del cron job principal
"""
import os
import sys
from dotenv import load_dotenv

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno requeridas estén presentes"""
    
    # Cargar variables de entorno si existe archivo .env
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Variables cargadas desde: {env_file}")
    else:
        print("ℹ️  No se encontró archivo .env, usando variables del sistema")
    
    # Lista de variables requeridas
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_NUMBER'
    ]
    
    # Variables opcionales pero útiles
    optional_vars = [
        'TZ',
        'USE_PROD_TABLES',
        'DEFAULT_RESTAURANT_NAME',
        'TEST_MODE'
    ]
    
    print("\n=== VERIFICACIÓN DE VARIABLES DE ENTORNO ===\n")
    
    # Verificar variables requeridas
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mostrar solo los primeros y últimos caracteres para seguridad
            if len(value) > 10:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = f"{value[:2]}...{value[-2:]}"
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
            missing_vars.append(var)
    
    print()
    
    # Verificar variables opcionales
    print("📋 Variables opcionales:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️  {var}: No configurada (opcional)")
    
    print()
    
    # Resultado final
    if missing_vars:
        print(f"❌ FALTAN {len(missing_vars)} VARIABLES REQUERIDAS:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n🔧 SOLUCIÓN:")
        print("1. Ve a tu dashboard de Render")
        print("2. Selecciona tu servicio (web app o cron job)")
        print("3. Ve a 'Environment' en el menú lateral")
        print("4. Agrega las variables faltantes")
        print("5. Guarda los cambios")
        print("\n📖 Ver documentación completa en: VARIABLES_ENTORNO_RENDER_SAFE.md")
        return False
    else:
        print("🎉 ¡TODAS LAS VARIABLES REQUERIDAS ESTÁN CONFIGURADAS!")
        print("✅ El sistema de recordatorios debería funcionar correctamente")
        return True

def mostrar_info_sistema():
    """Muestra información útil del sistema"""
    print("\n=== INFORMACIÓN DEL SISTEMA ===")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📁 Directorio del script: {os.path.dirname(__file__)}")
    print(f"🐍 Python: {sys.version}")
    print(f"🖥️  Plataforma: {sys.platform}")
    
    # Verificar si estamos en Render
    if os.getenv('RENDER'):
        print("🚀 Ejecutándose en Render")
        print(f"📦 Servicio: {os.getenv('RENDER_SERVICE_NAME', 'No identificado')}")
    else:
        print("🏠 Ejecutándose en entorno local")

if __name__ == "__main__":
    print("🔍 VERIFICADOR DE VARIABLES DE ENTORNO")
    print("=" * 50)
    
    # Mostrar información del sistema
    mostrar_info_sistema()
    
    # Verificar variables
    success = verificar_variables_entorno()
    
    # Exit code para scripts automatizados
    sys.exit(0 if success else 1)
