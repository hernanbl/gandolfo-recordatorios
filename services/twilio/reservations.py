from datetime import datetime, timedelta
import traceback
import logging

def handle_reservation_confirmation(phone_number, confirmed):
    """
    Maneja la respuesta de confirmación o cancelación de una reserva
    
    Args:
        phone_number (str): Número de teléfono que respondió
        confirmed (bool): True si confirmó, False si canceló
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Importar dependencias
        from services.reservas_service import buscar_reserva_por_telefono, actualizar_estado_reserva
        from services.twilio.messaging import send_whatsapp_message
        from services.db.supabase import get_supabase_client
        import logging
        
        logging.info(f"Procesando {'confirmación' if confirmed else 'cancelación'} para el número {phone_number}")
        
        # Normalizar el número de teléfono
        phone = phone_number.replace(' ', '').replace('-', '')
        if phone.startswith('whatsapp:'):
            phone = phone.replace('whatsapp:', '')
        
        # Asegurarse de que el número tenga formato correcto para la búsqueda
        if not phone.startswith('+'):
            phone = '+' + phone
            
        logging.info(f"Buscando reserva para el teléfono normalizado: {phone}")
            
        # Buscar la reserva
        reserva = buscar_reserva_por_telefono(phone)
        
        if not reserva:
            # Intentar con variantes del número
            if phone.startswith('+549'):
                # Probar con +54
                alt_phone = '+54' + phone[4:]
                logging.info(f"Intentando con número alternativo: {alt_phone}")
                reserva = buscar_reserva_por_telefono(alt_phone)
            elif phone.startswith('+54'):
                # Probar con +549
                alt_phone = '+549' + phone[3:]
                logging.info(f"Intentando con número alternativo: {alt_phone}")
                reserva = buscar_reserva_por_telefono(alt_phone)
        
        if not reserva:
            mensaje = "No encontramos una reserva asociada a este número de teléfono. Por favor, contacta directamente al restaurante al 116-6668-6255 si necesitas ayuda."
            send_whatsapp_message(phone_number, mensaje)
            logging.warning(f"No se encontró reserva para el número {phone_number}")
            return {"success": False, "message": "Reserva no encontrada"}
        
        # Verificar estado actual de la reserva para validar si se puede confirmar/cancelar
        estado_actual = reserva.get('estado', '').lower()
        estados_no_modificables = ['no asistió', 'completada']
        
        if estado_actual in estados_no_modificables:
            mensaje = f"Lo sentimos, no podemos modificar tu reserva porque ya está marcada como '{reserva.get('estado')}'. Para cualquier consulta, por favor contacta al restaurante al 116-6668-6255."
            send_whatsapp_message(phone_number, mensaje)
            logging.warning(f"No se puede modificar reserva en estado '{estado_actual}' para el número {phone_number}")
            return {"success": False, "message": f"Reserva en estado no modificable: {estado_actual}"}
        
        # Si se intenta confirmar una reserva ya cancelada
        if confirmed and estado_actual == 'cancelada':
            mensaje = "Lo sentimos, no podemos confirmar una reserva que ya ha sido cancelada. Por favor, llama al restaurante al 116-6668-6255 para hacer una nueva reserva."
            send_whatsapp_message(phone_number, mensaje)
            logging.warning(f"Intento de confirmar reserva cancelada para el número {phone_number}")
            return {"success": False, "message": "No se puede confirmar reserva cancelada"}
            
        # Si se intenta cancelar una reserva ya confirmada y es menos de 2 horas antes
        if not confirmed and estado_actual == 'confirmada':
            # Verificar si estamos a menos de 2 horas de la reserva
            try:
                from datetime import datetime
                
                fecha_reserva = reserva.get('fecha')
                hora_reserva = reserva.get('hora')
                
                if fecha_reserva and hora_reserva:
                    # Construir datetime de la reserva
                    fecha_hora_str = f"{fecha_reserva} {hora_reserva}"
                    fecha_hora_obj = None
                    
                    try:
                        fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M")
                    except:
                        try:
                            fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            logging.warning(f"No se pudo parsear la fecha/hora: {fecha_hora_str}")
                    
                    if fecha_hora_obj:
                        ahora = datetime.now()
                        delta = fecha_hora_obj - ahora
                        
                        # Si faltan menos de 2 horas, avisar pero permitir cancelar
                        if delta.total_seconds() < 7200:  # 2 horas en segundos
                            logging.info(f"Cancelación con menos de 2 horas de anticipación")
                            # Añadir mensaje de aviso pero permitir la cancelación
                            mensaje_aviso = "Ten en cuenta que estás cancelando con menos de 2 horas de anticipación."
                            send_whatsapp_message(phone_number, mensaje_aviso)
            except Exception as e:
                logging.error(f"Error al verificar tiempo para cancelación: {str(e)}")
            
        # Actualizar el estado de la reserva
        nuevo_estado = "Confirmada" if confirmed else "Cancelada"
        logging.info(f"Actualizando estado de reserva {reserva['id']} a {nuevo_estado}")
        
        resultado = actualizar_estado_reserva(reserva['id'], nuevo_estado)
        logging.info(f"Resultado de actualización de estado a {nuevo_estado}: {resultado}")
        
        # Verificar si la actualización fue exitosa
        if not resultado.get("success", False):
            logging.error(f"Error al actualizar estado: {resultado}")
            
            # Intentar nuevamente la actualización directamente con Supabase
            try:
                supabase = get_supabase_client()
                if supabase:
                    # Actualizar con la fecha de confirmación o cancelación
                    current_time = datetime.now().isoformat()
                    update_data = {
                        'estado': nuevo_estado,
                        'recordatorio_respondido': True
                    }
                    
                    if confirmed:
                        update_data['fecha_confirmacion'] = current_time
                    else:
                        update_data['fecha_cancelacion'] = current_time
                    
                    response = supabase.table('reservas_prod').update(update_data).eq('id', reserva['id']).execute()
                    logging.info(f"Reintento de actualización: {response}")
                    
                    if hasattr(response, 'data') and response.data and len(response.data) > 0:
                        resultado = {"success": True, "message": f"Estado actualizado a {nuevo_estado}"}
                        logging.info("Actualización exitosa en el reintento")
            except Exception as e:
                logging.error(f"Error en reintento de actualización: {str(e)}")
                logging.error(traceback.format_exc())
        
        if resultado.get("success", False):
            # Formatear la fecha para mostrar
            fecha_display = reserva['fecha']
            if '-' in fecha_display and len(fecha_display) == 10:
                # Convertir de YYYY-MM-DD a DD/MM/YYYY
                fecha_obj = datetime.strptime(fecha_display, "%Y-%m-%d")
                fecha_display = fecha_obj.strftime("%d/%m/%Y")
                
            if confirmed:
                mensaje = f"¡Gracias por confirmar tu reserva para el {fecha_display} a las {reserva['hora']}! Te esperamos en Gandolfo Restaurant."
            else:
                mensaje = f"Hemos cancelado tu reserva para el {fecha_display} a las {reserva['hora']}. Esperamos verte pronto en otra ocasión."
        else:
            mensaje = "Lo sentimos, ha ocurrido un error al procesar tu respuesta. Por favor, contacta directamente al restaurante al 116-6668-6255."
            
        # Enviar respuesta
        send_whatsapp_message(phone_number, mensaje)
        logging.info(f"Mensaje enviado: {mensaje}")
        
        return {"success": resultado.get("success", False), "message": mensaje, "reservation_id": reserva.get('id')}
        
    except Exception as e:
        error_msg = f"Error al procesar confirmación de reserva: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        
        # Intentar enviar mensaje de error
        try:
            from services.twilio.messaging import send_whatsapp_message
            send_whatsapp_message(phone_number, "Lo sentimos, ha ocurrido un error al procesar tu respuesta. Por favor, contacta directamente al restaurante al 116-6668-6255.")
        except Exception as msg_error:
            logging.error(f"Error al enviar mensaje de error: {str(msg_error)}")
            
        return {"success": False, "error": error_msg}

def send_reservation_reminder(reservation):
    """
    Envía un recordatorio de reserva por WhatsApp 24 horas antes
    
    Args:
        reservation: Diccionario con los datos de la reserva
    """
    try:
        from services.twilio.messaging import send_whatsapp_message
        
        # Verificar que la reserva tenga teléfono
        if not reservation.get('telefono'):
            print(f"No se puede enviar recordatorio: falta número de teléfono para reserva {reservation.get('id')}")
            return False
            
        # Formatear el mensaje de recordatorio
        message = f"""*Recordatorio de Reserva - Gandolfo Restó*

