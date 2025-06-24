import os
import json
from datetime import datetime, date
from services.db.supabase import get_supabase_client

async def validar_fecha_reserva(fecha_str):
    """
    Valida que la fecha de reserva sea válida:
    - No puede ser una fecha pasada
    - No puede ser más de 30 días en el futuro
    
    Retorna (es_valida, mensaje_error)
    """
    try:
        # Convertir string a objeto date
        fecha_reserva = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        hoy = date.today()
        
        # Verificar que no sea fecha pasada
        if fecha_reserva < hoy:
            return False, "Lo siento, no puedo hacer reservas para fechas pasadas. Por favor, elige una fecha futura."
        
        # Verificar que no sea más de 30 días en el futuro
        dias_diferencia = (fecha_reserva - hoy).days
        if dias_diferencia > 30:
            return False, "Lo siento, solo aceptamos reservas con hasta 30 días de anticipación. Por favor, elige una fecha más cercana."
        
        return True, ""
    except ValueError:
        return False, "El formato de fecha no es válido. Por favor, usa el formato DD/MM/YYYY."

async def verificar_capacidad_disponible(fecha_str: str, personas: int, restaurant_config: dict):
    """
    Verifica si hay capacidad disponible para la fecha y cantidad de personas solicitada,
    específico para un restaurante.
    Retorna (hay_capacidad, mensaje_error, personas_disponibles)
    """
    try:
        restaurant_id = restaurant_config.get('id')
        restaurant_name = restaurant_config.get('nombre_restaurante', 'el restaurante')
        if not restaurant_id:
            # This should ideally not happen if restaurant_config is validated upstream
            return False, f"Error: No se pudo identificar el restaurante para verificar capacidad.", 0

        # Convertir la fecha al formato adecuado para consultas
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        fecha_iso = fecha_obj.isoformat()
        
        # Consultar reservas existentes para esa fecha y restaurante
        supabase = get_supabase_client()
        if not supabase:
            # Handle case where Supabase client is not available
            print(f"Error al verificar capacidad: Supabase client no disponible para R:{restaurant_id}")
            # Fallback: assume capacity to not block, but log error
            return True, "", 100 # Or some other default/configurable behavior

        response = supabase.table("reservas_prod").select("personas").eq("fecha", fecha_iso).eq("restaurante_id", restaurant_id).execute()
        
        # Calcular personas ya reservadas para esa fecha
        reservas_existentes = response.data
        personas_ya_reservadas = sum(r.get('personas', 0) for r in reservas_existentes)
        
        # Obtener la capacidad total del restaurante desde restaurant_config
        # Assuming capacity is stored like: restaurant_config['info_json']['capacity']['total']
        capacidad_total = restaurant_config.get('info_json', {}).get('capacity', {}).get('total')

        if capacidad_total is None:
            print(f"Advertencia: No se encontró 'info_json.capacity.total' en restaurant_config para R:{restaurant_id}. Usando default de 100.")
            capacidad_total = 100 # Default capacity if not found in config

        capacidad_disponible = capacidad_total - personas_ya_reservadas
        
        # Verificar si hay capacidad suficiente
        if personas > capacidad_disponible:
            return False, f"Lo siento, para esa fecha en {restaurant_name} solo tenemos capacidad para {capacidad_disponible} personas más. ¿Deseas modificar la cantidad de personas o elegir otra fecha?", capacidad_disponible
        
        return True, "", capacidad_disponible
    except ValueError as ve: # Specific error for date parsing
        print(f"Error de formato de fecha al verificar capacidad para R:{restaurant_id if 'restaurant_id' in locals() else 'UNKNOWN'}: {str(ve)}")
        return False, "El formato de fecha no es válido. Por favor, usa el formato DD/MM/YYYY.", 0
    except Exception as e:
        print(f"Error al verificar capacidad para R:{restaurant_id if 'restaurant_id' in locals() else 'UNKNOWN'}: {str(e)}")
        # Fallback: assume capacity to not block, but log error and inform user generically
        return True, "Hubo un inconveniente al verificar la capacidad, pero puedes intentar continuar.", 100 

async def procesar_solicitud_reserva(mensaje, datos_reserva, restaurant_config: dict):
    """
    Procesa una solicitud de reserva del usuario.
    """
    # Si el mensaje contiene información sobre la fecha
    if "fecha" in datos_reserva:
        fecha_str = datos_reserva["fecha"]
        fecha_valida, mensaje_error = await validar_fecha_reserva(fecha_str) # validar_fecha_reserva is generic
        
        if not fecha_valida:
            return mensaje_error
    
    # Si el mensaje contiene información sobre la cantidad de personas
    if "fecha" in datos_reserva and "personas" in datos_reserva:
        fecha_str = datos_reserva["fecha"]
        try:
            personas = int(datos_reserva["personas"])
        except ValueError:
            return "La cantidad de personas debe ser un número. ¿Cuántas personas serán?"

        # Validar que el número de personas sea válido
        if personas <= 0:
            return "El número de personas debe ser mayor a 0. ¿Cuántas personas serán?"
        
        # Verificar capacidad disponible usando la función refactorizada
        hay_capacidad, mensaje_error, _ = await verificar_capacidad_disponible(fecha_str, personas, restaurant_config)
        
        if not hay_capacidad:
            return mensaje_error
    
    # ... existing code ...