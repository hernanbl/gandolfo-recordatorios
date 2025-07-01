import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde .env
load_dotenv(override=True)

# Configuración de la aplicación
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-por-defecto')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

# Configuración de Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_ENABLED = os.environ.get('SUPABASE_ENABLED', 'true').lower() == 'true'

# Configuración de DeepSeek
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = '+14155238886' # Usando el número del Sandbox de Twilio
# if TWILIO_WHATSAPP_NUMBER and TWILIO_WHATSAPP_NUMBER.startswith('whatsapp:'):
#     TWILIO_WHATSAPP_NUMBER = TWILIO_WHATSAPP_NUMBER.replace('whatsapp:', '')
TWILIO_REMINDER_TEMPLATE_SID = os.environ.get('TWILIO_REMINDER_TEMPLATE_SID')  # SID de la plantilla para recordatorios con botones
TWILIO_TEMPLATE_SID = 'HXad67da4f66de21dab850c59b4ed37bdb'  # Template SID para recordatorios con botones

# Configuración de correo electrónico
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_FROM = os.environ.get('EMAIL_FROM', EMAIL_USER)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# Email Configuration
EMAIL_CONFIG = {
    'host': 'smtp.hostinger.com',
    'port': 465,
    'use_tls': True,
    'timeout': 30,  # timeout in seconds
    'max_retries': 3,  # maximum number of retry attempts
    'retry_delay': 5,  # delay between retries in seconds
}

# Restaurant de demostración
DEMO_RESTAURANT_ID = "00000000-0000-0000-0000-000000000000"  # ID dummy - ningún restaurante será demo
DEMO_RESTAURANT_NAME = "Gandolfo Restó" # Placeholder for the demo restaurant name
DEMO_MODE_ENABLED = os.environ.get('DEMO_MODE_ENABLED', 'False').lower() == 'true' # Deshabilitado por defecto

# Detectar si estamos en entorno de producción (Render)
IS_PRODUCTION = os.environ.get('RENDER', False)

# Configuración multi-restaurante
USE_PROD_TABLES = os.environ.get('USE_PROD_TABLES', 'true').lower() == 'true'
RESERVAS_TABLE = 'reservas_prod' if USE_PROD_TABLES else 'reservas'
DEFAULT_RESTAURANT_ID = os.environ.get('DEFAULT_RESTAURANT_ID', None)  # UUID del restaurante por defecto
DEFAULT_RESTAURANT_NAME = os.environ.get('DEFAULT_RESTAURANT_NAME', 'Gandolfo Restó')

# Base directory
BASE_DIR = Path(__file__).parent

# Configurar directorios según el entorno
if IS_PRODUCTION:
    # En producción, usar rutas relativas
    PDF_DIRECTORY = os.environ.get('PDF_DIRECTORY', './data/raw')
    PROCESSED_DATA_DIRECTORY = os.environ.get('PROCESSED_DATA_DIRECTORY', './data/processed')
else:
    # En desarrollo, usar las rutas del .env
    PDF_DIRECTORY = os.environ.get('PDF_DIRECTORY', str(BASE_DIR / 'data/raw'))
    PROCESSED_DATA_DIRECTORY = os.environ.get('PROCESSED_DATA_DIRECTORY', str(BASE_DIR / 'data/processed'))