import requests
from datetime import datetime, timedelta
import re
import os
import json
from config import DEEPSEEK_API_KEY, DEFAULT_RESTAURANT_ID
from models.conversation import conversation_manager
from services.reservas_service import registrar_reserva
from db.supabase_client import get_supabase_client

def generate_restaurant_context(restaurant_config):
    """Genera el contexto completo del restaurante a partir de la configuración del restaurante."""
    if not restaurant_config or not isinstance(restaurant_config.get('info_json'), dict):
        print("ADVERTENCIA: No se pudo obtener información válida del restaurante desde restaurant_config")
        return "Información del restaurante no disponible."

    info_json = restaurant_config.get('info_json', {})
    restaurant_name = info_json.get('name', restaurant_config.get('nombre', 'Nuestro Restaurante'))

    context = f"Información General de {restaurant_name}\n"
    context += f"Nombre del Restaurante: {restaurant_name}\n"

    # Ubicación
    address = info_json.get('address', 'No especificada')
    reference_points = info_json.get('reference_points', [])
    parking = info_json.get('parking', '')

    context += f"Ubicación: {address}\n"
    if reference_points and isinstance(reference_points, list):
        context += "Puntos de referencia:\n"
        for punto in reference_points:
            context += f"- {punto}\n"
    if parking:
        context += f"Estacionamiento: {parking}\n"

    # Contacto
    phone = info_json.get('phone', 'No especificado')
    email = info_json.get('email', 'No especificado')
    context += f"Teléfono: {phone}\n"
    context += f"Correo Electrónico: {email}\n"

    # Horarios
    opening_hours = info_json.get('opening_hours')
    if opening_hours and isinstance(opening_hours, dict):
        context += "\nHorarios de Atención:\n"
        days_order = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        for day_key in days_order:
            if day_key in opening_hours:
                day_schedule = opening_hours[day_key]
                if isinstance(day_schedule, dict):
                    almuerzo_abre = day_schedule.get('almuerzo_abre', '')
                    almuerzo_cierra = day_schedule.get('almuerzo_cierra', '')
                    cena_abre = day_schedule.get('cena_abre', '')
                    cena_cierra = day_schedule.get('cena_cierra', '')
                    nota = day_schedule.get('nota', '')

                    day_name_es = day_key.capitalize()
                    schedule_parts = []
                    if almuerzo_abre != 'cerrado' and almuerzo_abre and almuerzo_cierra:
                        schedule_parts.append(f"Almuerzo: {almuerzo_abre} a {almuerzo_cierra}")
                    if cena_abre != 'cerrado' and cena_abre and cena_cierra:
                        schedule_parts.append(f"Cena: {cena_abre} a {cena_cierra}")
                    
                    if not schedule_parts and (almuerzo_abre == 'cerrado' and cena_abre == 'cerrado'):
                        schedule_str = "Cerrado"
                    elif not schedule_parts:
                        schedule_str = "Horario no especificado"
                    else:
                        schedule_str = ", ".join(schedule_parts)

                    context += f"- {day_name_es}: {schedule_str}"
                    if nota:
                        context += f" ({nota})"
                    context += "\n"
                elif isinstance(day_schedule, str):
                    context += f"- {day_key.capitalize()}: {day_schedule}\n"

    # Instrucciones para reserva
    context += "\nReservas\n"
    context += "Podés hacer tu reserva directamente por este chat.\n"
    context += "Se recomienda reservar con al menos 24 horas de anticipación, especialmente los fines de semana.\n"
    context += f"Para reservas de grupos grandes (+10 personas), es necesario contactar directamente al restaurante al {phone}.\n"
    
    return context

