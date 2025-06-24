from datetime import datetime
from db.supabase_client import supabase
from services.reservas.db import actualizar_estado_reserva as _actualizar_estado_reserva
from services.reservas.core import registrar_reserva as _registrar_reserva
from services.reservas.validacion import (
    validar_reserva, validar_paso_reserva, verificar_capacidad_disponible as _verificar_capacidad_disponible
)

def registrar_reserva(data, supabase=None):
    """
    Registra una reserva en Supabase y envía confirmaciones.
    
    Args:
        data: Diccionario con los datos de la reserva
        supabase: Cliente de Supabase (opcional)
    
    Returns:
        Diccionario con el resultado de la operación
    """
    return _registrar_reserva(data, supabase)

def actualizar_estado_reserva(reserva_id, nuevo_estado):
    """
    Actualiza el estado de una reserva
    
    Args:
        reserva_id: ID de la reserva a actualizar
        nuevo_estado: Nuevo estado ('Confirmada', 'Cancelada', etc.)
    
    Returns:
        Diccionario con el resultado de la operación
    """
    return _actualizar_estado_reserva(reserva_id, nuevo_estado)

def validar_disponibilidad_horaria(fecha_str, hora_str, restaurant_config):
    """
    Valida si el horario de la reserva está dentro de los horarios de atención.
    
    Args:
        fecha_str: Fecha en formato DD/MM/YYYY
        hora_str: Hora en formato HH:MM
        restaurant_config: Configuración del restaurante
    
    Returns:
        tuple (bool, str): (es_valida, mensaje_error)
    """
    fecha_actual = datetime.now()
    try:
        # Validar fecha
        valida_fecha, msg_fecha = validar_paso_reserva('fecha', fecha_str, fecha_actual)
        if not valida_fecha:
            return False, msg_fecha
            
        # Validar hora
        return validar_paso_reserva('hora', hora_str, fecha_actual)
    except Exception as e:
        return False, f"Error al validar disponibilidad: {str(e)}"

async def verificar_capacidad_disponible(fecha_str, personas, restaurant_config):
    """
    Verifica si hay capacidad disponible para la fecha y cantidad de personas.
    
    Args:
        fecha_str: Fecha en formato DD/MM/YYYY
        personas: Número de personas
        restaurant_config: Configuración del restaurante
        
    Returns:
        tuple (bool, str, int): (hay_capacidad, mensaje_error, capacidad_disponible)
    """
    return await _verificar_capacidad_disponible(fecha_str, personas, restaurant_config)