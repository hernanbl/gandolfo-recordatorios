from datetime import datetime, timedelta

def validar_paso_reserva(paso, valor, fecha_actual=None):
    """
    Valida un paso específico del proceso de reserva
    
    Args:
        paso (str): El paso a validar ('nombre', 'fecha', 'hora', 'personas', 'telefono', 'email')
        valor: El valor a validar
        fecha_actual (datetime, optional): Fecha actual para validaciones de fecha
        
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    try:
        if fecha_actual is None:
            fecha_actual = datetime.now()
            
        if paso == 'nombre':
            # Validar que el nombre tenga al menos 3 caracteres y contenga al menos un espacio
            if not valor or len(valor) < 3:
                return False, "Por favor ingresa un nombre válido con al menos 3 caracteres."
            if ' ' not in valor:
                return False, "Por favor ingresa tu nombre completo (nombre y apellido)."
            return True, ""
            
        elif paso == 'fecha':
            # Validar formato y validez de la fecha
            try:
                if '/' in valor:
                    dia, mes, anio = valor.split('/')
                    fecha_obj = datetime(int(anio), int(mes), int(dia))
                elif '-' in valor:
                    fecha_obj = datetime.strptime(valor, '%Y-%m-%d')
                else:
                    return False, "Formato de fecha inválido. Por favor usa DD/MM/YYYY."
                
                # Validar que la fecha no sea pasada
                if fecha_obj.date() < fecha_actual.date():
                    return False, "No se pueden hacer reservas para fechas pasadas."
                
                # Validar que la fecha no sea más de 30 días en el futuro
                limite = fecha_actual + timedelta(days=30)
                if fecha_obj.date() > limite.date():
                    return False, f"Solo aceptamos reservas hasta {limite.strftime('%d/%m/%Y')}."
                
                return True, ""
            except ValueError:
                return False, "La fecha proporcionada no existe en el calendario. Por favor verifica el día, mes y año."
                
        elif paso == 'hora':
            # Validar formato y validez de la hora
            try:
                if ':' in valor:
                    horas, minutos = valor.split(':')
                    horas = int(horas)
                    minutos = int(minutos)
                    
                    if horas < 0 or horas > 23:
                        return False, "La hora debe estar entre 00 y 23."
                    if minutos < 0 or minutos > 59:
                        return False, "Los minutos deben estar entre 00 y 59."
                    
                    # Validar horarios del restaurante (necesitaríamos la fecha para saber si es fin de semana)
                    # Por ahora validamos horarios generales
                    hora_num = horas + (minutos / 60)
                    if not ((12 <= hora_num < 16) or (19 <= hora_num < 24)):
                        return False, "Nuestros horarios son de 12:00 a 16:00 y de 19:00 a 00:00. Por favor elige un horario dentro de este rango."
                    
                    return True, ""
                else:
                    return False, "Formato de hora inválido. Por favor usa HH:MM."
            except ValueError:
                return False, "La hora proporcionada no es válida. Por favor usa el formato HH:MM."
                
        elif paso == 'personas':
            # Validar cantidad de personas
            try:
                num_personas = int(valor)
                if num_personas <= 0:
                    return False, "El número de personas debe ser mayor a 0."
                if num_personas > 10:
                    return False, "Para reservas de más de 10 personas, por favor llámanos al 116-6668-6255."
                return True, ""
            except ValueError:
                return False, "Por favor ingresa un número válido de personas."
                
        elif paso == 'telefono':
            # Validar formato básico de teléfono
            telefono_limpio = valor.replace(' ', '').replace('-', '').replace('+', '')
            if not telefono_limpio.isdigit() or len(telefono_limpio) < 8:
                return False, "Por favor ingresa un número de teléfono válido con al menos 8 dígitos."
            return True, ""
            
        elif paso == 'email':
            # Validar formato básico de email
            if '@' not in valor or '.' not in valor or len(valor.split('@')[0]) == 0:
                return False, "Por favor ingresa una dirección de correo electrónico válida."
            return True, ""
            
        else:
            # Paso desconocido
            return True, ""
            
    except Exception as e:
        print(f"Error al validar paso {paso}: {str(e)}")
        return False, f"Error al validar los datos: {str(e)}"

def validar_reserva(datos_reserva):
    """
    Valida los datos de una reserva antes de registrarla
    
    Args:
        datos_reserva (dict): Diccionario con los datos de la reserva
        
    Returns:
        tuple: (es_valida, mensaje_error)
    """
    try:
        # Validar fecha
        fecha = datos_reserva.get('fecha', '')
        if not fecha:
            return False, "La fecha es obligatoria"
        
        # Convertir formato DD/MM/YYYY a objeto datetime para validación
        try:
            if '/' in fecha:
                dia, mes, anio = fecha.split('/')
                fecha_obj = datetime(int(anio), int(mes), int(dia))
            elif '-' in fecha:
                # Formato YYYY-MM-DD
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                # Convertir al formato esperado DD/MM/YYYY
                datos_reserva['fecha'] = fecha_obj.strftime('%d/%m/%Y')
            else:
                return False, "Formato de fecha inválido. Use DD/MM/YYYY"
        except ValueError:
            return False, "La fecha proporcionada no es válida o no existe en el calendario"
        
        # Validar que la fecha no sea pasada
        hoy = datetime.now()
        if fecha_obj.date() < hoy.date():
            return False, "No se pueden hacer reservas para fechas pasadas"
        
        # Validar que la fecha no sea más de 30 días en el futuro
        limite = hoy + timedelta(days=30)
        if fecha_obj.date() > limite.date():
            return False, f"Solo aceptamos reservas hasta {limite.strftime('%d/%m/%Y')}"
        
        # Validar hora
        hora = datos_reserva.get('hora', '')
        if not hora:
            return False, "La hora es obligatoria"
        
        # Validar formato de hora
        try:
            if ':' in hora:
                horas, minutos = hora.split(':')
                horas = int(horas)
                minutos = int(minutos)
                
                if horas < 0 or horas > 23:
                    return False, "La hora debe estar entre 00 y 23"
                if minutos < 0 or minutos > 59:
                    return False, "Los minutos deben estar entre 00 y 59"
                
                # Formatear correctamente
                datos_reserva['hora'] = f"{horas:02d}:{minutos:02d}"
            else:
                return False, "Formato de hora inválido. Use HH:MM"
        except ValueError:
            return False, "La hora proporcionada no es válida"
        
        # Validar horarios de atención según día de la semana
        dia_semana = fecha_obj.weekday()  # 0=Lunes, 6=Domingo
        es_fin_de_semana = dia_semana >= 5  # Sábado o domingo
        
        hora_num = horas + (minutos / 60)
        
        if es_fin_de_semana:
            # Fines de semana: 12:00 a 16:00 y 19:00 a 00:00
            if not ((12 <= hora_num < 16) or (19 <= hora_num < 24)):
                return False, "Los fines de semana atendemos de 12:00 a 16:00 y de 19:00 a 00:00"
        else:
            # Días de semana
            # Almuerzo: 12:00 a 15:00
            # Cena: 19:00 a 23:30
            if not ((12 <= hora_num < 15) or (19 <= hora_num < 23.5)):
                return False, "De lunes a viernes atendemos de 12:00 a 15:00 y de 19:00 a 23:30"
        
        # Validar cantidad de personas
        personas = datos_reserva.get('personas', 0)
        try:
            personas = int(personas)
            if personas <= 0:
                return False, "El número de personas debe ser mayor a 0"
            if personas > 10:
                return False, "Para reservas de más de 10 personas, por favor llámanos al 116-6668-6255"
            
            # Actualizar el valor como entero
            datos_reserva['personas'] = personas
        except ValueError:
            return False, "El número de personas debe ser un número válido"
        
        # Validar teléfono
        telefono = datos_reserva.get('telefono', '')
        if not telefono:
            return False, "El teléfono es obligatorio"
        
        # Validar email
        email = datos_reserva.get('email', '')
        if not email:
            return False, "El email es obligatorio"
        
        if '@' not in email or '.' not in email:
            return False, "El email no tiene un formato válido"
        
        return True, ""
        
    except Exception as e:
        print(f"Error en validación de reserva: {str(e)}")
        return False, f"Error al validar la reserva: {str(e)}"
    
async def verificar_capacidad_disponible(fecha_str: str, personas: int, restaurant_config: dict):
    """
    Verifica si hay capacidad disponible para la fecha y cantidad de personas solicitada.
    Implementa fallbacks múltiples para obtener la configuración de capacidad.
    
    Args:
        fecha_str: Fecha en formato DD/MM/YYYY
        personas: Número de personas
        restaurant_config: Configuración del restaurante
        
    Returns:
        tuple (bool, str, int): (hay_capacidad, mensaje_error, capacidad_disponible)
    """
    try:
        from services.db.supabase import get_supabase_client
        
        restaurant_id = restaurant_config.get('id')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        
        if not restaurant_id:
            return False, "Error: No se pudo identificar el restaurante para verificar capacidad.", 0

        # Convertir la fecha al formato adecuado para consultas
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        fecha_iso = fecha_obj.isoformat()
        
        # Consultar reservas existentes para esa fecha y restaurante
        supabase = get_supabase_client()
        if not supabase:
            print(f"Error al verificar capacidad: Supabase client no disponible para R:{restaurant_id}")
            return True, "", 100  # Fallback para no bloquear el sistema

        # Consultar reservas confirmadas para esa fecha y restaurante  
        response = supabase.table("reservas_prod").select("personas").eq("fecha", fecha_iso).eq("restaurante_id", restaurant_id).eq("estado", "Confirmada").execute()
        
        # Calcular personas ya reservadas para esa fecha
        reservas_existentes = response.data
        personas_ya_reservadas = sum(r.get('personas', 0) for r in reservas_existentes)
        
        # Obtener la capacidad total del restaurante con fallbacks múltiples
        # Intentar obtener de info_json primero, luego de config como fallback
        capacidad_total = (restaurant_config.get('info_json', {}).get('capacity', {}).get('max_capacity') or
                          restaurant_config.get('config', {}).get('capacity', {}).get('max_capacity') or  
                          restaurant_config.get('capacity', {}).get('max_capacity'))

        if capacidad_total is None:
            print(f"Error: No se encontró la configuración de capacidad (max_capacity) para R:{restaurant_id}")
            print(f"restaurant_config disponible: {list(restaurant_config.keys())}")
            # Fallback con valor por defecto
            capacidad_total = 100
            print(f"Usando capacidad por defecto: {capacidad_total}")

        capacidad_disponible = capacidad_total - personas_ya_reservadas
        
        # Verificar si hay capacidad suficiente
        if personas > capacidad_disponible:
            return False, f"Lo siento, para esa fecha en {restaurant_name} solo tenemos capacidad para {capacidad_disponible} personas más. ¿Deseas modificar la cantidad de personas o elegir otra fecha?", capacidad_disponible
        
        return True, "", capacidad_disponible
        
    except ValueError as ve:
        print(f"Error de formato de fecha al verificar capacidad para R:{restaurant_id if 'restaurant_id' in locals() else 'UNKNOWN'}: {str(ve)}")
        return False, "El formato de fecha no es válido. Por favor, usa el formato DD/MM/YYYY.", 0
    except Exception as e:
        print(f"Error al verificar capacidad para R:{restaurant_id if 'restaurant_id' in locals() else 'UNKNOWN'}: {str(e)}")
        # Fallback: asumir capacidad disponible para no bloquear el sistema
        return True, "Hubo un inconveniente al verificar la capacidad, pero puedes intentar continuar.", 100