def format_opening_hours(opening_hours_data):
    """Formatea los horarios de apertura para las reglas de validación, desde info_json['opening_hours']."""
    if not opening_hours_data or not isinstance(opening_hours_data, dict):
        print("WARNING: No se encontraron datos de horarios válidos. Usando valores por defecto genéricos.")
        return """
           - Lunes a Sábado: Horario de almuerzo y cena (consultar específicamente).
           - Domingo: Horario de almuerzo (consultar específicamente).
           (Horarios exactos no disponibles en este momento.)
        """
    
    formatted_hours = ""
    days_order = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    
    for day_key in days_order:
        if day_key in opening_hours_data:
            day_schedule = opening_hours_data[day_key]
            day_name_es = day_key.capitalize()
            
            if isinstance(day_schedule, str) and day_schedule.lower() == 'cerrado':
                formatted_hours += f"           - {day_name_es}: Cerrado\n"
                continue

            if not isinstance(day_schedule, dict):
                formatted_hours += f"           - {day_name_es}: Horario no especificado\n"
                continue

            almuerzo_abre = day_schedule.get('almuerzo_abre', '')
            almuerzo_cierra = day_schedule.get('almuerzo_cierra', '')
            cena_abre = day_schedule.get('cena_abre', '')
            cena_cierra = day_schedule.get('cena_cierra', '')
            nota = day_schedule.get('nota', '')

            schedule_parts = []
            if almuerzo_abre and almuerzo_cierra and almuerzo_abre.lower() != 'cerrado':
                schedule_parts.append(f"Almuerzo: {almuerzo_abre}-{almuerzo_cierra}")
            if cena_abre and cena_cierra and cena_abre.lower() != 'cerrado':
                schedule_parts.append(f"Cena: {cena_abre}-{cena_cierra}")

            if not schedule_parts:
                schedule_str = "Cerrado (o no especificado)"
            else:
                schedule_str = ", ".join(schedule_parts)
            
            formatted_hours += f"           - {day_name_es}: {schedule_str}"
            if nota:
                formatted_hours += f" ({nota})"
            formatted_hours += "\n"
        else:
            formatted_hours += f"           - {day_key.capitalize()}: Horario no disponible\n"
            
    return formatted_hours

def call_deepseek_api(message, user_id, restaurant_id=None, restaurant_config=None):
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        if not restaurant_config and restaurant_id:
            print(f"call_deepseek_api: restaurant_config not provided, fetching for ID: {restaurant_id}")
            try:
                from routes.api_routes import get_restaurant_config_by_id
                restaurant_config = get_restaurant_config_by_id(restaurant_id)
                if restaurant_config:
                    print(f"Successfully fetched restaurant_config in call_deepseek_api for ID: {restaurant_id}")
                else:
                    print(f"Failed to fetch restaurant_config in call_deepseek_api for ID: {restaurant_id}, will proceed with defaults.")
            except ImportError:
                print("ImportError: Could not import get_restaurant_config_by_id from routes.api_routes. Proceeding without specific config.")
            except Exception as e:
                print(f"Error fetching restaurant_config in call_deepseek_api: {e}. Proceeding without specific config.")

        if not restaurant_config and DEFAULT_RESTAURANT_ID and not restaurant_id:
            print(f"call_deepseek_api: No specific restaurant_config, attempting to load default (ID: {DEFAULT_RESTAURANT_ID}).")
            try:
                from routes.api_routes import get_restaurant_config_by_id
                restaurant_config = get_restaurant_config_by_id(DEFAULT_RESTAURANT_ID)
                if restaurant_config:
                    restaurant_id = DEFAULT_RESTAURANT_ID
                    print(f"Successfully fetched default restaurant_config in call_deepseek_api: {restaurant_config.get('nombre')}")
                else:
                    print(f"Failed to fetch default restaurant_config in call_deepseek_api.")
            except ImportError:
                print("ImportError: Could not import get_restaurant_config_by_id for default config. Proceeding without specific config.")
            except Exception as e:
                print(f"Error fetching default restaurant_config in call_deepseek_api: {e}. Proceeding without specific config.")

        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        fecha_limite = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        
        conversation_manager.add_message(user_id, "user", message)
        current_step = conversation_manager.get_current_step(user_id)
        
        info_json = restaurant_config.get('info_json', {}) if restaurant_config else {}
        if not isinstance(info_json, dict):
            from app import DEFAULT_RESTAURANT_DATA
            info_json = DEFAULT_RESTAURANT_DATA

        opening_hours_text = format_opening_hours(info_json.get('opening_hours'))
        restaurant_context_text = generate_restaurant_context(restaurant_config)
        
        mensaje_lower = message.lower()

        context_prompt = f"""
        Eres la asistente virtual del restaurante con personalidad amable, cordial y un toque argentino.
        Nombre del restaurante: {info_json.get('name', 'Nuestro Restaurante')}
        
        TU PERSONALIDAD:
        {restaurant_context_text}
        
        INFORMACIÓN IMPORTANTE SOBRE FECHAS:
        - Hoy es {fecha_actual}
        - Solo aceptamos reservas hasta {fecha_limite}
        
        REGLAS IMPORTANTES PARA VALIDAR RESERVAS:
        1. FECHAS: Solo aceptar reservas desde hoy ({fecha_actual}) hasta {fecha_limite}. El formato debe ser DD/MM/YYYY.
        2. HORARIOS: 
{opening_hours_text}
        3. PERSONAS: Máximo 10 personas por reserva. Para grupos más grandes, indicar que deben llamar al {info_json.get('phone', 'nuestro teléfono principal')}.
        4. TELÉFONO: Debe ser un número válido argentino.
        5. EMAIL: Debe tener formato válido de correo electrónico.
        """

        api_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": context_prompt},
                *conversation_manager.get_messages(user_id)
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=api_payload)
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                assistant_response = response_data["choices"][0]["message"]["content"]
                conversation_manager.add_message(user_id, "assistant", assistant_response)
                
                reservation_data = conversation_manager.get_reservation_data(user_id)
                if reservation_data: 
                    if 'restaurant_id' not in reservation_data and restaurant_id:
                        reservation_data['restaurant_id'] = restaurant_id
                        conversation_manager.set_reservation_data(user_id, 'restaurant_id', restaurant_id)

                if user_id.startswith('whatsapp:'): 
                    if (len(reservation_data) >= 5 and 
                        'nombre' in reservation_data and 
                        'fecha' in reservation_data and 
                        'hora' in reservation_data and 
                        'personas' in reservation_data and 
                        'telefono' in reservation_data):
                        if 'email' not in reservation_data or not reservation_data['email']:
                            phone_clean = user_id.replace('whatsapp:', '').replace('+', '')
                            default_email = f"{phone_clean}@whatsapp.gandolfo.com"
                            reservation_data['email'] = default_email
                            conversation_manager.set_reservation_data(user_id, 'email', default_email)
                        print(f"Detectada reserva completa desde WhatsApp: {reservation_data}")
                return assistant_response
            else:
                return "Lo siento, no pude procesar tu solicitud en este momento (respuesta vacía de IA)."
        else:
            print(f"Error en la API de DeepSeek: {response.status_code} - {response.text}")
            return "Lo siento, hubo un problema al procesar tu solicitud (error de API)."
    
    except Exception as e:
        print(f"Error al llamar a DeepSeek API: {str(e)}")
        import traceback
        traceback.print_exc()
        return "Lo siento, ocurrió un error inesperado."

