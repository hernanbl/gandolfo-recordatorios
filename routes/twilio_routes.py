from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import traceback
import re
import json
import os
from datetime import datetime, timedelta
import urllib.parse  # Añadimos esta importación para codificar URLs

# Import all necessary dependencies at the top level
from models.reserva import Reserva
from utils.db import supabase_client
from utils.session_manager import get_session, save_session, delete_session
from services.email_service import enviar_correo_confirmacion
from services.twilio.handler import handle_whatsapp_message

twilio_bp = Blueprint('twilio', __name__, url_prefix='')

# Configuración de logging
logger = logging.getLogger(__name__)

def get_restaurant_config_by_twilio_number(twilio_to_number: str):
    """
    Obtiene la configuración de un restaurante desde Supabase usando el número de Twilio 'To'.
    Incluye retry automático para resolver timeouts.
    """
    global supabase_client
    
    if not twilio_to_number:
        logger.error("Número de Twilio no proporcionado para buscar configuración.")
        return None

    # Intentar reconectar si no hay cliente
    if not supabase_client:
        logger.warning("Cliente Supabase no inicializado. Reintentando conexión...")
        try:
            from services.db.supabase import get_supabase_client
            supabase_client = get_supabase_client(force_new=True)
            if supabase_client:
                logger.info("✅ Cliente Supabase reconectado exitosamente")
            else:
                logger.error("❌ No se pudo reconectar a Supabase")
                return None
        except Exception as e:
            logger.error(f"Error al reconectar Supabase: {str(e)}")
            return None

    # Normalizar el número
    normalized_number = twilio_to_number.strip()
    if normalized_number.startswith('whatsapp:'):
        normalized_number = normalized_number.split('whatsapp:')[1].strip()
    
    logger.info(f"🔍 Buscando configuración para: {normalized_number}")

    # Función de consulta con retry
    def query_restaurant():
        # Primero buscar en config.twilio_phone_number
        response = supabase_client.table('restaurantes') \
            .select('id, nombre, config, menu, info_json, estado') \
            .eq('config->>twilio_phone_number', normalized_number) \
            .eq('estado', 'activo') \
            .execute()
        
        if response.data:
            return response.data[0]
        
        # Si no encuentra, buscar en info_json.contact.whatsapp
        logger.info("🔍 Buscando en números de WhatsApp...")
        local_number = re.sub(r'\D', '', normalized_number)[-10:]
        
        all_restaurants = supabase_client.table('restaurantes') \
            .select('id, nombre, config, menu, info_json, estado') \
            .eq('estado', 'activo') \
            .execute()
        
        # Filtrar manualmente
        for restaurant in all_restaurants.data:
            info_json = restaurant.get('info_json', {})
            contact = info_json.get('contact', {})
            whatsapp = re.sub(r'\D', '', contact.get('whatsapp', ''))[-10:]
            if whatsapp == local_number:
                return restaurant
        
        return None

    try:
        # Ejecutar con retry usando la función helper
        from services.db.supabase import execute_with_retry
        restaurant_data = execute_with_retry(query_restaurant)
        
        if restaurant_data:
            logger.info(f"✅ Restaurante encontrado: {restaurant_data.get('nombre')} (ID: {restaurant_data.get('id')})")
            
            # Agregar campo nombre_restaurante para compatibilidad
            restaurant_data['nombre_restaurante'] = restaurant_data.get('nombre')
            
            # Cargar datos JSON del restaurante
            restaurant_id = restaurant_data.get('id')
            if restaurant_id:
                # Cargar archivos locales
                try:
                    import json
                    
                    # Cargar menú
                    menu_file = os.path.join(os.getcwd(), 'data', 'menus', f"{restaurant_id}_menu.json")
                    if os.path.exists(menu_file):
                        with open(menu_file, 'r', encoding='utf-8') as f:
                            restaurant_data['menu_json'] = json.load(f)
                    
                    # Cargar info
                    info_file = os.path.join(os.getcwd(), 'data', 'info', f"{restaurant_id}_info.json")
                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            restaurant_data['info_json'] = json.load(f)
                            
                except Exception as e:
                    logger.warning(f"Error cargando archivos JSON: {str(e)}")
            
            # Configurar credenciales de Twilio
            config_json = restaurant_data.get('config', {})
            if not config_json or not all(k in config_json for k in ['twilio_account_sid', 'twilio_auth_token']):
                from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
                restaurant_data['config'] = {
                    'twilio_account_sid': TWILIO_ACCOUNT_SID,
                    'twilio_auth_token': TWILIO_AUTH_TOKEN,
                    'twilio_phone_number': TWILIO_WHATSAPP_NUMBER
                }
            
            logger.info("✅ Configuración de restaurante completada")
            return restaurant_data
        else:
            logger.warning(f"❌ No se encontró restaurante para: {normalized_number}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error crítico en búsqueda de restaurante: {str(e)}")
        logger.error(traceback.format_exc())
        return None
