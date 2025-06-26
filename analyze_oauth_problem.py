#!/usr/bin/env python3
"""
ANÁLISIS DEL PROBLEMA OAUTH - LOCAL vs PRODUCCIÓN
"""

print("""
🔍 ANÁLISIS LÓGICO DEL PROBLEMA OAUTH

📋 DATOS QUE TENEMOS:
✅ Local (localhost:5000) + Google OAuth = FUNCIONA PERFECTO
❌ Producción (gandolfo.app) + Google OAuth = Redirige a localhost:5000

🤔 CONCLUSIÓN LÓGICA:
Si ambos usan la MISMA configuración de Supabase, entonces:
- ❌ NO es problema de Supabase Dashboard
- ❌ NO es problema de Site URL en Supabase  
- ❌ NO es problema de Redirect URLs en Supabase
- ✅ ES un problema de CÓDIGO o DETECCIÓN DE ENTORNO

🔍 POSIBLES CAUSAS:

1️⃣ DETECCIÓN DE ENTORNO INCORRECTA:
   • El código frontend detecta MAL si está en producción
   • Configuración de redirectUrl incorrecta en el JavaScript

2️⃣ CACHÉ DEL NAVEGADOR:
   • El navegador tiene guardada la URL localhost
   • Supabase tiene cached la configuración de localhost

3️⃣ CONFIGURACIÓN DIFERENTE ENTRE LOCAL Y PRODUCCIÓN:
   • Variables de entorno diferentes
   • Configuración de Supabase diferente

4️⃣ PROBLEMA EN EL FRONTEND:
   • JavaScript no detecta correctamente gandolfo.app
   • redirectUrl se configura mal en producción

""")

# Verificar configuración de producción
try:
    import requests
    
    print("🔍 VERIFICANDO CONFIGURACIÓN DE PRODUCCIÓN:")
    response = requests.get('https://gandolfo.app/admin/api/config', timeout=5)
    
    if response.status_code == 200:
        config = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📋 Supabase URL: {config.get('supabase_url', 'No disponible')}")
        print(f"   🔑 Supabase Key presente: {'Sí' if config.get('supabase_key') else 'No'}")
        
        # Comparar con configuración local
        import os
        from pathlib import Path
        
        # Intentar cargar .env local
        env_file = Path('/Volumes/AUDIO/gandolfo-recordatorios/.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
                if 'SUPABASE_URL=' in env_content:
                    local_url = [line.split('=', 1)[1].strip().strip('"') 
                                for line in env_content.split('\n') 
                                if line.startswith('SUPABASE_URL=')][0]
                    
                    prod_url = config.get('supabase_url')
                    print(f"\n🔄 COMPARACIÓN:")
                    print(f"   Local URL:  {local_url}")
                    print(f"   Prod URL:   {prod_url}")
                    
                    if local_url == prod_url:
                        print("   ✅ URLs coinciden - NO es problema de configuración")
                        print("   🎯 EL PROBLEMA ESTÁ EN EL FRONTEND/JAVASCRIPT")
                    else:
                        print("   ❌ URLs diferentes - PROBLEMA DE CONFIGURACIÓN")
        
    else:
        print(f"   ❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"   💥 Error verificando: {e}")

print("\n" + "="*70)
print("🎯 PRÓXIMA ACCIÓN RECOMENDADA:")
print("="*70)
print("1. Verificar el JavaScript de detección de entorno en login.html")
print("2. Agregar más logging al frontend para ver qué URL se está usando")
print("3. Verificar si hay diferencias en window.location entre local y prod")
print("="*70)
