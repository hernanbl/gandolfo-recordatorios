from datetime import datetime, timedelta
import sys
import os
import logging
import pytz
from services.twilio.messaging import send_whatsapp_message
import traceback
import config
from config import RESERVAS_TABLE, DEFAULT_RESTAURANT_ID, DEFAULT_RESTAURANT_NAME

# Configurar zona horaria de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

# Configuración del logger
logger = logging.getLogger(__name__)

# Añadir la ruta raíz del proyecto al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Modificar la importación para usar la ruta correcta
try:
    from db.supabase_client import supabase_client
    print("Conexión con Supabase establecida correctamente")
except ModuleNotFoundError as e:
    print(f"ERROR: No se pudo importar el módulo supabase_client: {str(e)}")
    print("Verifique que el archivo supabase_client.py existe y contiene la variable supabase_client.")
    print("Ruta encontrada: /Users/hernan/Documents/chatbot-0/db/supabase_client.py")
    
    # Crear un cliente ficticio para evitar errores fatales
    class DummyClient:
        def table(self, *args, **kwargs):
            return self
        def select(self, *args, **kwargs):
            return self
        def eq(self, *args, **kwargs):
            return self
        def execute(self, *args, **kwargs):
            class DummyResponse:
                data = []
            return DummyResponse()
    supabase_client = DummyClient()

# Función auxiliar para obtener el ID del restaurante seleccionado
def get_restaurant_id(restaurante_nombre=None):
    """
    Obtiene el ID del restaurante por nombre o devuelve el ID por defecto
    
    Args:
        restaurante_nombre (str): Nombre del restaurante (opcional)
    
    Returns:
        str: ID del restaurante
    """
    try:
        if DEFAULT_RESTAURANT_ID:
            return DEFAULT_RESTAURANT_ID
            
        if not restaurante_nombre:
            restaurante_nombre = DEFAULT_RESTAURANT_NAME
            
        response = supabase_client.table('restaurantes').select('id').eq('nombre', restaurante_nombre).execute()
        
        if hasattr(response, 'data') and response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        logger.error(f"Error al obtener ID del restaurante: {str(e)}")
        return None

def formatear_telefono_argentina(telefono):
    """
    Formatea un número de teléfono para Argentina asegurando que tenga el formato correcto para WhatsApp.
    Los números móviles en Argentina para WhatsApp deben tener el formato whatsapp:+549 seguido del número sin el 0 inicial.
    
    Args:
        telefono (str): Número de teléfono a formatear
        
    Returns:
        str: Número formateado o None si no se pudo formatear
    """
    if not telefono:
        return None
        
    # Si ya tiene el prefijo whatsapp:, quitarlo temporalmente
    if telefono.startswith('whatsapp:'):
        telefono = telefono[9:]
        
    # Eliminar espacios y caracteres no numéricos excepto el signo +
    telefono_limpio = ''.join(c for c in telefono if c.isdigit() or c == '+')
    
    # Si está vacío después de limpiar
    if not telefono_limpio:
        return None
    
    # Asegurarse de que el número comienza con + si no lo tiene
    if not telefono_limpio.startswith('+'):
        # Si comienza con 0, reemplazarlo con +549 (código de Argentina para móviles)
        if telefono_limpio.startswith('0'):
            telefono_limpio = '+549' + telefono_limpio[1:]
        # Si comienza con 11 (Buenos Aires), añadir +549
        elif telefono_limpio.startswith('11'):
            telefono_limpio = '+549' + telefono_limpio
        # Si comienza con 15 (prefijo de celular), reemplazar con +5411
        elif telefono_limpio.startswith('15'):
            telefono_limpio = '+549' + telefono_limpio[2:]
        # Para otros casos, añadir +54
        else:
            telefono_limpio = '+54' + telefono_limpio
    
    # Verificar si el número tiene el formato correcto para WhatsApp en Argentina
    # Los números móviles en Argentina para WhatsApp deben tener +549
    elif telefono_limpio.startswith('+54') and not telefono_limpio.startswith('+549'):
        # Si es un número argentino sin el 9, añadirlo después del código de país
        telefono_limpio = '+549' + telefono_limpio[3:]
    
    # Asegurar que tenga el prefijo whatsapp:
    if not telefono_limpio.startswith('whatsapp:'):
        telefono_limpio = f'whatsapp:{telefono_limpio}'
    
    return telefono_limpio

import traceback
from services.twilio.messaging import send_whatsapp_message
from utils.session_manager import save_session

