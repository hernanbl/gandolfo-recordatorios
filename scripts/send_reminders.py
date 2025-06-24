#!/usr/bin/env python3
import sys
import os
import logging
import traceback
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Add the project root to the Python path
app_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, app_dir)

# Cargar variables de entorno (solo si el archivo existe)
env_file = os.path.join(app_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"Variables de entorno cargadas desde {env_file}")
else:
    print("No se encontró archivo .env, usando variables de entorno del sistema")

# Configurar zona horaria de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

# Configure logging
log_dir = os.path.join(app_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'reminders.log')

# Configurar logging con rotación de archivos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Agregar manejadores de archivo y consola
try:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
except Exception as e:
    print(f"Advertencia: No se pudo crear el archivo de log en {log_file}: {str(e)}")
    print("Continuando con logs solo en consola")

logging.getLogger().addHandler(logging.StreamHandler())

# Import the reminder function
from services.recordatorio_service import enviar_recordatorios_reservas

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    
    # Obtener fecha y hora actual en Argentina
    ahora_argentina = datetime.now(ARGENTINA_TZ)
    manana_argentina = ahora_argentina + timedelta(days=1)
    fecha_manana = manana_argentina.strftime('%Y-%m-%d')
    
    logger.info("=== INICIANDO PROCESO DE RECORDATORIOS ===")
    logger.info(f"Fecha y hora actual en Argentina: {ahora_argentina.strftime('%d/%m/%Y %H:%M:%S %Z')}")
    logger.info(f"Fecha de mañana para buscar reservas: {manana_argentina.strftime('%d/%m/%Y')} ({fecha_manana})")
    
    # Verificar si estamos en modo de prueba
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    if test_mode:
        logger.info("🧪 Ejecutando en modo de prueba - forzando envío de recordatorios")
    
    # Verificar variables de entorno requeridas
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
        sys.exit(1)
    
    logger.info("✅ Todas las variables de entorno requeridas están presentes")
    
    # Mostrar información útil para depuración en Render
    logger.info(f"📁 Directorio de trabajo actual: {os.getcwd()}")
    logger.info(f"📁 Directorio del script: {os.path.dirname(__file__)}")
    logger.info(f"📁 Directorio de la aplicación: {app_dir}")
    
    try:
        logger.info("🚀 Llamando al servicio de recordatorios...")
        result = enviar_recordatorios_reservas()
        logger.info(f"📋 Resultado del servicio: {result}")
        
        # Mostrar un resumen más legible
        if isinstance(result, dict):
            if result.get('success', False):
                mensajes_enviados = result.get('mensajes_enviados', 0)
                mensajes_fallidos = result.get('mensajes_fallidos', 0)
                total_reservas = result.get('total_reservas', 0)
                reservas_encontradas = result.get('reservas_encontradas', 0)
                
                logger.info("=== RESUMEN FINAL ===")
                logger.info(f"📊 Reservas encontradas para mañana: {reservas_encontradas}")
                logger.info(f"📊 Total reservas procesadas: {total_reservas}")
                logger.info(f"✅ Mensajes enviados exitosamente: {mensajes_enviados}")
                logger.info(f"❌ Mensajes fallidos: {mensajes_fallidos}")
                
                if mensajes_enviados > 0:
                    logger.info("🎉 PROCESO COMPLETADO CON ÉXITO")
                elif reservas_encontradas == 0:
                    logger.info("ℹ️  No hay reservas para mañana que requieran recordatorio")
                else:
                    logger.warning("⚠️  Se encontraron reservas pero no se enviaron mensajes")
                    
            else:
                error_msg = result.get('error', 'Error desconocido')
                logger.error(f"❌ Error en el proceso: {error_msg}")
                sys.exit(1)
        else:
            logger.warning(f"⚠️  Resultado inesperado del servicio: {result}")
            
    except Exception as e:
        logger.error(f"💥 Error crítico al enviar recordatorios: {str(e)}")
        logger.error(f"📊 Traceback completo:\n{traceback.format_exc()}")
        sys.exit(1)
    
    logger.info("🏁 Proceso de recordatorios finalizado correctamente")