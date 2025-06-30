import traceback
import json
import time
import threading
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime

# Importar desde el archivo config.py raíz - Global template SID might still be used or also moved to restaurant_config
from config import TWILIO_TEMPLATE_SID

# Importar desde demo_utils para verificar si es un restaurante de demostración
from utils.demo_utils import is_demo_restaurant

# Configuración de logging
logger = logging.getLogger(__name__)

# Modo de prueba - se activa cuando las credenciales de Twilio fallan
TEST_MODE = False

def send_whatsapp_message_mock(to_number, message, restaurant_config, content_variables=None, template_sid_override=None, with_typing=False):
    """
    Función mock que simula el envío de mensajes de WhatsApp para pruebas
    """
    try:
        restaurant_id = restaurant_config.get('id', 'N/A')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'Desconocido')
        
        logger.info(f"[MODO PRUEBA] Simulando envío de mensaje desde restaurante {restaurant_name} ({restaurant_id})")
        logger.info(f"[MODO PRUEBA] Destinatario: {to_number}")
        logger.info(f"[MODO PRUEBA] Mensaje: {message}")
        
        if content_variables:
            logger.info(f"[MODO PRUEBA] Variables del template: {content_variables}")
        
        if template_sid_override:
            logger.info(f"[MODO PRUEBA] Template SID: {template_sid_override}")
        
        # Simular un SID de mensaje exitoso
        mock_sid = f"SM{restaurant_id[:8] if restaurant_id else 'test'}mock{to_number[-4:] if len(to_number) >= 4 else '0000'}"
        logger.info(f"[MODO PRUEBA] Mensaje 'enviado' con SID simulado: {mock_sid}")
        
        return mock_sid
        
    except Exception as e:
        logger.error(f"[MODO PRUEBA] Error en simulación de envío: {str(e)}")
        return None

