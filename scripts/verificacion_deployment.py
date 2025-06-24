#!/usr/bin/env python3
"""
Script de verificación final antes del deployment
Verifica que todos los archivos y configuraciones estén listos
"""

import os
import sys
import json
from datetime import datetime

def verificar_archivo(ruta, descripcion):
    """Verifica que un archivo existe"""
    if os.path.exists(ruta):
        print(f"✅ {descripcion}: {ruta}")
        return True
    else:
        print(f"❌ {descripcion}: {ruta} - NO EXISTE")
        return False

def verificar_contenido_archivo(ruta, contenido_requerido, descripcion):
    """Verifica que un archivo contiene cierto contenido"""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if contenido_requerido in contenido:
                print(f"✅ {descripcion}")
                return True
            else:
                print(f"❌ {descripcion} - Contenido no encontrado")
                return False
    except Exception as e:
        print(f"❌ {descripcion} - Error: {str(e)}")
        return False

def main():
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA DE RECORDATORIOS")
    print("=" * 60)
    
    todos_ok = True
    
    # Verificar archivos principales
    print("\n📁 ARCHIVOS PRINCIPALES:")
    archivos_principales = [
        ("render.yaml", "Configuración de Render"),
        ("requirements.txt", "Dependencias Python"),
        ("config.py", "Configuración del sistema"),
        ("app.py", "Aplicación principal"),
        ("scripts/send_reminders.py", "Script principal de recordatorios"),
        ("scripts/check_reminder_system.py", "Script de verificación"),
        ("services/recordatorio_service.py", "Servicio de recordatorios"),
        ("INSTRUCCIONES_DEPLOYMENT_COMPLETAS.md", "Instrucciones de deployment")
    ]
    
    for archivo, desc in archivos_principales:
        if not verificar_archivo(archivo, desc):
            todos_ok = False
    
    # Verificar contenido crítico
    print("\n🔧 CONTENIDO CRÍTICO:")
    verificaciones_contenido = [
        ("render.yaml", "cron", "Configuración de cron jobs"),
        ("render.yaml", "America/Argentina/Buenos_Aires", "Zona horaria argentina"),
        ("requirements.txt", "pytz", "Dependencia pytz para zona horaria"),
        ("config.py", "reservas_prod", "Tabla de producción"),
        ("services/recordatorio_service.py", "nombre_cliente", "Columna correcta de nombre"),
        ("scripts/send_reminders.py", "ARGENTINA_TZ", "Zona horaria en script principal")
    ]
    
    for archivo, contenido, desc in verificaciones_contenido:
        if not verificar_contenido_archivo(archivo, contenido, desc):
            todos_ok = False
    
    # Verificar estructura de directorios
    print("\n📂 ESTRUCTURA DE DIRECTORIOS:")
    directorios = [
        "scripts/",
        "services/", 
        "db/",
        "utils/",
        "routes/",
        "logs/"
    ]
    
    for directorio in directorios:
        if not verificar_archivo(directorio, f"Directorio {directorio}"):
            todos_ok = False
    
    # Verificar Git
    print("\n📦 REPOSITORIO GIT:")
    if os.path.exists(".git"):
        print("✅ Repositorio Git inicializado")
        
        # Verificar que no hay cambios pendientes
        import subprocess
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            if result.stdout.strip() == "":
                print("✅ No hay cambios pendientes en Git")
            else:
                print("⚠️  Hay cambios pendientes en Git:")
                print(result.stdout)
        except Exception as e:
            print(f"⚠️  No se pudo verificar estado de Git: {e}")
    else:
        print("❌ Repositorio Git no inicializado")
        todos_ok = False
    
    # Resumen final
    print("\n" + "=" * 60)
    if todos_ok:
        print("🎉 ¡SISTEMA 100% LISTO PARA DEPLOYMENT!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Crear repositorio en GitHub: gandolfo-recordatorios")
        print("2. git remote add origin https://github.com/hernanbl/gandolfo-recordatorios.git")
        print("3. git push -u origin main")
        print("4. Configurar Blueprint en Render")
        print("5. Agregar variables de entorno")
        print("\n📖 Ver: INSTRUCCIONES_DEPLOYMENT_COMPLETAS.md")
    else:
        print("❌ HAY PROBLEMAS QUE RESOLVER ANTES DEL DEPLOYMENT")
        return 1
    
    # Crear log de verificación
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "verificacion_completa": todos_ok,
        "sistema": "recordatorios_automaticos",
        "version": "1.0.0",
        "estado": "listo_para_deployment" if todos_ok else "requiere_atencion"
    }
    
    with open("logs/verificacion_deployment.json", "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\n📊 Log guardado en: logs/verificacion_deployment.json")
    
    return 0 if todos_ok else 1

if __name__ == "__main__":
    sys.exit(main())