@twilio_bp.route('/status', methods=['POST'])
def twilio_status_callback():
    """Procesa las notificaciones de estado de los mensajes de Twilio"""
    try:
        # Obtener datos de la notificación
        message_sid = request.values.get('MessageSid', '')
        message_status = request.values.get('MessageStatus', '')
        to = request.values.get('To', '')
        
        # Registrar la notificación de estado
        logger.info(f"Notificación de estado recibida - SID: {message_sid}, Estado: {message_status}, Destinatario: {to}")
        
        # Si el mensaje falló, podríamos intentar reenviarlo o notificar al administrador
        if message_status in ['failed', 'undelivered']:
            error_code = request.values.get('ErrorCode', '')
            error_message = request.values.get('ErrorMessage', '')
            logger.error(f"Error en mensaje {message_sid}: Código {error_code} - {error_message}")
            
            # Aquí podrías implementar lógica para reenviar el mensaje o notificar al administrador
        
        # Si el mensaje fue entregado, podríamos actualizar algún registro en la base de datos
        elif message_status == 'delivered':
            # Actualizar estado del mensaje en la base de datos si es necesario
            pass
        
        # Respuesta vacía con código 200 para confirmar recepción
        return '', 200
        
    except Exception as e:
        logger.error(f"Error al procesar notificación de estado: {str(e)}")
        logger.error(traceback.format_exc())
        return '', 500

