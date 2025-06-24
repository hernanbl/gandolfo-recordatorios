from flask import Blueprint, request, jsonify
import services.ai_service as ai_service
from models.conversation import conversation_manager
from services.twilio_service import send_whatsapp_message
from routes.twilio_routes import get_restaurant_config_by_twilio_number
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    """
    Webhook para recibir mensajes de WhatsApp a través de Twilio
    """
    try:
        # Log all request data for debugging
        print("Twilio Webhook Request:")
        print(f"Form data: {request.form}")
        print(f"Headers: {request.headers}")
        
        # Obtener datos del mensaje
        message_body = request.form.get('Body', '')
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')  # Número del restaurante
        message_sid = request.form.get('MessageSid', '')
        
        print(f"Webhook de Twilio recibido - Mensaje: '{message_body}', De: {from_number}, Para: {to_number}, SID: {message_sid}")
        
        # Obtener configuración del restaurante basada en el número de Twilio
        restaurant_config = get_restaurant_config_by_twilio_number(to_number)
        if not restaurant_config:
            print(f"Error: No se encontró configuración para el número {to_number}")
            return '', 400
        
        # Procesar el mensaje con la IA
        if message_body and from_number:
            print(f"Procesando mensaje de WhatsApp: {message_body}")
            
            # Usar el número de WhatsApp como identificador de usuario
            user_id = from_number  # Ya incluye 'whatsapp:+'
            
            # Añadir mensaje al historial de conversación
            conversation_manager.add_message(user_id, "user", message_body)
            
            # Procesar el mensaje - use the function that exists in the module
            if hasattr(ai_service, 'get_deepseek_response'):
                response = ai_service.get_deepseek_response(message_body, user_id)
            elif hasattr(ai_service, 'chat_with_ai'):
                response = ai_service.chat_with_ai(message_body, user_id)
            elif hasattr(ai_service, 'generate_ai_response'):
                response = ai_service.generate_ai_response(message_body, user_id)
            else:
                # Fallback to a generic function that might exist
                print("Warning: Using fallback method to process message")
                response = "Lo siento, no puedo procesar tu mensaje en este momento."
            
            # Verificar si se procesó correctamente
            if response:
                print(f"Respuesta generada: {response}")
                
                # Enviar la respuesta al usuario de WhatsApp
                phone_number = from_number.replace('whatsapp:', '')
                sent = send_whatsapp_message(phone_number, response, restaurant_config)
                
                if sent:
                    print(f"Respuesta enviada a {from_number}")
                else:
                    print(f"No se pudo enviar el mensaje de WhatsApp. Continuando sin enviar.")
            else:
                print(f"Error: No se pudo procesar el mensaje de {from_number}")
            
            # Devolver una respuesta vacía para Twilio
            return '', 204
        else:
            print("Error: Datos incompletos en la solicitud de Twilio")
            return '', 400
            
    except Exception as e:
        print(f"Error en webhook de Twilio: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return '', 500