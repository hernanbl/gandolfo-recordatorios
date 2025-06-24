from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import traceback
import re
import json
import os
from datetime import datetime, timedelta

# Configuración de logging
logger = logging.getLogger(__name__)

# Crear el blueprint para las rutas de recordatorios y confirmaciones
reminder_bp = Blueprint('reminder', __name__)

@reminder_bp.route('/webhook', methods=['POST'])
def reminder_webhook():
    """
    Procesa las respuestas a los recordatorios de reservas existentes.
    Esta ruta está separada del bot de Twilio para nuevas reservas.
    """
    try:
        # Obtener el mensaje entrante
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')
        message_sid = request.values.get('MessageSid', '')
        
        # Log detallado para depuración
        logger.info("=== INICIO PROCESAMIENTO WEBHOOK RECORDATORIO ===")
        logger.info(f"URL path: {request.path}")
        logger.info(f"Método HTTP: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Mensaje recibido - De: {sender}")
        logger.info(f"Contenido del mensaje: '{incoming_msg}'")
        logger.info(f"SID del mensaje: {message_sid}")
        logger.info(f"Datos completos del request: {dict(request.values)}")
        
        # Inicializar respuesta
        response = MessagingResponse()

        # Obtener el número de Twilio para detectar el restaurante
        twilio_to_number = request.values.get('To', '')
        logger.info(f"Número de Twilio destino: {twilio_to_number}")
        
        # Detectar restaurante usando el número de Twilio
        from routes.twilio_routes import get_restaurant_config_by_twilio_number
        restaurant_config = get_restaurant_config_by_twilio_number(twilio_to_number)
        
        if not restaurant_config:
            logger.error(f"No se pudo obtener configuración del restaurante para {twilio_to_number}")
            response.message("Lo sentimos, no pudimos identificar el restaurante. Por favor, contacta al administrador.")
            return str(response)
        
        restaurant_id = restaurant_config.get('id')
        logger.info(f"Restaurante detectado: {restaurant_config.get('nombre_restaurante', 'N/A')} (ID: {restaurant_id})")

        # Verificar si es una respuesta a recordatorio
        from services.twilio.reminder_handler import get_user_session_data
        reminder_data = get_user_session_data(sender, restaurant_id)
        logger.info(f"Datos de recordatorio encontrados: {reminder_data}")
        
        if not reminder_data or not reminder_data.get('is_reminder'):
            logger.info("No es una respuesta a recordatorio, redirigiendo al flujo principal")
            return str(response)

        # Verificar si es una solicitud de reinicio/reset
        is_reset_request = incoming_msg.strip().lower() in ["reset", "reiniciar", "refresh", "reinicio", "comenzar de nuevo", "empezar de nuevo", "borrar", "limpiar"]
        
        if is_reset_request:
            try:
                from services.twilio.reminder_handler import reset_user_session
                logger.info(f"Detectada solicitud de reinicio de sesión: '{incoming_msg}' de {sender}")
                result = reset_user_session(sender, restaurant_id, restaurant_config)
                logger.info(f"Resultado de reinicio de sesión: {result}")
                return str(response)
            except Exception as reset_error:
                logger.error(f"Error al procesar solicitud de reinicio: {str(reset_error)}")
                logger.error(traceback.format_exc())
                response.message("Lo sentimos, ha ocurrido un error al reiniciar tu sesión. Por favor, intenta nuevamente.")
                return str(response)

        # Lista de palabras clave para confirmación y cancelación
        confirmation_keywords = ["1", "confirmar", "confirmo", "confirm", "si", "sí", "s"]
        cancellation_keywords = ["2", "cancelar", "cancelo", "cancel", "no", "n"]
        
        # Verificar si el mensaje es una confirmación o cancelación
        normalized_msg = incoming_msg.strip().lower()
        
        # Log del mensaje normalizado
        logger.info(f"Mensaje normalizado: '{normalized_msg}'")
        
        # Verificar coincidencias exactas primero
        is_confirmation = normalized_msg == "1" or normalized_msg in confirmation_keywords
        is_cancellation = normalized_msg == "2" or normalized_msg in cancellation_keywords
        
        # Log de primera verificación
        logger.info(f"Primera verificación - Es confirmación: {is_confirmation}, Es cancelación: {is_cancellation}")
        
        # Si no hay coincidencia exacta, buscar coincidencias parciales
        if not is_confirmation and not is_cancellation:
            for keyword in confirmation_keywords:
                if keyword in normalized_msg:
                    is_confirmation = True
                    logger.info(f"Confirmación detectada por coincidencia parcial con '{keyword}'")
                    break
                    
            if not is_confirmation:
                for keyword in cancellation_keywords:
                    if keyword in normalized_msg:
                        is_cancellation = True
                        logger.info(f"Cancelación detectada por coincidencia parcial con '{keyword}'")
                        break
        
        # Verificar si es un nombre propio (2+ palabras con letras)
        palabras = normalized_msg.split()
        is_nombre_propio = len(palabras) >= 2 and all(palabra.isalpha() for palabra in palabras)
        if is_nombre_propio:
            logger.info(f"Nombre propio detectado como posible confirmación: '{incoming_msg}'")
            is_confirmation = True
            
        is_confirmation_response = is_confirmation or is_cancellation
        
        # Log final de verificación
        logger.info(f"Verificación final - Es confirmación: {is_confirmation}, Es cancelación: {is_cancellation}")
        
        if is_confirmation_response:
            try:
                # Importar el manejador de recordatorios
                from services.twilio.reminder_handler import handle_reminder_response, is_conversation_completed
                
                # Verificar si la conversación ya está completada
                if is_conversation_completed(sender, restaurant_id):
                    logger.info(f"Conversación ya completada para {sender} en restaurante {restaurant_id}")
                    return str(response)
                
                logger.info(f"🔄 Enviando respuesta a recordatorio: '{incoming_msg}' de {sender} a handle_reminder_response")
                result = handle_reminder_response(incoming_msg, sender, restaurant_config)
                logger.info(f"✅ Respuesta procesada: {result}")
                
                return str(response)
                
            except Exception as reminder_error:
                logger.error(f"❌ Error al procesar respuesta a recordatorio: {str(reminder_error)}")
                logger.error(traceback.format_exc())
                response.message("Lo sentimos, ha ocurrido un error al procesar tu respuesta. Por favor, contacta directamente al restaurante al 116-6668-6255.")
                return str(response)
        else:
            # Si no es una respuesta de confirmación o cancelación, enviar mensaje de ayuda
            logger.info("Mensaje no reconocido como confirmación o cancelación, enviando ayuda")
            from services.twilio.reminder_handler import send_help_message
            send_help_message(sender, restaurant_config)
            return str(response)
            
    except Exception as e:
        logger.error(f"Error en el webhook de recordatorios: {str(e)}")
        logger.error(traceback.format_exc())
        response = MessagingResponse()
        response.message("Lo sentimos, ha ocurrido un error. Por favor, contacta directamente al restaurante al 116-6668-6255.")
        return str(response)

    finally:
        logger.info("=== FIN PROCESAMIENTO WEBHOOK RECORDATORIO ===")
        logger.info("----------------------------------------")

# Nueva ruta para manejar las notificaciones de estado de los mensajes de Twilio
@reminder_bp.route('/status', methods=['POST'])
def reminder_status_callback():
    """Procesa las notificaciones de estado de los mensajes de recordatorio"""
    try:
        # Obtener datos de la notificación
        message_sid = request.values.get('MessageSid', '')
        message_status = request.values.get('MessageStatus', '')
        to = request.values.get('To', '')
        
        # Registrar la notificación de estado
        logger.info(f"Notificación de estado de recordatorio recibida - SID: {message_sid}, Estado: {message_status}, Destinatario: {to}")
        
        # Si el mensaje falló, podríamos intentar reenviarlo o notificar al administrador
        if message_status in ['failed', 'undelivered']:
            error_code = request.values.get('ErrorCode', '')
            error_message = request.values.get('ErrorMessage', '')
            logger.error(f"Error en mensaje de recordatorio {message_sid}: Código {error_code} - {error_message}")
            
        # Respuesta vacía con código 200 para confirmar recepción
        return '', 200
        
    except Exception as e:
        logger.error(f"Error al procesar notificación de estado de recordatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return '', 500