@twilio_bp.route('/webhook', methods=['GET','POST'])
def twilio_webhook():
    # Responder a GET para verificar que el webhook está activo
    if request.method == 'GET':
        return "Webhook endpoint is live", 200
    """Procesa los mensajes entrantes de Twilio WhatsApp"""
    logger.info("!!! WEBHOOK /webhook HA SIDO CONTACTADO !!!") # Nuevo log
    try:
        # Imprimir todos los datos recibidos para debug
        logger.debug("Headers recibidos:")
        for header, value in request.headers.items():
            logger.debug(f"{header}: {value}")
        
        logger.debug("Datos del formulario recibidos:")
        for key, value in request.form.items():
            logger.debug(f"{key}: {value}")
        
        # Obtener el mensaje entrante con validación robusta
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')
        message_sid = request.values.get('MessageSid', '')
        twilio_to_number = request.values.get('To', '') # Número de Twilio que recibió el mensaje
        
        # Logging detallado para debugging
        logger.info(f"=== DATOS RECIBIDOS DE TWILIO ===")
        logger.info(f"Body: '{incoming_msg}'")
        logger.info(f"From: '{sender}'")
        logger.info(f"To: '{twilio_to_number}'")
        logger.info(f"MessageSid: '{message_sid}'")
        logger.info(f"Valores completos: {dict(request.values)}")
        logger.info(f"=== FIN DATOS TWILIO ===")

        logger.info(f"Mensaje recibido de {sender} para {twilio_to_number}: '{incoming_msg}' (SID: {message_sid})") 
        response = MessagingResponse()
        
        # Validación robusta de datos críticos
        validation_errors = []
        
        # Validar 'From' (remitente)
        if not sender:
            validation_errors.append("remitente (From)")
        elif not sender.startswith('whatsapp:'):
            logger.warning(f"Formato de remitente inusual: {sender}")
        
        # Validar 'Body' (mensaje)
        if not incoming_msg:
            # Verificar si es un mensaje vacío intencional o datos faltantes
            if sender:  # Si tenemos remitente pero no mensaje
                logger.warning(f"Mensaje vacío recibido de {sender} - puede ser un mensaje multimedia o error")
                # Verificar si hay archivos multimedia
                num_media = request.values.get('NumMedia', '0')
                if num_media and int(num_media) > 0:
                    logger.info(f"Mensaje multimedia detectado con {num_media} archivos de {sender}")
                    response.message("📎 Hemos recibido tu archivo multimedia. Por el momento, solo podemos procesar mensajes de texto para reservas. ¿En qué podemos ayudarte?")
                    return str(response)
                else:
                    validation_errors.append("contenido del mensaje (Body)")
            else:
                validation_errors.append("contenido del mensaje (Body)")
        
        # Validar 'MessageSid'
        if not message_sid:
            validation_errors.append("identificador del mensaje (MessageSid)")
        
        # Si hay errores críticos de validación
        if validation_errors:
            error_msg = f"❌ DATOS CRÍTICOS FALTANTES: {', '.join(validation_errors)}"
            logger.error(error_msg)
            
            # Si tenemos al menos el remitente, enviar mensaje personalizado
            if sender:
                response.message("Lo sentimos, hubo un problema al recibir tu mensaje. Por favor, intenta enviarlo nuevamente.")
            else:
                response.message("Error: No se recibieron datos válidos del mensaje. Por favor, intenta nuevamente.")
            return str(response)
        
        # Validación adicional del contenido del mensaje
        if len(incoming_msg) > 1000:  # Límite razonable para mensajes
            logger.warning(f"Mensaje muy largo recibido ({len(incoming_msg)} caracteres) de {sender}")
            response.message("El mensaje es demasiado largo. Por favor, envía un mensaje más corto para que podamos ayudarte mejor.")
            return str(response)
        
        # Detectar posibles caracteres problemáticos
        problematic_chars = ['�', '\ufffd']  # Caracteres de reemplazo Unicode
        if any(char in incoming_msg for char in problematic_chars):
            logger.warning(f"Caracteres problemáticos detectados en mensaje de {sender}: {incoming_msg}")
            response.message("Parece que tu mensaje contiene caracteres que no podemos procesar. Por favor, intenta enviarlo nuevamente usando solo texto.")
            return str(response)

        # Obtener y validar configuración del restaurante
        if not twilio_to_number:
            logger.warning("Número de Twilio 'To' no proporcionado en la solicitud. Intentando con número por defecto...")
            # Intentar obtener el número de Twilio por defecto de las variables de entorno
            import os
            default_twilio_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
            if default_twilio_number:
                # Asegurar formato correcto
                if not default_twilio_number.startswith('whatsapp:'):
                    default_twilio_number = f"whatsapp:{default_twilio_number}"
                twilio_to_number = default_twilio_number
                logger.info(f"Usando número por defecto: {twilio_to_number}")
            else:
                logger.error("No se pudo obtener ningún número de Twilio")
                response.message("Error: No se pudo identificar el número de destino. Por favor, contacta al administrador.")
                return str(response)
            
        try:
            logger.debug(f"Obteniendo configuración para el número: {twilio_to_number}")
            restaurant_config = get_restaurant_config_by_twilio_number(twilio_to_number)
            logger.debug(f"Configuración del restaurante obtenida: {restaurant_config}")

            if not restaurant_config:
                logger.warning(f"No se encontró configuración para el número: {twilio_to_number}")
                logger.info("🔧 USANDO CONFIGURACIÓN DE FALLBACK PARA SANDBOX")
                
                # Crear configuración de fallback para sandbox
                from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, DEFAULT_RESTAURANT_NAME
                
                # Buscar el primer restaurante activo como fallback
                try:
                    fallback_response = supabase_client.table('restaurantes')\
                        .select('id, nombre, config, menu, info_json')\
                        .eq('estado', 'activo')\
                        .limit(1)\
                        .execute()
                    
                    if fallback_response.data:
                        restaurant_config = fallback_response.data[0]
                        restaurant_config['nombre_restaurante'] = restaurant_config.get('nombre')
                        
                        # Asegurar configuración de Twilio
                        restaurant_config['config'] = {
                            'twilio_account_sid': TWILIO_ACCOUNT_SID,
                            'twilio_auth_token': TWILIO_AUTH_TOKEN,
                            'twilio_phone_number': TWILIO_WHATSAPP_NUMBER
                        }
                        
                        logger.info(f"✅ Usando restaurante fallback: {restaurant_config.get('nombre')} (ID: {restaurant_config.get('id')})")
                    else:
                        # Si no hay restaurantes, crear config mínima
                        restaurant_config = {
                            'id': 'sandbox-default',
                            'nombre': DEFAULT_RESTAURANT_NAME or 'Restaurante Demo',
                            'nombre_restaurante': DEFAULT_RESTAURANT_NAME or 'Restaurante Demo',
                            'config': {
                                'twilio_account_sid': TWILIO_ACCOUNT_SID,
                                'twilio_auth_token': TWILIO_AUTH_TOKEN,
                                'twilio_phone_number': TWILIO_WHATSAPP_NUMBER
                            },
                            'info_json': {
                                'contact': {
                                    'phone': '11-6668-6255',
                                    'whatsapp': '+5491166686255'
                                }
                            }
                        }
                        logger.info("✅ Usando configuración mínima de sandbox")
                        
                except Exception as fallback_error:
                    logger.error(f"Error buscando restaurante fallback: {str(fallback_error)}")
                    response.message("Lo sentimos, este servicio no está disponible actualmente para este número. Por favor, contacta al administrador.")
                    return str(response)
                
            if not restaurant_config:
                logger.error(f"No se pudo obtener la configuración para el número de Twilio: {twilio_to_number}")
                response.message("Lo sentimos, este servicio no está disponible actualmente para este número. Por favor, contacta al administrador.")
                return str(response)

            # Validación adicional de la configuración
            required_config = ['id', 'config', 'info_json']
            if not all(key in restaurant_config for key in required_config):
                missing_fields = [key for key in required_config if key not in restaurant_config]
                logger.error(f"Configuración de restaurante incompleta. Faltan campos: {missing_fields}")
                response.message("Error de configuración del sistema. Por favor, contacta al administrador.")
                return str(response)
        except Exception as e:
            logger.error(f"Error al obtener o validar la configuración del restaurante: {str(e)}")
            logger.error(traceback.format_exc())
            response.message("Ocurrió un error procesando tu mensaje. Por favor, intenta nuevamente más tarde.")
            return str(response)

        logger.info(f"Procesando mensaje para el restaurante: {restaurant_config.get('nombre_restaurante')} (ID: {restaurant_config.get('id')})")
        
        # El restaurant_id será necesario para la gestión de sesiones y otras lógicas específicas
        restaurant_id = restaurant_config.get('id')
        
        # Verificar si es una solicitud de reinicio/reset - PRIORIDAD MÁXIMA
        reset_commands = [
            "reset", "reiniciar", "refresh", "reinicio", "comenzar de nuevo", 
            "empezar de nuevo", "borrar", "limpiar", "salir", "0", "restart",
            "nuevo", "start", "inicio", "empezar", "comenzar", "clear"
        ]
        is_reset_request = incoming_msg.strip().lower() in reset_commands
        
        if is_reset_request:
            try:
                logger.info(f"🔄 COMANDO DE REINICIO DETECTADO: '{incoming_msg}' de {sender} para restaurante {restaurant_id}")
                
                # Importar función de reset
                from services.twilio.reminder_handler import reset_user_session 
                from utils.session_manager import clear_session
                
                # Limpiar sesión completamente
                clear_session(sender, restaurant_id)
                logger.info(f"Sesión limpiada para {sender} en R:{restaurant_id}")
                
                # Enviar mensaje de reinicio exitoso
                restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
                reset_message = f"""🔄 *Sesión reiniciada exitosamente*

¡Hola! Tu sesión con {restaurant_name} ha sido completamente reiniciada. 

¿Cómo podemos ayudarte hoy?

Escribí:
➡️ *Reservar* - para hacer una reserva
➡️ *Menu* - para ver nuestro menú  
➡️ *Ubicacion* - para saber dónde encontrarnos
➡️ *Hola* - para iniciar una conversación"""
                
                response.message(reset_message)
                logger.info(f"✅ Reinicio exitoso para {sender} en R:{restaurant_id}")
                return str(response)
                
            except Exception as e:
                logger.error(f"❌ Error al reiniciar sesión para {restaurant_id}: {str(e)}")
                logger.error(traceback.format_exc())
                response.message("Lo sentimos, ocurrió un error al reiniciar la sesión. Por favor, intenta nuevamente.")
                return str(response)

        # Verificar si es una respuesta a un recordatorio
        try:
            from services.twilio.reminder_handler import get_user_session_data, handle_reminder_response
            logger.info(f"🔍 DEBUG: Verificando recordatorio para {sender} en restaurante {restaurant_id}")
            
            reminder_data = get_user_session_data(sender, restaurant_id)
            logger.info(f"🔍 DEBUG: reminder_data obtenido: {reminder_data}")
            
            if reminder_data:
                logger.info(f"🔍 DEBUG: reminder_data encontrado - is_reminder: {reminder_data.get('is_reminder')}, completed_at: {reminder_data.get('completed_at')}")
                
                if reminder_data.get('is_reminder') and not reminder_data.get('completed_at'):
                    logger.info(f"🔔 Detectada respuesta a recordatorio activo de {sender} para restaurante {restaurant_id}")
                    logger.info(f"🔔 Mensaje recibido: '{incoming_msg}'")
                    
                    # Procesar la respuesta directamente aquí
                    try:
                        result = handle_reminder_response(incoming_msg, sender, restaurant_config)
                        logger.info(f"✅ Respuesta de recordatorio procesada: {result}")
                        return str(response)  # Retornar respuesta vacía ya que handle_reminder_response envía el mensaje
                    except Exception as reminder_error:
                        logger.error(f"❌ Error procesando respuesta de recordatorio: {str(reminder_error)}")
                        logger.error(traceback.format_exc())
                        response.message("Lo sentimos, hubo un error procesando tu respuesta. Por favor contacta al restaurante directamente.")
                        return str(response)
                else:
                    logger.info(f"🔍 DEBUG: reminder_data encontrado pero no es activo - is_reminder: {reminder_data.get('is_reminder')}, completed_at: {reminder_data.get('completed_at')}")
            else:
                logger.info(f"🔍 DEBUG: No se encontró reminder_data para {sender} en restaurante {restaurant_id}")
        except Exception as e:
            logger.error(f"Error al verificar recordatorio: {str(e)}")
            logger.error(traceback.format_exc())

        # Si no es respuesta a recordatorio o el recordatorio ya fue completado, continuar con el flujo normal
        
        # Normalizar el mensaje para verificaciones
        normalized_msg = incoming_msg.strip().lower()
        logger.info(f"Mensaje normalizado para verificación: '{normalized_msg}'")

        # Obtener la sesión actual si existe
        try:
            session = get_session(sender, restaurant_id)
            current_step = session.get('current_step') if session else None
            logger.info(f"Paso actual de la sesión para {restaurant_id}: {current_step}")
        except Exception as e:
            logger.error(f"Error al obtener sesión: {str(e)}")
            logger.error(traceback.format_exc())
            session = None
            current_step = None

        # Procesar el mensaje con el handler
        try:
            handler_result_message = handle_whatsapp_message(incoming_msg, sender, restaurant_config, message_sid)
            logger.info(f"Resultado del handler: {handler_result_message}")
            
            # Solo enviar respuesta TwiML si el handler retorna un mensaje específico
            # Si retorna None, significa que el mensaje ya fue enviado directamente por el handler
            if handler_result_message:
                response.message(handler_result_message)
                logger.info(f"Enviando respuesta TwiML: {handler_result_message}")
            elif session and session.get('error'):
                # Si hay un error específico en la sesión, usarlo
                error_msg = session.get('error')
                logger.warning(f"Error recuperado de la sesión: {error_msg}")
                response.message(error_msg)
            else:
                # Si handler_result_message es None, el mensaje ya fue enviado directamente
                # No enviar mensaje adicional para evitar duplicados
                logger.info("Handler retornó None - mensaje ya enviado directamente, no enviando respuesta TwiML adicional")
            return str(response)
        except Exception as e:
            logger.error(f"Error en handle_whatsapp_message: {str(e)}")
            logger.error(traceback.format_exc())
            # Obtener número de contacto del restaurante para el mensaje de error
            try:
                contact_phone = restaurant_config.get('info_json', {}).get('contact', {}).get('phone', '116-6668-6255')
                response.message(f"Lo sentimos, ocurrió un error al procesar tu mensaje. Por favor, contacta al {contact_phone} o intenta nuevamente en unos minutos.")
            except:
                response.message("Lo sentimos, ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente en unos minutos.")
            return str(response)

    except Exception as e:
        logger.error(f"Error general en webhook de Twilio: {str(e)}")
        logger.error(traceback.format_exc())
        final_response = MessagingResponse()
        final_response.message("Ocurrió un error inesperado. Por favor, intenta más tarde.")
        return str(final_response)