def send_message_to_user(user_id, message, restaurant_config=None): 
    if user_id.startswith('whatsapp:'):
        from services.twilio.messaging import send_whatsapp_message 
        
        if not restaurant_config:
            print(f"WARNING: send_message_to_user via WhatsApp for {user_id} called without restaurant_config. Attempting to load default.")
            if DEFAULT_RESTAURANT_ID:
                try:
                    from routes.api_routes import get_restaurant_config_by_id
                    restaurant_config = get_restaurant_config_by_id(DEFAULT_RESTAURANT_ID)
                    if not restaurant_config:
                        print(f"CRITICAL: Failed to load default restaurant_config for WhatsApp message to {user_id}.")
                        return "Error: No se pudo enviar el mensaje de WhatsApp debido a configuración faltante."
                except Exception as e:
                    print(f"CRITICAL: Error loading default restaurant_config for WhatsApp: {e}")
                    return "Error: No se pudo enviar el mensaje de WhatsApp debido a un error de configuración."
            else:
                print(f"CRITICAL: Cannot send WhatsApp to {user_id} without restaurant_config and no DEFAULT_RESTAURANT_ID set.")
                return "Error: No se pudo enviar el mensaje de WhatsApp debido a configuración faltante."

        phone = user_id.replace('whatsapp:', '')
        return send_whatsapp_message(phone, message, restaurant_config)
    
    print(f"Mensaje para {user_id} (no WhatsApp): {message}")
    return message

