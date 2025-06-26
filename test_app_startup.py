#!/usr/bin/env python3
"""
Script para verificar que la aplicación puede arrancar correctamente
"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def test_app_startup():
    """Probar que la aplicación puede importarse y configurarse sin errores"""
    try:
        print("🔍 Verificando importación de módulos...")
        
        # Importar Flask y verificar configuración
        from flask import Flask
        print("✅ Flask importado correctamente")
        
        # Importar configuración
        import config
        print("✅ Configuración importada correctamente")
        
        # Verificar variables de entorno críticas
        if not config.SUPABASE_URL:
            raise Exception("SUPABASE_URL no configurada")
        if not config.SUPABASE_KEY:
            raise Exception("SUPABASE_KEY no configurada")
        if not config.SECRET_KEY:
            raise Exception("SECRET_KEY no configurada")
        
        print("✅ Variables de entorno críticas configuradas")
        
        # Importar cliente de Supabase
        from db.supabase_client import supabase
        print("✅ Cliente Supabase importado correctamente")
        
        # Importar todas las rutas
        from routes.admin_routes import admin_bp
        from routes.web_routes import web_bp
        from routes.api_routes import api_bp
        from routes.twilio_routes import twilio_bp
        from routes.webhook_routes import webhook_bp
        from routes.reminder_routes import reminder_bp
        print("✅ Todas las rutas importadas correctamente")
        
        # Crear aplicación Flask de prueba
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = config.SECRET_KEY
        test_app.config['DEBUG'] = False
        
        # Registrar blueprints
        test_app.register_blueprint(admin_bp)
        test_app.register_blueprint(web_bp)
        test_app.register_blueprint(api_bp)
        test_app.register_blueprint(twilio_bp)
        test_app.register_blueprint(webhook_bp)
        test_app.register_blueprint(reminder_bp)
        
        print("✅ Blueprints registrados correctamente")
        
        # Verificar que las rutas principales existen
        with test_app.test_client() as client:
            # Verificar que la ruta principal existe (puede devolver cualquier código)
            response = client.get('/')
            print(f"✅ Ruta principal responde (status: {response.status_code})")
            
            # Verificar que la ruta de login existe
            response = client.get('/admin/login')
            print(f"✅ Ruta de login responde (status: {response.status_code})")
            
            # Verificar que la ruta de config API existe
            response = client.get('/admin/api/config')
            print(f"✅ Ruta de config API responde (status: {response.status_code})")
        
        print("\n🎉 VERIFICACIÓN COMPLETA: La aplicación puede arrancar correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR en la verificación: {e}")
        return False

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)