@twilio_bp.route('/menu', methods=['GET'])
def get_menu():
    """Endpoint para obtener el menú del restaurante para uso en WhatsApp"""
    try:
        # Ruta absoluta al archivo de menú
        menu_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'menu.json')
        logger.info(f"Intentando leer menú desde: {menu_path}")
        
        # Verificar si el archivo existe
        if not os.path.exists(menu_path):
            logger.error(f"Archivo de menú no encontrado en: {menu_path}")
            return jsonify({"error": "Archivo de menú no encontrado"}), 404
        
        # Leer el archivo JSON
        with open(menu_path, 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        # Extraer platos de muestra de diferentes días
        sample_dishes = []
        for day, meals in menu_data.get("dias_semana", {}).items():
            if isinstance(meals, dict):
                if "almuerzo" in meals and isinstance(meals["almuerzo"], list):
                    for dish in meals["almuerzo"]:
                        if isinstance(dish, dict) and "name" in dish:
                            sample_dishes.append(dish["name"])
                if "cena" in meals and isinstance(meals["cena"], list):
                    for dish in meals["cena"]:
                        if isinstance(dish, dict) and "name" in dish:
                            sample_dishes.append(dish["name"])
        
        # Eliminar duplicados y limitar a 10 platos
        import random
        sample_dishes = list(set(sample_dishes))
        if len(sample_dishes) > 10:
            sample_dishes = random.sample(sample_dishes, 10)
        
        # Verificar menú para celíacos
        has_celiaco = "menu_especial" in menu_data and "celiaco" in menu_data["menu_especial"]
        celiaco_dishes = []
        celiaco_nota = ""
        
        if has_celiaco:
            celiaco_dishes = menu_data["menu_especial"]["celiaco"].get("platos_principales", [])[:3]
            celiaco_nota = menu_data["menu_especial"]["celiaco"].get("nota", "")
        
        return jsonify({
            "success": True,
            "sample_dishes": sample_dishes,
            "celiaco_dishes": celiaco_dishes,
            "celiaco_nota": celiaco_nota
        })
    except Exception as e:
        logger.error(f"Error al obtener menú: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500