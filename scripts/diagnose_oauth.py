#!/usr/bin/env python3
"""
Script para diagnosticar problemas de OAuth con Google en producción
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_oauth_config():
    """
    Verifica la configuración necesaria para OAuth
    """
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN OAUTH")
    print("="*50)
    
    # Variables de entorno necesarias
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SECRET_KEY'
    ]
    
    print("\n📋 Variables de entorno:")
    all_vars_present = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if var == 'SECRET_KEY':
                print(f"  ✅ {var}: {'*' * len(value[:8])}...")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NO CONFIGURADA")
            all_vars_present = False
    
    if not all_vars_present:
        print("\n⚠️ PROBLEMA: Faltan variables de entorno necesarias")
        return False
    
    # URLs esperadas en producción
    production_urls = {
        'app_url': 'https://gandolfo.app',
        'callback_url': 'https://gandolfo.app/admin/auth/callback',
        'site_url': 'https://gandolfo.app'
    }
    
    print(f"\n🌍 URLs de producción esperadas:")
    for key, url in production_urls.items():
        print(f"  • {key}: {url}")
    
    # Verificar Supabase URL
    supabase_url = os.environ.get('SUPABASE_URL', '')
    print(f"\n🔗 Supabase Project URL: {supabase_url}")
    
    if 'supabase.co' in supabase_url:
        project_id = supabase_url.split('//')[1].split('.')[0]
        print(f"  📍 Project ID: {project_id}")
        dashboard_url = f"https://supabase.com/dashboard/project/{project_id}/auth/url-configuration"
        print(f"  🎛️ Dashboard de configuración: {dashboard_url}")
        
        print(f"\n📝 CONFIGURACIÓN REQUERIDA EN SUPABASE DASHBOARD:")
        print(f"  1. Site URL: https://gandolfo.app")
        print(f"  2. Redirect URLs:")
        print(f"     - https://gandolfo.app/admin/auth/callback")
        print(f"     - https://gandolfo.app/")
        print(f"     - http://localhost:5000/admin/auth/callback (para desarrollo)")
        print(f"  3. Configuración OAuth Google:")
        print(f"     - Autorized redirect URIs en Google Console:")
        print(f"       * https://gandolfo.app/admin/auth/callback")
        print(f"       * {supabase_url}/auth/v1/callback")
    
    return True

def check_render_deployment():
    """
    Información específica para el deployment en Render
    """
    print(f"\n🚀 INFORMACIÓN PARA RENDER:")
    print(f"  • Domain: gandolfo.app")
    print(f"  • Asegúrate de que las variables de entorno estén configuradas en Render")
    print(f"  • Verifica que el dominio gandolfo.app apunte correctamente a Render")
    
    print(f"\n🔧 COMANDOS PARA VERIFICAR EN RENDER:")
    print(f"  1. Verificar variables de entorno en Render Dashboard")
    print(f"  2. Verificar logs de deployment")
    print(f"  3. Probar login desde https://gandolfo.app/admin/login")

def main():
    check_oauth_config()
    check_render_deployment()
    
    print(f"\n✅ PASOS SIGUIENTES:")
    print(f"  1. Verificar configuración en Supabase Dashboard")
    print(f"  2. Actualizar redirect URLs si es necesario")
    print(f"  3. Probar login en producción")
    print(f"  4. Revisar logs de Render para errores específicos")

if __name__ == "__main__":
    main()
