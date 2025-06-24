import os
import threading
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

# Template SID para mensajes con botones interactivos
TWILIO_TEMPLATE_SID = os.environ.get('TWILIO_TEMPLATE_SID')

# Variables para control de límites
DAILY_MESSAGE_COUNT = 0
DAILY_MESSAGE_LIMIT = 100  # Ajusta este valor según tu plan de Twilio
LAST_RESET_DATE = datetime.now().date()
MESSAGE_COUNT_LOCK = threading.Lock()

# Diccionario para seguimiento de conversaciones activas
CONVERSACIONES_ACTIVAS = {}

# Palabras clave para detectar consultas relevantes
PALABRAS_CLAVE_RESTAURANTE = [
    'reserva', 'reservar', 'mesa', 'comer', 'cenar', 'almorzar', 'restaurante', 'gandolfo',
    'horario', 'abierto', 'cerrado', 'menú', 'menu', 'carta', 'precio', 'precios',
    'dirección', 'direccion', 'ubicación', 'ubicacion', 'donde', 'dónde', 'como llegar',
    'estacionamiento', 'parking', 'valet', 'wifi', 'baño', 'sanitario',
    'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo',
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    'confirmar', 'cancelar', 'modificar', 'cambiar',
    # Métodos de pago y promociones
    'pago', 'pagos', 'tarjeta', 'efectivo', 'mercadopago', 'modo', 'transferencia', 
    'débito', 'crédito', 'debito', 'credito', 'promoción', 'promociones', 'promocion', 
    'descuento', 'descuentos', 'oferta', 'ofertas', 'beneficio', 'beneficios',
    '30%', '20%', '15%', '10%', '2x1', 'dos por uno', 'cuotas', 'sin interés', 'sin interes',
    # Números y horas comunes para reservas
    '12', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', 
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00',
    '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30'
]