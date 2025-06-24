from datetime import datetime
from config import SUPABASE_ENABLED
from services.email_service import enviar_correo_confirmacion
from services.twilio.messaging import send_whatsapp_message
from .validacion import validar_reserva

def get_restaurant_config_by_id(restaurant_id, supabase=None):
    """
    Obtiene la configuración real del restaurante desde la base de datos
    """
    if not supabase:
        return None
    try:
        response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).single().execute()
        if response.data:
            return response.data
        return None
    except Exception as e:
        print(f"Error fetching restaurant config by ID {restaurant_id}: {e}")
        return None

def get_default_restaurant_config():
    """
    Obtiene una configuración por defecto para WhatsApp cuando no se proporciona restaurant_config
    """
    import os
    return {
        'config': {
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'twilio_phone_number': os.getenv('TWILIO_WHATSAPP_NUMBER')
        }
    }

def registrar_reserva(data, supabase=None):
    """
    Registra una reserva en Supabase y envía confirmaciones
    """
    try:
        # Validar datos requeridos
        required_fields = ['nombre', 'fecha', 'hora', 'personas', 'telefono', 'email']
        for field in required_fields:
            if field not in data:
                return {
                    "success": False,
                    "error": f"Falta el campo requerido: {field}",
                    "status_code": 400
                }
        
        # Convertir personas a entero si es string
        if isinstance(data.get('personas'), str):
            data['personas'] = int(data['personas'])
        
        # Normalizar formato de fecha (aceptar YYYY-MM-DD o DD/MM/YYYY)
        try:
            if '-' in data['fecha'] and len(data['fecha']) == 10:  # formato YYYY-MM-DD
                fecha_obj = datetime.strptime(data['fecha'], "%Y-%m-%d").date()
                data['fecha'] = fecha_obj.strftime("%d/%m/%Y")
            else:  # Intentar con el formato esperado DD/MM/YYYY
                # Validar el formato sin modificar el valor
                datetime.strptime(data['fecha'], "%d/%m/%Y").date()
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al registrar en base de datos: formato de fecha incorrecto. Use DD/MM/YYYY o YYYY-MM-DD",
                "status_code": 400
            }
        
        # Validar los datos antes de registrar
        es_valida, mensaje_error = validar_reserva(data)
        if not es_valida:
            return {
                "success": False,
                "error": mensaje_error,
                "message": f"No se pudo crear la reserva: {mensaje_error}",
                "status_code": 400
            }
        
        # Registrar en Supabase si está disponible
        reserva_id = None
        if SUPABASE_ENABLED and supabase:
            try:
                # Convertir la fecha al formato ISO
                fecha_obj = datetime.strptime(data['fecha'], "%d/%m/%Y").date()
                fecha_iso = fecha_obj.isoformat()
                
                # Crear un diccionario con los datos básicos requeridos usando los nombres de campos correctos para reservas_prod
                reserva_data = {
                    'nombre_cliente': data['nombre'],  # Mapear 'nombre' -> 'nombre_cliente'
                    'fecha': fecha_iso,
                    'hora': data['hora'],
                    'personas': data['personas'],
                    'telefono': data['telefono'],
                    'email': data['email'],
                    'comentarios': data.get('comentarios', ''),
                    'estado': 'Pendiente',  # Usar formato consistente 
                    'origen': data.get('origen', 'chatbot-web'),  # Agregar campo origen
                    'restaurante_id': data.get('restaurante_id')  # Incluir ID del restaurante
                }
                
                result = supabase.table('reservas_prod').insert(reserva_data).execute()
                
                # Obtener el ID de la reserva si está disponible
                if hasattr(result, 'data') and result.data and len(result.data) > 0:
                    reserva_id = result.data[0].get('id', 'N/A')
                else:
                    print(f"No se pudo extraer ID - data vacío o no existe")
            except Exception as e:
                print(f"Error al registrar reserva en Supabase: {str(e)}")
                return {
                    "success": False,
                    "error": f"Error al registrar en base de datos: {str(e)}",
                    "status_code": 500
                }
        
        # Enviar correo de confirmación
        email_sent = False
        restaurant_config = None
        
        # Obtener configuración real del restaurante si tenemos restaurant_id
        restaurant_id = data.get('restaurante_id')
        if restaurant_id and supabase:
            restaurant_config = get_restaurant_config_by_id(restaurant_id, supabase)
            if restaurant_config:
                print(f"✅ Configuración del restaurante obtenida: {restaurant_config.get('nombre', 'Sin nombre')}")
            else:
                print(f"⚠️ No se pudo obtener configuración para restaurant_id: {restaurant_id}")
        
        # Si no tenemos configuración real, usar configuración básica con credenciales de entorno
        if not restaurant_config:
            print("⚠️ Usando configuración por defecto con credenciales de entorno")
            restaurant_config = {
                'id': restaurant_id,
                'nombre': 'Gandolfo Restaurant', 
                'info_json': {
                    'contact': {
                        'email': 'gandolfo.restaurant@gmail.com',
                        'phone': '116-6668-6255'
                    },
                    'location': {
                        'address': 'Nuestra dirección'
                    },
                    'email_sending': {
                        'user': None,  # Usará EMAIL_USER de config
                        'password': None  # Usará EMAIL_PASSWORD de config
                    }
                }
            }
        
        # Asegurar que siempre haya configuración de email_sending
        if not restaurant_config.get('info_json', {}).get('email_sending'):
            if not restaurant_config.get('info_json'):
                restaurant_config['info_json'] = {}
            restaurant_config['info_json']['email_sending'] = {
                'user': None,  # Usará EMAIL_USER de config
                'password': None  # Usará EMAIL_PASSWORD de config
            }
        
        email_sent = enviar_correo_confirmacion(data, data['email'], restaurant_config)
        
        # Enviar confirmación por WhatsApp si hay teléfono
        whatsapp_sent = False
        if 'telefono' in data:
            phone = data['telefono']
            # Formatear el número para WhatsApp (agregar código de país si es necesario)
            phone = phone.replace(" ", "").replace("-", "")
            if not phone.startswith('+'):
                # Asumir que es un número de Argentina si no tiene código de país
                phone = f'+54{phone}' if not phone.startswith('54') else f'+{phone}'
            
            fecha_formateada = data['fecha']
            
            # Usar el nombre del restaurante de la configuración real
            restaurant_name = restaurant_config.get('nombre', 'Gandolfo Restaurant')
            contact_phone = restaurant_config.get('info_json', {}).get('contact', {}).get('phone', '116-6668-6255')
            
            whatsapp_message = f"""
¡Gracias por tu reserva en {restaurant_name}!

*Detalles de tu reserva:*
• Nombre: {data['nombre']}
• Fecha: {fecha_formateada}
• Hora: {data['hora']}
• Personas: {data['personas']}
• Teléfono: {data['telefono']}

Si necesitas modificar o cancelar tu reserva, por favor contáctanos al {contact_phone}.

¡Esperamos recibirte pronto!
{restaurant_name}
"""
            # Usar la configuración real del restaurante que ya tenemos
            whatsapp_sent = send_whatsapp_message(phone, whatsapp_message, restaurant_config)
        
        # Crear un mensaje de confirmación para el usuario
        confirmation_message = f"""
¡Reserva creada con éxito!

Tu reserva para {data['personas']} personas a nombre de {data['nombre']} ha sido confirmada para el {data['fecha']} a las {data['hora']}.
{f"ID de reserva: {reserva_id}" if reserva_id else ""}

Te hemos enviado un correo de confirmación a {data['email']}.
{f"También te hemos enviado un mensaje de WhatsApp al {data['telefono']}." if whatsapp_sent else ""}

¿Hay algo más en lo que pueda ayudarte?
"""
        
        return {
            "success": True,
            "email_sent": email_sent,
            "whatsapp_sent": whatsapp_sent,
            "message": confirmation_message,
            "reserva_id": reserva_id,
            "status_code": 200
        }
        
    except Exception as e:
        print(f"Error al procesar reserva: {str(e)}")
        return {
            "success": False,
            "error": f"Error al procesar reserva: {str(e)}",
            "status_code": 500
        }