Hola {reservation.get('nombre')},

Te recordamos que tienes una reserva para mañana:

• *Fecha:* {reservation.get('fecha')}
• *Hora:* {reservation.get('hora')}
• *Personas:* {reservation.get('personas')}
• *Comentarios:* {reservation.get('comentarios', 'Ninguno')}

Por favor, confirma tu asistencia respondiendo con una de estas opciones:
*CONFIRMAR* - Para confirmar tu reserva
*CANCELAR* - Para cancelar tu reserva

¡Gracias y te esperamos!
"""
        
        # Enviar el mensaje
        phone = reservation.get('telefono').replace('+', '').replace(' ', '')
        if not phone.startswith('+'):
            # Si no tiene código de país, agregar el de Argentina
            if phone.startswith('549') or phone.startswith('54'):
                pass  # Ya tiene código de Argentina
            else:
                phone = '549' + phone
                
        print(f"Enviando recordatorio de reserva a {phone}")
        return send_whatsapp_message(phone, message)
        
    except Exception as e:
        print(f"Error al enviar recordatorio de reserva: {str(e)}")
        print(traceback.format_exc())
        return False

def check_upcoming_reservations():
    """
    Verifica las reservas próximas y envía recordatorios para las que son en 24 horas.
    Esta función debe ejecutarse periódicamente (por ejemplo, cada hora).
    
    Returns:
        dict: Resultado de la operación con contadores de éxito y error.
    """
    try:
        from config import SUPABASE_ENABLED, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        from services.db.supabase import get_supabase_client
        from datetime import datetime, timedelta
        from twilio.rest import Client
        
        # Inicializar contadores para seguimiento
        resultado = {
            "procesadas": 0,
            "exitosas": 0, 
            "fallidas": 0,
            "sin_telefono": 0
        }
        
        if not SUPABASE_ENABLED:
            logging.warning("Supabase no está habilitado, no se pueden procesar recordatorios")
            return resultado
            
        # Obtener cliente de Supabase
        supabase = get_supabase_client()
        if not supabase:
            logging.error("No se pudo obtener el cliente de Supabase")
            return resultado
        
        # Obtener cliente de Twilio
        try:
            twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        except Exception as e:
            logging.error(f"Error al inicializar cliente de Twilio: {str(e)}")
            return resultado
        
        # Calcular fechas para la búsqueda
        now = datetime.now()
        start_time = now + timedelta(hours=23)  # 23 horas desde ahora
        end_time = now + timedelta(hours=25)    # 25 horas desde ahora
        
        logging.info(f"Buscando reservas entre {start_time.strftime('%Y-%m-%d')} y {end_time.strftime('%Y-%m-%d')}")
        
        # Buscar reservas que:
        # 1. Estén dentro del rango de tiempo
        # 2. No estén canceladas ni completadas ni marcadas como no asistió
        # 3. No tengan recordatorio enviado
        # 4. Filtradas por restaurante activo
        try:
            # Obtener todos los restaurantes activos para procesar sus reservas
            restaurantes_response = supabase.table('restaurantes')\
                .select('id, nombre, config')\
                .eq('activo', True)\
                .execute()
            
            if not restaurantes_response.data:
                logging.info("No hay restaurantes activos configurados")
                return resultado
            
            # Procesar reservas para cada restaurante por separado
            all_reservas = []
            for restaurante in restaurantes_response.data:
                restaurant_id = restaurante.get('id')
                restaurant_name = restaurante.get('nombre', 'Sin nombre')
                
                logging.info(f"Procesando reservas para restaurante: {restaurant_name} (ID: {restaurant_id})")
                
                response = supabase.table('reservas_prod')\
                    .select('*')\
                    .lt('fecha', end_time.strftime('%Y-%m-%d'))\
                    .gte('fecha', start_time.strftime('%Y-%m-%d'))\
                    .not_.in_('estado', ['Cancelada', 'No asistió', 'Completada'])\
                    .eq('recordatorio_enviado', False)\
                    .eq('restaurante_id', restaurant_id)\
                    .execute()
                
                if response.data:
                    logging.info(f"Encontradas {len(response.data)} reservas para {restaurant_name}")
                    all_reservas.extend(response.data)
                else:
                    logging.info(f"No hay reservas próximas para {restaurant_name}")
            
            # Usar todas las reservas encontradas
            reservas = all_reservas
                
            if not reservas:
                logging.info("No hay reservas próximas para enviar recordatorios en ningún restaurante")
                return resultado
            logging.info(f"Encontradas {len(reservas)} reservas próximas para enviar recordatorios")
            resultado["procesadas"] = len(reservas)
            
            # Enviar recordatorios
            for reserva in reservas:
                try:
                    # Verificar que tenga teléfono
                    if not reserva.get('telefono'):
                        logging.warning(f"Reserva {reserva.get('id')} no tiene teléfono")
                        resultado["sin_telefono"] += 1
                        continue
                            
                    # Formatear fecha para mostrar
                    fecha_display = reserva['fecha']
                    if '-' in fecha_display and len(fecha_display) == 10:
                        fecha_obj = datetime.strptime(fecha_display, "%Y-%m-%d")
                        fecha_display = fecha_obj.strftime("%d/%m/%Y")
                    
                    # Formatear número de teléfono
                    phone = reserva.get('telefono').replace('+', '').replace(' ', '')
                    if not phone.startswith('+'):
                        if phone.startswith('549') or phone.startswith('54'):
                            phone = '+' + phone
                        else:
                            phone = '+549' + phone
                            
                    if not phone.startswith('whatsapp:'):
                        phone = f'whatsapp:{phone}'
                            
                    logging.info(f"Enviando recordatorio a {phone} para reserva {reserva.get('id')}")
                    
                    try:
                        # Preparar mensaje para envío
                        mensaje = f"""*¡Hola {reserva.get('nombre')}!* 👋

