import logging
import traceback
import random
from datetime import datetime, timedelta
from config import SUPABASE_ENABLED
from db.supabase_client import supabase_client
from services.twilio.messaging import send_whatsapp_message
from utils.session_manager import get_session, save_session, delete_session
from utils.phone_utils import normalize_argentine_phone, get_phone_variants

logger = logging.getLogger(__name__)

# Helper function to safely access nested dictionary values
def _get_nested_value(data_dict, keys, default=None):
    temp_dict = data_dict
    for key in keys:
        if isinstance(temp_dict, dict):
            temp_dict = temp_dict.get(key)
        else:
            return default
    return temp_dict if temp_dict is not None else default

def handle_reminder_response(message: str, phone_number: str, restaurant_config: dict) -> str:
    """
    Procesa las respuestas a los recordatorios de WhatsApp.
    """
    try:
        restaurant_id = restaurant_config.get('id')
        if not restaurant_id:
            logger.error(f"handle_reminder_response: restaurant_id no encontrado en restaurant_config para {phone_number}.")
            send_whatsapp_message(phone_number, "Error: No se pudo identificar el restaurante. Por favor, contacte a soporte.", {})
            return "Error: Configuración de restaurante no válida"

        logger.info(f"🔄 RECIBIDO [{phone_number} R:{restaurant_id}]: '{message}'")
        
        contact_phone = _get_nested_value(restaurant_config, ['info_json', 'contact', 'phone'], 'nuestro número de contacto')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')

        reset_keywords = ["reset", "reiniciar", "refresh", "reinicio", "comenzar de nuevo", 
                          "empezar de nuevo", "borrar", "limpiar", "salir", "0", "menu", "menú", "inicio"]
        
        normalized_msg = message.strip().lower()
        if normalized_msg in reset_keywords:
            logger.info(f"🔄 Comando de REINICIO detectado en recordatorio para R:{restaurant_id}: '{message}'")
            result = reset_user_session(phone_number, restaurant_id, restaurant_config)
            return result
        
        reminder_data = get_user_session_data(phone_number, restaurant_id)
        
        if not reminder_data or not reminder_data.get('is_reminder'):
            logger.info(f"No hay datos de recordatorio activo para {phone_number} en R:{restaurant_id}")
            mensaje = f"""Lo sentimos, parece que estás respondiendo a un recordatorio expirado o inexistente para {restaurant_name}.

Si necesitas ayuda con tu reserva, por favor llámanos al {contact_phone}."""
            send_whatsapp_message(phone_number, mensaje, restaurant_config)
            return "Sin recordatorio activo"
            
        if is_conversation_completed(phone_number, restaurant_id):
            thank_words = ["gracias", "thanks", "thank", "ok", "perfecto", "genial", "excelente", "👍", "👌"]
            is_thanks = any(word in normalized_msg for word in thank_words)
            
            if is_thanks:
                logger.info(f"Agradecimiento detectado después de conversación completada para R:{restaurant_id}: '{message}'")
                respuestas_agradecimiento = [
                    "¡Gracias a vos! Que tengas un hermoso día. ✨",
                    "¡El placer es nuestro! Que tengas un excelente día. 😊",
                    "¡Gracias a vos por tu tiempo! Que disfrutes tu día. 🌟",
                    f"¡Muchas gracias por tu amabilidad! Esperamos verte pronto en {restaurant_name}. Que tengas un día maravilloso. 💫",
                    f"¡Gracias por tu mensaje! Esperamos verte pronto en {restaurant_name}. Que tengas un lindo día. 🌈"
                ]
                respuesta = random.choice(respuestas_agradecimiento)
                send_whatsapp_message(phone_number, respuesta, restaurant_config)
                return "Agradecimiento recibido después de completar"
            else:
                logger.info(f"Mensaje ignorado después de conversación completada para R:{restaurant_id}: '{message}'")
                return "Conversación ya completada"
        
        confirmar_palabras = ["1", "confirmar", "confirmo", "si", "sí", "s", "yes", "ok", "confirmado", "dale", "listo", "👍"]
        cancelar_palabras = ["2", "cancelar", "cancelo", "no", "n", "nop", "cancelado"]
        
        is_confirmar = normalized_msg == "1" or normalized_msg in confirmar_palabras
        is_cancelar = normalized_msg == "2" or normalized_msg in cancelar_palabras
        
        if not is_confirmar and not is_cancelar:
            if normalized_msg in reset_keywords:
                logger.info(f"🔄 Comando de REINICIO secundario detectado para R:{restaurant_id}: '{message}'")
                result = reset_user_session(phone_number, restaurant_id, restaurant_config)
                return result
                
            send_help_message(phone_number, restaurant_config)
            return "Instrucciones enviadas"
            
        if is_confirmar:
            logger.info(f"✅ Mensaje reconocido como CONFIRMACIÓN para R:{restaurant_id}: '{message}'")
            result = process_confirmation(phone_number, restaurant_id, restaurant_config)
            if "exitosamente" in result or "confirmada exitosamente" in result.lower():
                mark_conversation_completed(phone_number, restaurant_id, "confirmed")
            return result
            
        elif is_cancelar:
            logger.info(f"❌ Mensaje reconocido como CANCELACIÓN para R:{restaurant_id}: '{message}'")
            result = process_cancellation(phone_number, restaurant_id, restaurant_config)
            if "exitosamente" in result:
                mark_conversation_completed(phone_number, restaurant_id, "cancelled")
            return result

    except Exception as e:
        logger.error(f"Error procesando respuesta del recordatorio para R:{restaurant_id if 'restaurant_id' in locals() else 'UNKNOWN'}: {str(e)}")
        logger.error(traceback.format_exc())
        effective_contact_phone = contact_phone if 'contact_phone' in locals() else 'nuestro número de contacto'
        mensaje = f"Lo sentimos, ocurrió un error al procesar tu respuesta. Por favor, contáctanos al {effective_contact_phone}."
        send_whatsapp_message(phone_number, mensaje, restaurant_config if restaurant_config else {})
        return f"Error: {str(e)}"

