#!/usr/bin/env python3
"""Script para verificar reservas próximas y enviar recordatorios
Este script debe ejecutarse periódicamente (por ejemplo, cada hora)"""

import os
import sys
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Añadir el directorio raíz al path para poder importar los módulos
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)

# Cargar variables de entorno
load_dotenv(os.path.join(app_dir, '.env'))

# Configurar logging
log_dir = os.path.join(app_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'check_reservations.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # Verificar variables de entorno requeridas
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
        sys.exit(1)

    # Importar la función correcta desde el módulo de reservations
    from services.twilio.reservations import check_upcoming_reservations
    
    logger.info("Iniciando verificación de reservas próximas...")
    result = check_upcoming_reservations()
    logger.info(f"Verificación completada. Resultado: {result}")
    
except Exception as e:
    logger.error(f"ERROR: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)