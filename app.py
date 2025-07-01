from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, g
from functools import wraps
from flask_cors import CORS
import os
import json
import logging
from supabase import create_client, Client
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse  # Added import
load_dotenv()
from config import (
    SECRET_KEY, DEBUG, PORT, 
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_ENABLED,
    DEEPSEEK_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER,
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM,
    DEFAULT_RESTAURANT_ID, PROCESSED_DATA_DIRECTORY,  # Added PROCESSED_DATA_DIRECTORY
    BASE_DIR,  # Import BASE_DIR
    DEMO_RESTAURANT_ID, DEMO_RESTAURANT_NAME, DEMO_MODE_ENABLED
)
from werkzeug.exceptions import HTTPException, InternalServerError
from asgiref.wsgi import WsgiToAsgi

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de zona horaria
TIMEZONE = timezone('America/Argentina/Buenos_Aires')  # BUE

# Default restaurant data structure (placeholder if not defined elsewhere)
DEFAULT_RESTAURANT_DATA = {
    "name": "Mi Restaurante",
    "address": "Dirección Desconocida",
    "phone": "000-0000000",
    "email": "contacto@example.com",
    "website": "www.example.com",
    "description": "Un lugar increíble para comer.",
    "opening_hours": {
        "lunes": {"almuerzo_abre": "12:00", "almuerzo_cierra": "15:00", "cena_abre": "20:00", "cena_cierra": "23:00"},
        "martes": {"almuerzo_abre": "12:00", "almuerzo_cierra": "15:00", "cena_abre": "20:00", "cena_cierra": "23:00"},
        "miércoles": {"almuerzo_abre": "12:00", "almuerzo_cierra": "15:00", "cena_abre": "20:00", "cena_cierra": "23:00"},
        "jueves": {"almuerzo_abre": "12:00", "almuerzo_cierra": "15:00", "cena_abre": "20:00", "cena_cierra": "23:00"},
        "viernes": {"almuerzo_abre": "12:00", "almuerzo_cierra": "15:00", "cena_abre": "20:00", "cena_cierra": "00:00"},
        "sábado": {"almuerzo_abre": "12:00", "almuerzo_cierra": "16:00", "cena_abre": "20:00", "cena_cierra": "00:00"},
        "domingo": {"almuerzo_abre": "12:00", "almuerzo_cierra": "16:00", "cena_abre": "cerrado", "cena_cierra": "cerrado"}
    },
    "config": {"activo": True}
}

# Ensure the data/menus directory exists
MENUS_DATA_DIRECTORY = os.path.join(BASE_DIR, 'data', 'menus')
os.makedirs(MENUS_DATA_DIRECTORY, exist_ok=True)
logger.info(f"Menus directory is set to: {MENUS_DATA_DIRECTORY}")

# Ensure the data/info directory exists
INFO_DIRECTORY = os.path.join(BASE_DIR, 'data', 'info')
os.makedirs(INFO_DIRECTORY, exist_ok=True)
logger.info(f"Info directory is set to: {INFO_DIRECTORY}")

# Ensure the data/processed directory exists
PROCESSED_DIRECTORY = os.path.join(BASE_DIR, 'data', 'processed')
os.makedirs(PROCESSED_DIRECTORY, exist_ok=True)
logger.info(f"Processed directory is set to: {PROCESSED_DIRECTORY}")

# Conexión Supabase
supabase = None
if SUPABASE_ENABLED:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Conexión a Supabase establecida correctamente")
    except Exception as e:
        logger.error(f"Error al conectar con Supabase: {str(e)}")
        if not DEBUG:
            raise

# Register error handlers for API routes
def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    return jsonify(error=str(error)), code

# Initialize Flask app only once
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
app.secret_key = SECRET_KEY
# Lista de dominios permitidos
origins = [
    "https://gandolfo.app",
    "https://www.gandolfo.app",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000" # Puerto común para desarrollo de frontend
]
CORS(app, supports_credentials=True, origins=origins)

# Configure error handlers for API routes
@app.errorhandler(Exception)
def handle_exception(e):
    if request.path.startswith('/api/'):
        return handle_error(e)
    return e  # Let Flask handle non-API errors normally

# Import the login_required decorator from its new location
from utils.auth import login_required
from utils.demo_utils import initialize_demo_restaurant_if_needed

# Blueprints (moved after login_required definition)
from routes import admin_bp
from routes.web_routes import web_bp
from routes.api_routes import api_bp
from routes.twilio_routes import twilio_bp
from routes.reminder_routes import reminder_bp
from routes.demo_routes import demo_bp
from routes.restaurant_selector import restaurant_bp

# FORZAR la ejecución de admin_routes.py para asegurar el registro de todas las rutas
import routes.admin_routes

# Register blueprints
app.register_blueprint(web_bp)
app.register_blueprint(api_bp, url_prefix='/api')  # Register API routes with prefix
app.register_blueprint(twilio_bp, url_prefix='/api/twilio')  # Register Twilio webhook blueprint with '/api/twilio' prefix
app.register_blueprint(admin_bp, url_prefix='/admin')  # Register admin routes with '/admin' prefix
app.register_blueprint(reminder_bp)
app.register_blueprint(demo_bp)
app.register_blueprint(restaurant_bp)



# Manejadores de error personalizados
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html' if os.path.exists(os.path.join(app.template_folder, '500.html')) else '404.html'), 500

# Inicializar el restaurante de demostración si es necesario
if DEMO_MODE_ENABLED:
    logger.info(f"Modo de demostración habilitado para el restaurante {DEMO_RESTAURANT_NAME} (ID: {DEMO_RESTAURANT_ID})")
    initialize_demo_restaurant_if_needed()

# Before request handler to share restaurant information with templates
@app.before_request
def before_request():
    # Set restaurant information in g for templates
    if 'restaurant_id' in session:
        g.restaurant_id = session['restaurant_id']
        g.restaurant_name = session.get('restaurant_name', 'Restaurante')
    else:
        g.restaurant_id = None
        g.restaurant_name = None

if __name__ == '__main__':
    # Diagnóstico: imprimir todas las rutas registradas en Flask
    print("\n=== RUTAS REGISTRADAS EN FLASK ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> endpoint: {rule.endpoint}, methods: {rule.methods}")
    print("=== FIN DE RUTAS ===\n")
    # Make sure to use the PORT from your config, and enable debug mode
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)