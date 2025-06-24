#!/usr/bin/env python3
"""
Script de verificación final antes del deployment
Confirma que todo el sistema de recordatorios esté correctamente configurado
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add the project root to the Python path
app_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv

# Cargar variables de entorno
env_file = os.path.join(app_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def verificar_configuracion():
    """Verifica la configuración del sistema"""
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA DE RECORDATORIOS")
    print("=" * 60)
    
    errores = []
    warnings = []
    
    # 1. Verificar archivos críticos
    archivos_criticos = [
        'scripts/send_reminders.py',
        'scripts/check_reminder_system.py',
        'services/recordatorio_service.py',
        'render.yaml',
        'config.py',
        'requirements.txt'
    ]
    
    print("\n1️⃣ VERIFICANDO ARCHIVOS CRÍTICOS:")
    for archivo in archivos_criticos:
        ruta_completa = os.path.join(app_dir, archivo)
        if os.path.exists(ruta_completa):
            print(f"   ✅ {archivo}")
        else:
            errores.append(f"Archivo faltante: {archivo}")
            print(f"   ❌ {archivo}")
    
    # 2. Verificar configuración
    print("\n2️⃣ VERIFICANDO CONFIGURACIÓN:")
    
    try:
        from config import RESERVAS_TABLE, USE_PROD_TABLES, DEFAULT_RESTAURANT_NAME
        print(f"   ✅ USE_PROD_TABLES: {USE_PROD_TABLES}")
        print(f"   ✅ RESERVAS_TABLE: {RESERVAS_TABLE}")
        print(f"   ✅ DEFAULT_RESTAURANT_NAME: {DEFAULT_RESTAURANT_NAME}")
        
        if RESERVAS_TABLE != 'reservas_prod':
            warnings.append(f"RESERVAS_TABLE es '{RESERVAS_TABLE}' pero debería ser 'reservas_prod'")
            
    except Exception as e:
        errores.append(f"Error importando configuración: {str(e)}")
    
    # 3. Verificar variables de entorno críticas
    print("\n3️⃣ VERIFICANDO VARIABLES DE ENTORNO:")
    
    variables_criticas = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_NUMBER'
    ]
    
    for var in variables_criticas:
        if os.getenv(var):
            print(f"   ✅ {var}: configurado")
        else:
            errores.append(f"Variable de entorno faltante: {var}")
            print(f"   ❌ {var}: NO configurado")
    
    # 4. Verificar render.yaml
    print("\n4️⃣ VERIFICANDO RENDER.YAML:")
    
    render_file = os.path.join(app_dir, 'render.yaml')
    if os.path.exists(render_file):
        with open(render_file, 'r') as f:
            render_content = f.read()
            
        # Verificar servicios requeridos
        servicios_requeridos = [
            'daily-system-check',
            'daily-reminders-morning', 
            'daily-reminders-backup'
        ]
        
        for servicio in servicios_requeridos:
            if servicio in render_content:
                print(f"   ✅ Servicio {servicio}: configurado")
            else:
                errores.append(f"Servicio faltante en render.yaml: {servicio}")
                print(f"   ❌ Servicio {servicio}: NO configurado")
        
        # Verificar horarios de cron
        horarios_esperados = ['0 12 * * *', '0 13 * * *', '0 17 * * *']
        for horario in horarios_esperados:
            if horario in render_content:
                print(f"   ✅ Horario {horario}: configurado")
            else:
                warnings.append(f"Horario {horario} no encontrado en render.yaml")
                
        # Verificar variable USE_PROD_TABLES
        if 'USE_PROD_TABLES' in render_content:
            print(f"   ✅ USE_PROD_TABLES: configurado en render.yaml")
        else:
            errores.append("Variable USE_PROD_TABLES faltante en render.yaml")
            
    else:
        errores.append("Archivo render.yaml no encontrado")
    
    # 5. Verificar requirements.txt
    print("\n5️⃣ VERIFICANDO REQUIREMENTS.TXT:")
    
    req_file = os.path.join(app_dir, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            req_content = f.read()
            
        dependencias_criticas = ['pytz', 'twilio', 'supabase', 'python-dotenv']
        for dep in dependencias_criticas:
            if dep in req_content:
                print(f"   ✅ {dep}: incluido")
            else:
                errores.append(f"Dependencia faltante en requirements.txt: {dep}")
                print(f"   ❌ {dep}: NO incluido")
    else:
        errores.append("Archivo requirements.txt no encontrado")
    
    # 6. Verificar lógica de fecha
    print("\n6️⃣ VERIFICANDO LÓGICA DE FECHAS:")
    
    try:
        ahora_argentina = datetime.now(ARGENTINA_TZ)
        manana_argentina = ahora_argentina + timedelta(days=1)
        
        print(f"   ✅ Zona horaria Argentina: {ahora_argentina.strftime('%Z')}")
        print(f"   ✅ Fecha actual: {ahora_argentina.strftime('%d/%m/%Y %H:%M')}")
        print(f"   ✅ Fecha de mañana: {manana_argentina.strftime('%d/%m/%Y')}")
        print(f"   ✅ Formato BD: {manana_argentina.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        errores.append(f"Error en lógica de fechas: {str(e)}")
    
    # 7. Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL")
    print("=" * 60)
    
    if errores:
        print(f"❌ ERRORES CRÍTICOS ENCONTRADOS ({len(errores)}):")
        for error in errores:
            print(f"   • {error}")
        print("\n🚨 EL SISTEMA NO ESTÁ LISTO PARA DEPLOYMENT")
        return False
    
    if warnings:
        print(f"⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errores:
        print("🎉 SISTEMA COMPLETAMENTE LISTO PARA DEPLOYMENT")
        print("\n📋 Pasos siguientes:")
        print("   1. git add .")
        print("   2. git commit -m 'Sistema recordatorios final - tabla reservas_prod'")
        print("   3. git push origin main")
        print("\n⏰ Horarios de ejecución en Render:")
        print("   • 09:00 AM Argentina → Verificación del sistema")
        print("   • 10:00 AM Argentina → Envío principal de recordatorios")
        print("   • 14:00 PM Argentina → Envío de respaldo")
        print("\n📱 Tabla utilizada: reservas_prod")
        print("📱 Columna de nombre: nombre_cliente")
        return True
    
    return False

if __name__ == "__main__":
    success = verificar_configuracion()
    sys.exit(0 if success else 1)
