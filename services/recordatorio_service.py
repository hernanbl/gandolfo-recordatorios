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
        
        # Normalizar número de teléfono a formato E.164 (ej. +54911...)
        # Eliminar espacios, guiones y paréntesis
        phone_clean = ''.join(filter(str.isdigit, reserva['telefono']))
        
        # Asegurar que el número comience con '+' y el código de país
        if not phone_clean.startswith('54'): # Asumiendo que todos los números son de Argentina
            phone_clean = '549' + phone_clean # Añadir +549 si no está presente (para móviles de Argentina)
        
        # Asegurar que el número tenga el prefijo '+'
        if not phone_clean.startswith('+'):
            phone_clean = '+' + phone_clean

        # Formato final para Twilio: whatsapp:+<número>
        to_number = f"whatsapp:{phone_clean}"
        
        session_data = {'reminder_data': reminder_data}
        logger.info(f"Guardando datos de sesión para recordatorio ID {reserva['id']}")
        
        # Obtener restaurant_id para la sesión
        restaurant_id = reserva.get('restaurante_id')
        if not restaurant_id:
            logger.error(f"Recordatorio para reserva {reserva['id']} no tiene restaurant_id - esto puede causar problemas")
            # Usar un valor por defecto para evitar que falle completamente
            restaurant_id = "default"
        
        # Guardar sesión para el número normalizado
        try:
            save_session(to_number, session_data, restaurant_id)
            logger.info(f"Sesión guardada para: {to_number} en restaurante: {restaurant_id}")
        except Exception as e:
            logger.error(f"Error guardando sesión para {to_number} en restaurante {restaurant_id}: {str(e)}")
        
        try:
            # Construir el diccionario de configuración del restaurante para la función de mensajería
            restaurant_config = {
                'id': reserva.get('restaurante_id', DEFAULT_RESTAURANT_ID),
                'nombre_restaurante': nombre_restaurante,
                'twilio_account_sid': config.TWILIO_ACCOUNT_SID,
                'twilio_auth_token': config.TWILIO_AUTH_TOKEN,
                'twilio_phone_number': config.TWILIO_WHATSAPP_NUMBER
            }

            # Usar la función centralizada para enviar mensajes
            result = send_whatsapp_message(
                to_number=to_number,
                message=mensaje,
                restaurant_config=restaurant_config
            )

            if not result:
                raise Exception("El envío de mensaje no retornó un SID.")

        except Exception as e:
            logger.error(f"Error al enviar mensaje a través de send_whatsapp_message: {str(e)}")
            logger.error(traceback.format_exc())
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