def send_help_message(phone_number: str, restaurant_config: dict) -> str:
    """
    Envía un mensaje de ayuda cuando la respuesta no es clara.
    """
    try:
        mensaje = """Por favor, responde con:
1️⃣ para *CONFIRMAR* tu reserva
2️⃣ para *CANCELAR* tu reserva"""
        
        send_whatsapp_message(phone_number, mensaje, restaurant_config)
        return "Mensaje de ayuda enviado"
    except Exception as e:
        logger.error(f"Error enviando mensaje de ayuda: {str(e)}")
        return "Error al enviar mensaje de ayuda"

def get_user_session_data(phone_number: str, restaurant_id: str) -> dict:
    """
    Obtiene los datos de la sesión del usuario para el recordatorio enviado, específico del restaurante.
    """
    try:
        logger.info(f"🔍 DEBUG: Intentando obtener sesión para: {phone_number} en Restaurante ID: {restaurant_id}")
        
        phone_variants = get_phone_variants(phone_number)
        logger.info(f"🔍 DEBUG: Probando variantes de número: {phone_variants} para R:{restaurant_id}")
        
        for variant in phone_variants:
            logger.info(f"🔍 DEBUG: Probando variante: {variant}")
            session = get_session(variant, restaurant_id) 
            if session:
                logger.info(f"🔍 DEBUG: Sesión encontrada para variante: {variant} en R:{restaurant_id}")
                logger.info(f"🔍 DEBUG: Contenido completo de sesión: {session}")
                
                if 'reminder_data' in session:
                    logger.info(f"✅ DEBUG: reminder_data encontrado para {variant} en R:{restaurant_id}: {session['reminder_data']}")
                    return session['reminder_data']
                else:
                    logger.warning(f"⚠️ DEBUG: Sesión encontrada pero sin 'reminder_data' para {variant} en R:{restaurant_id}")
                    logger.warning(f"⚠️ DEBUG: Claves disponibles en sesión: {list(session.keys())}")
            else:
                logger.info(f"🔍 DEBUG: No se encontró sesión para variante: {variant}")
        
        logger.warning(f"❌ DEBUG: No se encontró sesión o 'reminder_data' para ninguna variante de {phone_number} en R:{restaurant_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener la sesión del usuario para R:{restaurant_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def mark_conversation_completed(phone_number: str, restaurant_id: str, status: str = "completed") -> bool:
    """
    Marca una conversación como completada para evitar respuestas innecesarias a mensajes subsiguientes.
    
    Args:
        phone_number (str): Número de teléfono del usuario
        restaurant_id (str): ID del restaurante
        status (str): Estado de la conversación (completed, confirmed, cancelled)
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        logger.info(f"Marcando conversación como {status} para {phone_number} en R:{restaurant_id}")
        
        current_session = get_session(phone_number, restaurant_id)
        if not current_session:
            current_session = {}

        if 'reminder_data' not in current_session:
            current_session['reminder_data'] = {}
            logger.info(f"Clave 'reminder_data' creada en sesión para {phone_number} R:{restaurant_id}")
        
        current_session['reminder_data']['conversation_status'] = status
        current_session['reminder_data']['completed_at'] = datetime.now().isoformat()
        current_session['reminder_data']['is_reminder'] = True

        save_session(phone_number, current_session, restaurant_id)
        logger.info(f"Sesión guardada con estado de conversación {status} para {phone_number} R:{restaurant_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error al marcar conversación como completada para R:{restaurant_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def is_conversation_completed(phone_number: str, restaurant_id: str) -> bool:
    """
    Verifica si una conversación ya ha sido completada (confirmada o cancelada) para un restaurante.
    """
    try:
        reminder_data_content = get_user_session_data(phone_number, restaurant_id)
        
        if not reminder_data_content:
            return False
            
        return 'conversation_status' in reminder_data_content and reminder_data_content['conversation_status'] in ['completed', 'confirmed', 'cancelled']
    except Exception as e:
        logger.error(f"Error al verificar estado de conversación para R:{restaurant_id}: {str(e)}")
        return False

def reset_user_session(phone_number: str, restaurant_id: str, restaurant_config: dict) -> str:
    """
    Reinicia la sesión del usuario para el restaurante especificado.
    Debería limpiar la sesión y quizás enviar un mensaje de reinicio.
    """
    logger.info(f"Iniciando reinicio de sesión para {phone_number} en R:{restaurant_id}")
    try:
        current_session = get_session(phone_number, restaurant_id)
        if current_session and 'reminder_data' in current_session:
            del current_session['reminder_data']
            save_session(phone_number, current_session, restaurant_id)
            logger.info(f"Datos de recordatorio eliminados de la sesión para {phone_number} R:{restaurant_id}")
        elif current_session:
            save_session(phone_number, current_session, restaurant_id)
        else:
            logger.info(f"No se encontró sesión existente para {phone_number} R:{restaurant_id} para limpiar reminder_data.")

        mark_conversation_completed(phone_number, restaurant_id, "reset")

        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        contact_phone = _get_nested_value(restaurant_config, ['info_json', 'contact', 'phone'], 'nuestro número de contacto')
        
        logger.info(f"Sesión reiniciada (o datos de recordatorio limpiados) para {phone_number} en R:{restaurant_id}")
        return f"Tu interacción anterior con {restaurant_name} ha sido reiniciada. Si deseas iniciar una nueva consulta o reserva, por favor envía 'hola'."

    except Exception as e:
        logger.error(f"Error al reiniciar la sesión para {phone_number} R:{restaurant_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Hubo un error al intentar reiniciar tu sesión. Por favor, intenta nuevamente o contacta a {contact_phone}."

def process_confirmation(phone_number: str, restaurant_id: str, restaurant_config: dict) -> str:
    """
    Procesa la confirmación de la reserva por parte del usuario.
    Debería actualizar el estado de la reserva en la base de datos.
    """
    logger.info(f"Procesando confirmación para {phone_number} en R:{restaurant_id}")
    contact_phone = _get_nested_value(restaurant_config, ['info_json', 'contact', 'phone'], 'nuestro número de contacto')
    restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
    
    try:
        reminder_data = get_user_session_data(phone_number, restaurant_id)
        if not reminder_data or 'reserva_id' not in reminder_data:
            logger.warning(f"No se encontró reserva_id en session_data para confirmación. Usuario: {phone_number}, R:{restaurant_id}")
            return f"No pudimos encontrar los detalles de tu reserva en {restaurant_name}. Por favor, contacta a {contact_phone} para confirmar."

        reserva_id = reminder_data['reserva_id']
        logger.info(f"Confirmando reserva ID: {reserva_id} para {phone_number} en R:{restaurant_id}")

        if SUPABASE_ENABLED:
            if supabase_client:
                update_data = {
                    'estado': 'Confirmada', 
                    'recordatorio_respondido': True,
                    'fecha_confirmacion': datetime.now().isoformat()
                }
                response = supabase_client.table('reservas_prod').update(update_data).eq('id', reserva_id).eq('restaurante_id', restaurant_id).execute()
                
                response = supabase_client.table('reservas_prod').update(update_data).eq('id', reserva_id).eq('restaurante_id', restaurant_id).execute()
                
                if not response.error:
                    logger.info(f"Reserva {reserva_id} actualizada a 'Confirmada' en Supabase para R:{restaurant_id}.")
                    mensaje_confirmacion = f"¡Gracias! Tu reserva en {restaurant_name} ha sido confirmada exitosamente. ¡Te esperamos!"
                    send_whatsapp_message(phone_number, mensaje_confirmacion, restaurant_config)
                    mark_conversation_completed(phone_number, restaurant_id, "confirmed")
                    return mensaje_confirmacion
                else:
                    logger.error(f"Error al actualizar reserva {reserva_id} en Supabase para R:{restaurant_id}: {response.error}")
                    mensaje_error = f"Hubo un problema al confirmar tu reserva en {restaurant_name}. Por favor, intenta nuevamente o contacta a {contact_phone}."
                    send_whatsapp_message(phone_number, mensaje_error, restaurant_config)
                    return mensaje_error
            else:
                logger.error("Supabase client no disponible para process_confirmation.")
                return f"No pudimos procesar tu confirmación en este momento debido a un error del sistema en {restaurant_name}. Por favor, contacta a {contact_phone}."
        else:
            logger.info(f"SUPABASE_ENABLED=False. Simulación de confirmación de reserva {reserva_id} para R:{restaurant_id}.")
            mark_conversation_completed(phone_number, restaurant_id, "confirmed")
            return f"¡Gracias! Tu reserva en {restaurant_name} ha sido confirmada (simulado). ¡Te esperamos!"

    except Exception as e:
        logger.error(f"Error al procesar confirmación para {phone_number} R:{restaurant_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Ocurrió un error al procesar tu confirmación para {restaurant_name}. Por favor, contacta a {contact_phone}."

def process_cancellation(phone_number: str, restaurant_id: str, restaurant_config: dict) -> str:
    """
    Procesa la cancelación de la reserva por parte del usuario.
    Debería actualizar el estado de la reserva en la base de datos.
    """
    logger.info(f"Procesando cancelación para {phone_number} en R:{restaurant_id}")
    contact_phone = _get_nested_value(restaurant_config, ['info_json', 'contact', 'phone'], 'nuestro número de contacto')
    restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')

    try:
        reminder_data = get_user_session_data(phone_number, restaurant_id)
        if not reminder_data or 'reserva_id' not in reminder_data:
            logger.warning(f"No se encontró reserva_id en session_data para cancelación. Usuario: {phone_number}, R:{restaurant_id}")
            return f"No pudimos encontrar los detalles de tu reserva en {restaurant_name}. Por favor, contacta a {contact_phone} para verificar."

        reserva_id = reminder_data['reserva_id']
        logger.info(f"Cancelando reserva ID: {reserva_id} para {phone_number} en R:{restaurant_id}")

        if SUPABASE_ENABLED:
            if supabase_client:
                update_data = {
                    'estado': 'Cancelada', 
                    'recordatorio_respondido': True,
                    'fecha_cancelacion': datetime.now().isoformat()
                }
                response = supabase_client.table('reservas_prod').update(update_data).eq('id', reserva_id).eq('restaurante_id', restaurant_id).execute()
                
                if not response.error:
                    logger.info(f"Reserva {reserva_id} actualizada a 'Cancelada' en Supabase para R:{restaurant_id}.")
                    mensaje_cancelacion = f"Tu reserva en {restaurant_name} ha sido cancelada exitosamente. Esperamos verte en otra ocasión."
                    send_whatsapp_message(phone_number, mensaje_cancelacion, restaurant_config)
                    mark_conversation_completed(phone_number, restaurant_id, "cancelled")
                    return mensaje_cancelacion
                else:
                    logger.error(f"Error al actualizar reserva {reserva_id} (cancelación) en Supabase para R:{restaurant_id}: {response.error}")
                    mensaje_error = f"Hubo un problema al cancelar tu reserva en {restaurant_name}. Por favor, intenta nuevamente o contacta a {contact_phone}."
                    send_whatsapp_message(phone_number, mensaje_error, restaurant_config)
                    return mensaje_error
            else:
                logger.error("Supabase client no disponible para process_cancellation.")
                return f"No pudimos procesar tu cancelación en este momento debido a un error del sistema en {restaurant_name}. Por favor, contacta a {contact_phone}."
        else:
            logger.info(f"SUPABASE_ENABLED=False. Simulación de cancelación de reserva {reserva_id} para R:{restaurant_id}.")
            mark_conversation_completed(phone_number, restaurant_id, "cancelled")
            return f"Tu reserva en {restaurant_name} ha sido cancelada (simulado). Esperamos verte en otra ocasión."

    except Exception as e:
        logger.error(f"Error al procesar cancelación para {phone_number} R:{restaurant_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Ocurrió un error al procesar tu cancelación para {restaurant_name}. Por favor, contacta a {contact_phone}."