def process_reservation_confirmation(user_id, confirmation, reservation_data, restaurant_config=None):
    if 'restaurant_id' not in reservation_data:
        if restaurant_config and 'id' in restaurant_config:
            reservation_data['restaurant_id'] = restaurant_config['id']
        elif DEFAULT_RESTAURANT_ID:
             reservation_data['restaurant_id'] = DEFAULT_RESTAURANT_ID
        else:
            print("CRITICAL: restaurant_id missing in reservation_data and cannot be determined.")
            send_message_to_user(user_id, "Lo siento, hubo un error crítico al procesar tu reserva (falta ID de restaurante). Por favor, contacta directamente.", restaurant_config)
            return False

    if confirmation.lower() in ['sí', 'si', 'yes', 'confirmar', 'dale', 'bueno', 'ok', 'sipi']:
        response_text = "¡Excelente! Estoy creando tu reserva..."
        send_message_to_user(user_id, response_text, restaurant_config) 
        
        result = registrar_reserva(reservation_data) 

        if result["success"]:
            confirmation_message = result["message"]
            send_message_to_user(user_id, confirmation_message, restaurant_config) 
            conversation_manager.reset_conversation(user_id) 
            return True
        else:
            error_message = f"Lo siento, ha ocurrido un error al crear la reserva: {result.get('error', 'Error desconocido')}. Por favor, intentá de nuevo o contactanos directamente."
            send_message_to_user(user_id, error_message, restaurant_config) 
            return False
    else:
        send_message_to_user(user_id, "Entendido. Cancelaste la reserva. ¿Hay algo más en lo que pueda ayudarte?", restaurant_config) 
        conversation_manager.reset_conversation(user_id) 
        return False

def process_reservation_intent(intent_data, user_id=None, restaurant_config=None):
    if 'date' in intent_data and intent_data['date']:
        try:
            if '-' in intent_data['date'] and len(intent_data['date']) == 10:
                date_obj = datetime.strptime(intent_data['date'], '%Y-%m-%d')
                intent_data['date'] = date_obj.strftime('%d/%m/%Y')
        except Exception as e:
            print(f"Error formatting date: {str(e)}")
    
    reservation_data = {
        'nombre': intent_data.get('name', ''),
        'fecha': intent_data.get('date', ''),
        'hora': intent_data.get('time', ''),
        'personas': intent_data.get('people', 1),
        'telefono': intent_data.get('phone', ''),
        'email': intent_data.get('email', ''),
        'comentarios': intent_data.get('comments', '')
    }
    
    current_restaurant_id = None
    restaurant_display_name = 'el restaurante'
    if restaurant_config and 'id' in restaurant_config:
        current_restaurant_id = restaurant_config['id']
        reservation_data['restaurant_id'] = current_restaurant_id
        if isinstance(restaurant_config.get('info_json'), dict):
            restaurant_display_name = restaurant_config['info_json'].get('name', restaurant_config.get('nombre', 'el restaurante'))
    elif DEFAULT_RESTAURANT_ID:
        current_restaurant_id = DEFAULT_RESTAURANT_ID
        reservation_data['restaurant_id'] = current_restaurant_id

    required_fields = ['nombre', 'fecha', 'hora', 'personas', 'telefono']
    missing_fields = [field for field in required_fields if not reservation_data[field]]
    
    if missing_fields:
        return f"Faltan datos para completar la reserva: {', '.join(missing_fields)}"
    
    if user_id and user_id.startswith('whatsapp:') and not reservation_data.get('email'):
        phone_clean = user_id.replace('whatsapp:', '').replace('+', '')
        reservation_data['email'] = f"{phone_clean}@whatsapp.gandolfo.com"

    confirmation_prompt = f"""
    Por favor, confirma los siguientes datos de tu reserva para {restaurant_display_name}:
    
    • Nombre: {reservation_data['nombre']}
    • Fecha: {reservation_data['fecha']}
    • Hora: {reservation_data['hora']}
    • Personas: {reservation_data['personas']}
    • Teléfono: {reservation_data['telefono']}
    • Email: {reservation_data['email']}
    • Comentarios: {reservation_data['comentarios'] or 'Ninguno'}
    
    ¿Confirmas esta reserva? (responde 'sí' o 'no')
    """
    
    if user_id:
        conversation_manager.set_reservation_data(user_id, reservation_data) 
        conversation_manager.set_current_step(user_id, "confirmacion_reserva_intent")

    return confirmation_prompt