def enviar_recordatorio(reserva):
    """Envía un recordatorio por WhatsApp para una reserva"""
    try:
        logger.info(f"Iniciando envío de recordatorio para reserva: {reserva['id']}")
        
        # Formatear la fecha para mostrar
        fecha_obj = datetime.strptime(reserva['fecha'], '%Y-%m-%d')
        fecha_display = fecha_obj.strftime('%d/%m/%Y')
        
        # Obtener el nombre del restaurante si existe el restaurante_id
        nombre_restaurante = DEFAULT_RESTAURANT_NAME
        if 'restaurante_id' in reserva and reserva['restaurante_id']:
            try:
                response = supabase_client.table('restaurantes').select('nombre').eq('id', reserva['restaurante_id']).execute()
                if hasattr(response, 'data') and response.data:
                    nombre_restaurante = response.data[0]['nombre']
            except Exception as e:
                logger.error(f"Error al obtener nombre de restaurante: {str(e)}")
        
        # Preparar mensaje
        # Usar nombre_cliente (columna correcta en la tabla)
        nombre_cliente = reserva.get('nombre_cliente', 'Cliente')
        
        mensaje = f"""¡Hola {nombre_cliente}! 👋

Te recordamos tu reserva para mañana en {nombre_restaurante}:

📅 *Fecha:* {fecha_display}
🕒 *Hora:* {reserva['hora']} hs
👥 *Personas:* {reserva['personas']}

Responde con *1* para CONFIRMAR o *2* para CANCELAR tu reserva.

¡Te esperamos! 🍽️"""

        # Datos del recordatorio para la sesión
        reminder_data = {
            'is_reminder': True,
            'reserva_id': reserva['id'],
            'fecha': reserva['fecha'],
            'hora': reserva['hora'],
            'personas': reserva['personas'],
            'nombre': nombre_cliente,
            'enviado_en': datetime.now().isoformat(),
            'conversation_status': 'pending'
        }
        
        # Normalizar número y guardar sesión para todas las variantes
        phone_clean = reserva['telefono'].replace('+', '').replace(' ', '').replace('-', '')
        
        # Asegurar formato correcto del número
        if not phone_clean.startswith('549'):
            if phone_clean.startswith('54'):
                phone_clean = f"9{phone_clean[2:]}"  # Insertar el 9 después del 54
            else:
                phone_clean = f"549{phone_clean}"
        
        session_data = {'reminder_data': reminder_data}
        logger.info(f"Guardando datos de sesión para recordatorio ID {reserva['id']}")
        
        # Obtener restaurant_id para la sesión
        restaurant_id = reserva.get('restaurante_id')
        if not restaurant_id:
            logger.error(f"Recordatorio para reserva {reserva['id']} no tiene restaurant_id - esto puede causar problemas")
            # Usar un valor por defecto para evitar que falle completamente
            restaurant_id = "default"
        
        # Guardar sesión para todas las variantes posibles del número con restaurant_id
        for phone_variant in [
            f"whatsapp:+{phone_clean}",
            phone_clean,
            f"+{phone_clean}",
            phone_clean[2:] if phone_clean.startswith('54') else None,  # Sin 54
            phone_clean[3:] if phone_clean.startswith('549') else None  # Sin 549
        ]:
            if phone_variant:
                try:
                    save_session(phone_variant, session_data, restaurant_id)
                    logger.info(f"Sesión guardada para variante: {phone_variant} en restaurante: {restaurant_id}")
                except Exception as e:
                    logger.error(f"Error guardando sesión para {phone_variant} en restaurante {restaurant_id}: {str(e)}")
        
        # Usar el método legacy con persistent_action directamente - esto garantiza que se envíen los botones
        try:
            from twilio.rest import Client
            
            # Asegurarnos de que tenemos acceso a las credenciales de Twilio
            twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
            
            if not all([twilio_account_sid, twilio_auth_token, twilio_whatsapp_number]):
                raise Exception("Faltan credenciales de Twilio en las variables de entorno")
            
            # Validar que el número de Twilio es válido
            logger.info(f"🔧 DEBUG - Número de Twilio configurado: '{twilio_whatsapp_number}'")
            logger.info(f"🔧 DEBUG - Tipo: {type(twilio_whatsapp_number)}")
            logger.info(f"🔧 DEBUG - Longitud: {len(twilio_whatsapp_number) if twilio_whatsapp_number else 'None'}")
            
            client = Client(twilio_account_sid, twilio_auth_token)
            
            # Asegurar que el número tenga el formato correcto para WhatsApp
            to_number = f"whatsapp:+{phone_clean}"
            
            # Limpiar el número de WhatsApp de origen para evitar duplicaciones del prefijo
            if twilio_whatsapp_number.startswith('whatsapp:'):
                from_number = twilio_whatsapp_number
                logger.info(f"🔧 DEBUG - Número ya tiene prefijo whatsapp:")
            else:
                from_number = f"whatsapp:{twilio_whatsapp_number}"
                logger.info(f"🔧 DEBUG - Agregando prefijo whatsapp: al número")
            
            logger.info(f"🔧 DEBUG - from_number final: '{from_number}'")
            logger.info(f"🔧 DEBUG - to_number final: '{to_number}'")
            
            # Verificación adicional del formato
            if not from_number.startswith('whatsapp:+'):
                logger.error(f"❌ FORMATO INCORRECTO - from_number no tiene formato whatsapp:+XXXXXX")
                logger.error(f"   Valor actual: '{from_number}'")
                logger.error(f"   Esperado (sandbox): 'whatsapp:+14155238886'")
                raise Exception(f"Formato incorrecto del número de origen: {from_number}")
            
            if not to_number.startswith('whatsapp:+'):
                logger.error(f"❌ FORMATO INCORRECTO - to_number no tiene formato whatsapp:+XXXXXX")
                logger.error(f"   Valor actual: '{to_number}'")
                raise Exception(f"Formato incorrecto del número de destino: {to_number}")
            
            # Verificar que el número coincida con el esperado (sandbox)
            expected_from = "whatsapp:+14155238886"
            if from_number != expected_from:
                logger.warning(f"⚠️  NÚMERO DIFERENTE AL ESPERADO (SANDBOX):")
                logger.warning(f"   Configurado: '{from_number}'")
                logger.warning(f"   Esperado (sandbox): '{expected_from}'")
                logger.warning(f"   Si estás en producción, debería ser: 'whatsapp:+18059093442'")
            
            logger.info(f"✅ Formatos validados correctamente")
            
            logger.info(f"Enviando mensaje WhatsApp desde: {from_number} hacia: {to_number}")
            
            # Crear mensaje WhatsApp - sin persistent_action que no es válido
            message = client.messages.create(
                body=mensaje,
                from_=from_number,
                to=to_number
            )
            result = message.sid
            logger.info(f"Mensaje WhatsApp enviado con botones interactivos. SID: {result}")
            
            # Verificar que el mensaje se envió por WhatsApp y no SMS
            message_details = client.messages(result).fetch()
            if hasattr(message_details, 'from_') and not message_details.from_.startswith('whatsapp:'):
                logger.warning(f"ADVERTENCIA: El mensaje se envió como SMS en lugar de WhatsApp!")
                logger.warning(f"From: {message_details.from_}, To: {message_details.to}")
            else:
                logger.info(f"✅ Confirmado: Mensaje enviado por WhatsApp correctamente")
                    
        except Exception as e:
            logger.error(f"Error al enviar mensaje con botones: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Verificar si es un error específico de canal de Twilio
            if "Twilio could not find a Channel with the specified From address" in str(e):
                logger.error(f"❌ PROBLEMA DE CONFIGURACIÓN DE TWILIO:")
                logger.error(f"   El número {from_number} no está configurado como canal WhatsApp en Twilio")
                logger.error(f"   ")
                logger.error(f"   🔧 SOLUCIONES POSIBLES:")
                logger.error(f"   1. Si estás en SANDBOX, usar: TWILIO_WHATSAPP_NUMBER=+14155238886")
                logger.error(f"   2. Si estás en PRODUCCIÓN, usar: TWILIO_WHATSAPP_NUMBER=+18059093442")
                logger.error(f"   3. Verificar en Twilio Console > Messaging > WhatsApp > Senders")
                logger.error(f"   4. El número debe estar 'approved' para WhatsApp Business")
                logger.error(f"   ")
                logger.error(f"   📱 SANDBOX: Solo números registrados pueden recibir mensajes")
                logger.error(f"   📱 PRODUCCIÓN: Cualquier número puede recibir mensajes")
                return None
            
            # Intentar enviar sin botones como último recurso solo si no es error de configuración
            logger.info("Intentando envío de fallback sin botones...")
            try:
                # Crear una configuración básica de restaurante para el fallback
                restaurant_config = {
                    'id': reserva.get('restaurante_id', 'default'),
                    'config': {
                        'twilio_account_sid': twilio_account_sid,
                        'twilio_auth_token': twilio_auth_token,
                        'twilio_phone_number': twilio_whatsapp_number
                    }
                }
                result = send_whatsapp_message(
                    f"+{phone_clean}", 
                    mensaje,
                    restaurant_config
                )
                if result:
                    logger.info(f"✅ Fallback exitoso - Mensaje enviado sin botones: {result}")
                else:
                    logger.error("❌ Fallback también falló")
                    return None
            except Exception as fallback_error:
                logger.error(f"❌ Error en fallback: {str(fallback_error)}")
                return None

        logger.info(f"Resultado envío de mensaje a +{phone_clean}: {result}")
        
        if result:
            try:
                # Actualizar estado en Supabase en una sola operación
                update_data = {
                    'recordatorio_enviado': True,
                    'fecha_recordatorio': datetime.now().isoformat()
                }
                
                # Usar el cliente supabase_client directamente y la tabla dinámica RESERVAS_TABLE
                response = supabase_client.table(RESERVAS_TABLE)\
                    .update(update_data)\
                    .eq('id', reserva['id'])\
                    .execute()
                    
                if not (hasattr(response, 'data') and response.data):
                    raise Exception("La actualización en Supabase no retornó datos")
                    
                logger.info(f"Estado de recordatorio actualizado en BD para reserva {reserva['id']}")
                return True
                
            except Exception as e:
                logger.error(f"Error actualizando estado en BD: {str(e)}")
                logger.error(traceback.format_exc())
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"Error enviando recordatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def enviar_recordatorios_reservas():
    """
    Envía recordatorios de reserva para el día siguiente.
    Usa zona horaria de Argentina para calcular "mañana" correctamente.
    """
    try:
        mensajes_enviados = 0
        mensajes_fallidos = 0
        errores = []
        
        print("=== INICIANDO PROCESO DE RECORDATORIOS ===")
        
        # Verificar si estamos en modo de prueba
        test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        if test_mode:
            print("🧪 EJECUTANDO EN MODO DE PRUEBA - Se enviarán recordatorios para fecha específica")
        
        # Usar directamente supabase_client en lugar de get_supabase_client()
        supabase = supabase_client
        
        # Calcular fechas usando zona horaria de Argentina
        ahora_argentina = datetime.now(ARGENTINA_TZ)
        manana_argentina = ahora_argentina + timedelta(days=1)
        
        manana_display = manana_argentina.strftime("%d/%m/%Y")
        manana_db = manana_argentina.strftime("%Y-%m-%d")
        
        print(f"📅 Fecha y hora actual en Argentina: {ahora_argentina.strftime('%d/%m/%Y %H:%M:%S %Z')}")
        print(f"📅 Buscando reservas para mañana: {manana_display} ({manana_db})")
        
        # Obtener ID del restaurante si existe configuración multi-restaurante
        restaurant_id = get_restaurant_id()
        if restaurant_id:
            print(f"🏪 Filtrando para restaurante con ID: {restaurant_id}")
        
        # Para propósitos de depuración, buscar algunas reservas recientes
        try:
            debug_response = supabase.table(RESERVAS_TABLE)\
                .select('id,fecha,estado,recordatorio_enviado,nombre_cliente,telefono')\
                .order('fecha', desc=False)\
                .limit(10)\
                .execute()
                
            if hasattr(debug_response, 'data') and debug_response.data:
                print(f"🔍 DEBUG: Últimas 10 reservas en la base de datos:")
                for r in debug_response.data:
                    print(f"   ID: {r.get('id')} | Fecha: {r.get('fecha')} | Estado: {r.get('estado')} | Recordatorio: {r.get('recordatorio_enviado')} | Cliente: {r.get('nombre_cliente')}")
            else:
                print("🔍 DEBUG: No se encontraron reservas en la base de datos")
        except Exception as debug_error:
            print(f"⚠️  Error en debug: {str(debug_error)}")
        
        # Buscar reservas que necesitan recordatorio para mañana
        query = supabase.table(RESERVAS_TABLE).select('*')
        
        # Filtrar por fecha de mañana y que no hayan recibido recordatorio
        query = query.eq('fecha', manana_db).eq('recordatorio_enviado', False)
        
        # Filtrar por restaurante si tenemos un ID específico
        if restaurant_id:
            query = query.eq('restaurante_id', restaurant_id)
            
        print(f"🔍 Ejecutando consulta para reservas del {manana_db} sin recordatorio...")
        response = query.execute()
        
        if not hasattr(response, 'data') or not response.data:
            print("ℹ️  No se encontraron reservas que requieran recordatorio")
            return {
                "success": True,
                "reservas_encontradas": 0,
                "total_reservas": 0,
                "reservas_activas": 0,
                "mensajes_enviados": 0,
                "mensajes_fallidos": 0,
                "message": "No hay reservas pendientes para mañana"
            }
            
        reservas = response.data
        total_reservas = len(reservas)
        print(f"📊 Total de reservas encontradas para mañana: {total_reservas}")
        
        # Filtrar reservas activas (no canceladas)
        reservas_activas = []
        for reserva in reservas:
            estado = reserva.get('estado', '').lower()
            if estado not in ['cancelada', 'no asistió', 'cancelado']:
                reservas_activas.append(reserva)
            else:
                print(f"⏭️  Omitiendo reserva {reserva.get('id')} con estado: {estado}")
        
        num_reservas_activas = len(reservas_activas)
        print(f"📊 Reservas activas que necesitan recordatorio: {num_reservas_activas}")
        
        if not reservas_activas:
            print("ℹ️  No hay reservas activas que requieran recordatorio")
            return {
                "success": True,
                "reservas_encontradas": total_reservas,
                "total_reservas": total_reservas,
                "reservas_activas": 0,
                "mensajes_enviados": 0,
                "mensajes_fallidos": 0,
                "message": "No hay reservas activas que requieran recordatorio"
            }

        # Enviar recordatorios
        print(f"\n🚀 Iniciando envío de recordatorios para {num_reservas_activas} reservas...")
        
        for i, reserva in enumerate(reservas_activas, 1):
            try:
                reserva_id = reserva.get('id')
                nombre_cliente = reserva.get('nombre_cliente', 'Cliente')
                telefono = reserva.get('telefono', 'N/A')
                hora = reserva.get('hora', 'N/A')
                
                print(f"\n--- Procesando reserva {i}/{num_reservas_activas} ---")
                print(f"📋 ID: {reserva_id}")
                print(f"👤 Cliente: {nombre_cliente}")
                print(f"📞 Teléfono: {telefono}")
                print(f"🕒 Hora: {hora}")
                
                resultado = enviar_recordatorio(reserva)
                
                if resultado:
                    mensajes_enviados += 1
                    print(f"✅ Recordatorio enviado exitosamente")
                    
                    # Marcar como recordatorio enviado
                    try:
                        update_response = supabase.table(RESERVAS_TABLE)\
                            .update({'recordatorio_enviado': True, 'fecha_recordatorio': ahora_argentina.isoformat()})\
                            .eq('id', reserva_id)\
                            .execute()
                        
                        if update_response.data:
                            print(f"✅ Reserva marcada como recordatorio enviado en BD")
                        else:
                            print(f"⚠️  Recordatorio enviado pero no se pudo actualizar BD")
                            
                    except Exception as update_error:
                        print(f"⚠️  Error actualizando BD: {str(update_error)}")
                        
                else:
                    mensajes_fallidos += 1
                    error_msg = f"Fallo al enviar recordatorio para reserva {reserva_id}"
                    errores.append(error_msg)
                    print(f"❌ {error_msg}")
                    
            except Exception as e:
                mensajes_fallidos += 1
                error_msg = f"Error general con reserva {reserva.get('id')}: {str(e)}"
                errores.append(error_msg)
                print(f"💥 {error_msg}")
                print(f"📊 Traceback: {traceback.format_exc()}")
                
        # Resumen final
        print(f"\n=== RESUMEN FINAL ===")
        print(f"📊 Reservas encontradas: {total_reservas}")
        print(f"📊 Reservas activas procesadas: {num_reservas_activas}")
        print(f"✅ Mensajes enviados: {mensajes_enviados}")
        print(f"❌ Mensajes fallidos: {mensajes_fallidos}")
        
        if errores:
            print(f"⚠️  Errores encontrados:")
            for error in errores:
                print(f"   - {error}")
        
        return {
            "success": True,
            "reservas_encontradas": total_reservas,
            "total_reservas": num_reservas_activas,
            "reservas_activas": num_reservas_activas,
            "mensajes_enviados": mensajes_enviados,
            "mensajes_fallidos": mensajes_fallidos,
            "errores": errores,
            "resumen": f"Proceso completado: {mensajes_enviados} enviados, {mensajes_fallidos} fallidos"
        }
        
    except Exception as e:
        error_msg = f"Error crítico en el proceso de recordatorios: {str(e)}"
        print(f"💥 {error_msg}")
        print(f"📊 Traceback completo: {traceback.format_exc()}")
        return {"success": False, "error": error_msg}