Te recordamos que tienes una reserva para mañana:

📅 *Fecha:* {fecha_display}
🕒 *Hora:* {reserva.get('hora')} hs
👥 *Personas:* {reserva.get('personas')}

Por favor, confirma tu asistencia usando los botones a continuación.

Si necesitas modificar tu reserva, por favor llámanos al 116-6668-6255.

¡Te esperamos en *Gandolfo Restó*! 🍽️✨"""
                        
                        # Verificar si hay plantilla de contenido disponible
                        from config import TWILIO_REMINDER_TEMPLATE_SID
                        
                        if TWILIO_REMINDER_TEMPLATE_SID:
                            # Usar el método moderno con plantillas de contenido
                            content_variables = {
                                "1": reserva.get('nombre'),  # Nombre del cliente
                                "2": fecha_display,         # Fecha formateada
                                "3": reserva.get('hora'),   # Hora de la reserva
                                "4": str(reserva.get('personas'))  # Cantidad de personas
                            }
                            
                            # Usar la función actualizada de messaging.py
                            message_sid = send_whatsapp_message(
                                phone,
                                mensaje,  # Se usará como fallback si la plantilla falla
                                content_sid=TWILIO_REMINDER_TEMPLATE_SID,
                                content_variables=content_variables
                            )
                        else:
                            # Usar el método legacy con persistent_action
                            message_sid = send_whatsapp_message(
                                phone, 
                                mensaje,
                                quick_replies=["CONFIRMAR", "CANCELAR"]
                            )
                        
                        logging.info(f"Mensaje enviado con SID: {message_sid}")
                        
                        logging.info(f"Mensaje enviado con SID: {message.sid}")
                        
                        # Marcar recordatorio como enviado con una sola operación
                        update_response = supabase.table('reservas_prod')\
                            .update({
                                'recordatorio_enviado': True,
                                'fecha_recordatorio': datetime.now().isoformat()
                            })\
                            .eq('id', reserva['id'])\
                            .execute()
                            
                        if hasattr(update_response, 'data') and update_response.data:
                            logging.info(f"Recordatorio marcado como enviado para reserva {reserva.get('id')}")
                            resultado["exitosas"] += 1
                        else:
                            logging.warning(f"No se pudo actualizar el estado de la reserva {reserva.get('id')}")
                            resultado["fallidas"] += 1
                        
                    except Exception as twilio_error:
                        logging.error(f"Error al enviar mensaje de Twilio: {str(twilio_error)}")
                        logging.error(traceback.format_exc())
                        resultado["fallidas"] += 1
                
                except Exception as e:
                    logging.error(f"Error al procesar recordatorio para reserva {reserva.get('id')}: {str(e)}")
                    logging.error(traceback.format_exc())
                    resultado["fallidas"] += 1
            
            return resultado
                
        except Exception as e:
            logging.error(f"Error al consultar reservas en Supabase: {str(e)}")
            logging.error(traceback.format_exc())
            return resultado
                
    except Exception as e:
        logging.error(f"Error general al verificar reservas próximas: {str(e)}")
        logging.error(traceback.format_exc())
        return {
            "procesadas": 0,
            "exitosas": 0,
            "fallidas": 0,
            "sin_telefono": 0,
            "error": str(e)
        }