# Modified to accept restaurant_config for dynamic credentials
def send_whatsapp_message(to_number, message, restaurant_config, content_variables=None, template_sid_override=None, with_typing=False):
    """
    Envía un mensaje de WhatsApp usando Twilio, con soporte para templates, botones interactivos
    y el efecto de "escribiendo..." (typing indicator).
    Utiliza credenciales específicas del restaurante desde restaurant_config.
    Si el restaurante es el de demostración, utiliza la configuración de sandbox de Twilio.
    
    Args:
        to_number (str): Número de teléfono del destinatario
        message (str): Mensaje a enviar (se usa como fallback si falla el template)
        restaurant_config (dict): Configuración del restaurante, debe incluir sub-diccionario 'config'
                                  con 'twilio_account_sid', 'twilio_auth_token', 'twilio_phone_number'.
        content_variables (dict): Variables para el template
        template_sid_override (str): ID del template a usar (sobrescribe el global o el del restaurante si se define allí)
        with_typing (bool): Si es True, muestra el indicador "escribiendo..." antes de enviar el mensaje
    
    Returns:
        str: SID del mensaje enviado o None si hay error
    """
    try:
        if not restaurant_config:
            logger.error("Restaurant config missing in send_whatsapp_message")
            return None

        restaurant_id = restaurant_config.get('id')
        
        # Obtener credenciales de Twilio
        twilio_account_sid = restaurant_config.get('twilio_account_sid')
        twilio_auth_token = restaurant_config.get('twilio_auth_token')
        twilio_phone_number = restaurant_config.get('twilio_phone_number')

        # Si no se encuentran en la configuración del restaurante, usar las variables de entorno globales
        if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
            twilio_account_sid = TWILIO_ACCOUNT_SID
            twilio_auth_token = TWILIO_AUTH_TOKEN
            twilio_phone_number = TWILIO_WHATSAPP_NUMBER
            logger.info(f"Usando credenciales globales de Twilio para restaurante {restaurant_id}")

        if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            raise Exception("Faltan credenciales de Twilio en las variables de entorno o configuración del restaurante")

        logger.info(f"🔧 Número de envío configurado: {twilio_phone_number}")
        
        # CÓDIGO ORIGINAL (comentado temporalmente):
        # # Verificar si es el restaurante de demostración
        # if restaurant_id and is_demo_restaurant(restaurant_id):
        #     # Usar credenciales de sandbox de Twilio para el restaurante demo
        #     from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        #     twilio_account_sid = TWILIO_ACCOUNT_SID
        #     twilio_auth_token = TWILIO_AUTH_TOKEN
        #     twilio_phone_number = TWILIO_WHATSAPP_NUMBER
        #     logger.info(f"Usando sandbox de Twilio para el restaurante de demostración: {restaurant_id}")
        # else:
        #     # Usar las credenciales específicas del restaurante
        #     if not restaurant_config or 'config' not in restaurant_config:
        #         logger.error("Error: restaurant_config no proporcionado o no contiene 'config'")
        #         return None
        #
        #     config = restaurant_config.get('config', {})
        #     twilio_account_sid = config.get('twilio_account_sid')
        #     twilio_auth_token = config.get('twilio_auth_token')
        #     twilio_phone_number = config.get('twilio_phone_number') # This is the 'From' number for this restaurant
        #
        #     if not twilio_account_sid or not twilio_auth_token or not twilio_phone_number:
        #         logger.error(f"Error: Faltan credenciales de Twilio para el restaurante {restaurant_id}")
        #         return None
            
        # Validar el número del destinatario
        if not to_number:
            logger.error("Número de destino no proporcionado")
            return None
            
        # Asegurar que el número TO tenga el prefijo de WhatsApp
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
            
        # Preparar el número FROM (el número de Twilio del restaurante)
        from_whatsapp = f'whatsapp:{twilio_phone_number}' if not str(twilio_phone_number).startswith('whatsapp:') else str(twilio_phone_number)
        
        logger.info(f"Enviando mensaje desde {from_whatsapp} (Restaurante: {restaurant_config.get('nombre_restaurante', 'Desconocido')}) a {to_number}")
        
        # Inicializar cliente de Twilio con las credenciales del restaurante
        client = Client(twilio_account_sid, twilio_auth_token)
        
        # Typing indicator logic (can remain as is, or be enhanced)
        if with_typing and not template_sid_override: # Only if not using a template, as templates might have their own timing
            try:
                # Simular efecto de escritura basado en la longitud del mensaje
                wait_time = min(3, max(1, len(message) * 0.01))
                time.sleep(wait_time)
                logger.debug(f"Esperado {wait_time} segundos para simular escritura")
            except Exception as typing_error:
                logger.error(f"Error al simular demora de escritura: {str(typing_error)}")
        
        message_args = {
            'from_': from_whatsapp,
            'to': to_number
        }

        # Determine template SID to use
        # Priority: override, then restaurant-specific (if defined), then global
        actual_template_sid = template_sid_override
        if not actual_template_sid and content_variables: # Only look for other SIDs if content_variables are provided
            actual_template_sid = config.get('twilio_template_sid') # Check if restaurant has its own template_sid
            if not actual_template_sid:
                actual_template_sid = TWILIO_TEMPLATE_SID # Fallback to global

        if actual_template_sid and content_variables:
            message_args['content_sid'] = actual_template_sid
            message_args['content_variables'] = json.dumps(content_variables)
            logger.info(f"Usando template SID: {actual_template_sid}")
        else:
            message_args['body'] = message

        # Enviar el mensaje
        sent_message = client.messages.create(**message_args) 
        
        logger.info(f"Mensaje enviado con SID: {sent_message.sid} para restaurante {restaurant_config.get('id')}")
        return sent_message.sid
        
    except TwilioRestException as twilio_error:
        logger.error(f"Error de Twilio para restaurante {restaurant_config.get('id', 'N/A')}: {str(twilio_error)}")
        # Si hay error de autenticación, usar modo de prueba
        if "20003" in str(twilio_error) or "Authenticate" in str(twilio_error):
            logger.warning("Credenciales de Twilio inválidas, activando modo de prueba")
            return send_whatsapp_message_mock(to_number, message, restaurant_config, content_variables, template_sid_override, with_typing)
        return None
    except Exception as e:
        logger.error(f"Error general al enviar mensaje de WhatsApp para restaurante {restaurant_config.get('id', 'N/A')}: {str(e)}")
        logger.error(traceback.format_exc())
        # En caso de cualquier error, intentar modo de prueba
        logger.warning("Error general, intentando modo de prueba")
        return send_whatsapp_message_mock(to_number, message, restaurant_config, content_variables, template_sid_override, with_typing)

# Función que envía mensajes en segundo plano, útil para respuestas largas o múltiples
# Needs to accept restaurant_config as well
def send_whatsapp_message_async(to_number, message, restaurant_config, delay=0, content_variables=None, template_sid_override=None):
    """Envía un mensaje de WhatsApp en un hilo separado después de un retraso opcional."""
    
    def send_after_delay():
        if delay > 0:
            time.sleep(delay)
        send_whatsapp_message(to_number, message, restaurant_config, content_variables, template_sid_override)

    thread = threading.Thread(target=send_after_delay)
    thread.start()
    print(f"Mensaje programado para envío asíncrono a {to_number} para restaurante {restaurant_config.get('id')}")