def registrar_reserva_whatsapp(data, supabase=None):
    """
    Registra una reserva que viene desde WhatsApp
    """
    try:
        print(f"Iniciando registro de reserva desde WhatsApp con datos: {data}")
        
        # Validar datos mínimos necesarios
        if not data.get('nombre') or not data.get('fecha') or not data.get('hora') or not data.get('personas'):
            print(f"Datos incompletos para reserva WhatsApp: {data}")
            return {
                "success": False,
                "error": "Datos incompletos para la reserva",
                "status_code": 400
            }
        
        # Asegurarse de que la fecha tenga el formato correcto
        try:
            if '/' in data['fecha']:
                # Verificar si ya está en formato DD/MM/YYYY
                datetime.strptime(data['fecha'], "%d/%m/%Y")
            elif '-' in data['fecha']:
                # Convertir de YYYY-MM-DD a DD/MM/YYYY
                fecha_obj = datetime.strptime(data['fecha'], "%Y-%m-%d").date()
                data['fecha'] = fecha_obj.strftime("%d/%m/%Y")
            print(f"Fecha formateada: {data['fecha']}")
        except Exception as e:
            print(f"Error al formatear fecha WhatsApp: {str(e)}")
            # Intentar recuperar si es posible
            if len(data['fecha'].split('/')) == 3:
                pass  # Fecha ya está en formato correcto
            else:
                return {
                    "success": False,
                    "error": f"Formato de fecha incorrecto: {data['fecha']}",
                    "status_code": 400
                }
        
        # Si no hay email, usar uno genérico basado en el teléfono
        if 'email' not in data or not data['email']:
            phone_clean = data.get('telefono', '').replace('+', '').replace(' ', '')
            data['email'] = f"{phone_clean}@whatsapp.gandolfo.com"
        
        # Asegurarse de que personas sea un número
        if isinstance(data.get('personas'), str):
            try:
                data['personas'] = int(data['personas'])
            except ValueError:
                # Mantener como string si no se puede convertir
                pass
        
        # Marcar el origen como WhatsApp
        data['origen'] = 'whatsapp'
        
        # Verificar que Supabase esté disponible
        if not supabase:
            return {
                "success": False,
                "error": "Base de datos no disponible",
                "status_code": 500
            }
        
        # Usar la función general de registro
        result = registrar_reserva(data, supabase)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al procesar reserva de WhatsApp: {str(e)}",
            "status_code": 500
        }
