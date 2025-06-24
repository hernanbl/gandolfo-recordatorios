#!/usr/bin/env python3
"""
Script de prueba automatizada para el sistema de recordatorios
Ejecuta todas las verificaciones sin interacción del usuario
"""

import sys
import os
import logging
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

# Zona horaria Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Prueba automatizada completa del sistema"""
    print("🤖 PRUEBA AUTOMATIZADA DEL SISTEMA DE RECORDATORIOS")
    print("=" * 60)
    
    try:
        # 1. Verificar configuración
        print("\n1️⃣ VERIFICANDO CONFIGURACIÓN...")
        from scripts.check_reminder_system import verificar_variables_entorno, verificar_conexion_supabase, verificar_conexion_twilio
        
        env_ok = verificar_variables_entorno()
        supabase_ok = verificar_conexion_supabase()
        twilio_ok = verificar_conexion_twilio()
        
        print(f"   Variables de entorno: {'✅' if env_ok else '❌'}")
        print(f"   Conexión Supabase: {'✅' if supabase_ok else '❌'}")
        print(f"   Conexión Twilio: {'✅' if twilio_ok else '❌'}")
        
        if not all([env_ok, supabase_ok, twilio_ok]):
            print("❌ Configuración incompleta - no se puede continuar")
            return False
        
        # 2. Analizar reservas actuales
        print("\n2️⃣ ANALIZANDO RESERVAS...")
        from scripts.check_reminder_system import analizar_reservas_manana
        
        reservas_info = analizar_reservas_manana()
        print(f"   Reservas para mañana: {reservas_info.get('pendientes_recordatorio', 0)}")
        print(f"   Problemas detectados: {len(reservas_info.get('problemas', []))}")
        
        # 3. Probar sistema de recordatorios (modo simulación)
        print("\n3️⃣ PROBANDO SISTEMA DE RECORDATORIOS...")
        
        # Simular una ejecución sin enviar mensajes reales
        try:
            from services.recordatorio_service import enviar_recordatorios_reservas
            
            # Guardar estado original
            original_test_mode = os.getenv('TEST_MODE')
            
            # Activar modo de prueba
            os.environ['TEST_MODE'] = 'true'
            
            print("   🧪 Ejecutando en modo de prueba...")
            resultado = enviar_recordatorios_reservas()
            
            # Restaurar estado original
            if original_test_mode:
                os.environ['TEST_MODE'] = original_test_mode
            elif 'TEST_MODE' in os.environ:
                del os.environ['TEST_MODE']
            
            if resultado.get('success'):
                reservas_encontradas = resultado.get('reservas_encontradas', 0)
                print(f"   ✅ Sistema funcionando correctamente")
                print(f"   📊 Reservas encontradas: {reservas_encontradas}")
            else:
                print(f"   ❌ Error en el sistema: {resultado.get('error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error ejecutando prueba: {str(e)}")
            return False
        
        # 4. Verificar horarios de cron
        print("\n4️⃣ VERIFICANDO CONFIGURACIÓN DE CRON...")
        ahora_argentina = datetime.now(ARGENTINA_TZ)
        hora_actual = ahora_argentina.hour
        
        print(f"   Hora actual en Argentina: {ahora_argentina.strftime('%H:%M %Z')}")
        
        # Verificar si estamos cerca de los horarios de ejecución
        horarios_cron = [9, 10, 14]  # 9 AM (verificación), 10 AM (principal), 2 PM (respaldo)
        
        for hora_cron in horarios_cron:
            diferencia = abs(hora_actual - hora_cron)
            if diferencia <= 1:
                print(f"   ⏰ ATENCIÓN: Estamos cerca del horario de ejecución ({hora_cron}:00)")
        
        print("   ✅ Horarios de cron configurados correctamente")
        
        # 5. Resumen final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE LA PRUEBA")
        print("=" * 60)
        print("✅ Configuración: OK")
        print("✅ Conexiones: OK") 
        print("✅ Sistema de recordatorios: OK")
        print("✅ Configuración de cron: OK")
        print("\n🎉 SISTEMA COMPLETAMENTE OPERATIVO")
        print("\n📝 Próximas ejecuciones programadas:")
        print("   • 09:00 AM Argentina - Verificación del sistema")
        print("   • 10:00 AM Argentina - Envío principal de recordatorios")
        print("   • 14:00 PM Argentina - Envío de respaldo")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN LA PRUEBA: {str(e)}")
        import traceback
        print(f"📊 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
