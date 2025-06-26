#!/usr/bin/env python3
"""
Verificación final post-deploy - Confirmar que todo funciona en producción
"""

import requests
import time
import json
from datetime import datetime

def check_production_status():
    """Verificar que la aplicación está funcionando en producción"""
    
    print("🚀 VERIFICACIÓN FINAL POST-DEPLOY")
    print("=" * 50)
    
    base_url = "https://gandolfo.app"
    
    # Endpoints críticos a verificar
    critical_endpoints = {
        "/": "Página principal",
        "/admin/login": "Login de administración", 
        "/admin/api/config": "Configuración Supabase",
        "/admin/auth/callback": "Callback OAuth"
    }
    
    results = {}
    all_ok = True
    
    for endpoint, description in critical_endpoints.items():
        print(f"\n🔍 Verificando {description}...")
        url = base_url + endpoint
        
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ {status} - OK")
                if endpoint == "/admin/api/config":
                    try:
                        config = response.json()
                        has_supabase_url = bool(config.get('supabase_url'))
                        has_supabase_key = bool(config.get('supabase_key'))
                        print(f"   📋 Supabase URL: {'✅' if has_supabase_url else '❌'}")
                        print(f"   🔑 Supabase Key: {'✅' if has_supabase_key else '❌'}")
                        
                        if not (has_supabase_url and has_supabase_key):
                            all_ok = False
                    except:
                        print("   ⚠️ No se pudo parsear config JSON")
                        all_ok = False
                        
            elif status in [301, 302, 307, 308]:
                print(f"   🔄 {status} - Redirect (normal)")
            else:
                print(f"   ❌ {status} - Error")
                all_ok = False
                
            results[endpoint] = status
            
        except Exception as e:
            print(f"   💥 Error: {e}")
            results[endpoint] = f"ERROR: {e}"
            all_ok = False
    
    # Verificación especial del flujo OAuth
    print(f"\n🔐 Verificando flujo OAuth...")
    oauth_url = f"{base_url}/admin/api/config"
    
    try:
        response = requests.get(oauth_url, timeout=10)
        if response.status_code == 200:
            config = response.json()
            supabase_url = config.get('supabase_url', '')
            
            if 'qhfivsunmqbifotjpqdw.supabase.co' in supabase_url:
                print("   ✅ Supabase URL correcta")
            else:
                print("   ❌ Supabase URL incorrecta")
                all_ok = False
        else:
            print("   ❌ No se pudo obtener configuración")
            all_ok = False
            
    except Exception as e:
        print(f"   💥 Error verificando OAuth: {e}")
        all_ok = False
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    
    if all_ok:
        print("🎉 ¡DEPLOY EXITOSO!")
        print("✅ Todos los endpoints funcionan correctamente")
        print("✅ Configuración de Supabase OK")
        print("✅ OAuth debería funcionar correctamente")
        print("\n🧪 PRUEBA MANUAL RECOMENDADA:")
        print("1. Ir a https://gandolfo.app")
        print("2. Hacer clic en 'Continuar con Google'")
        print("3. Completar autenticación con Google")
        print("4. Verificar que llega al dashboard")
        print("5. Probar también login con email/password")
    else:
        print("⚠️ HAY PROBLEMAS EN EL DEPLOY")
        print("❌ Algunos endpoints no funcionan correctamente")
        print("🔧 Revisar logs de Render para más detalles")
    
    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": timestamp,
        "all_endpoints_ok": all_ok,
        "endpoint_results": results,
        "deploy_status": "SUCCESS" if all_ok else "ISSUES"
    }
    
    filename = f"deploy_verification_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Reporte guardado en: {filename}")
    
    return all_ok

if __name__ == "__main__":
    success = check_production_status()
    exit(0 if success else 1)
