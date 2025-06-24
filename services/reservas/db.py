import os
import json
from datetime import datetime, timedelta
import traceback

def get_supabase_client():
    """
    Obtiene un cliente de Supabase configurado
    """
    try:
        from services.ai_service import get_supabase_client
        return get_supabase_client()
    except Exception as e:
        print(f"Error al obtener cliente Supabase: {str(e)}")
        return None

def obtener_reservas(supabase):
    """
    Obtiene todas las reservas de la tabla 'reservas' en Supabase
    """
    try:
        # Consultar la tabla 'reservas'
        response = supabase.table('reservas_prod').select('*').execute()
        
        # Verificar si hay datos
        if response.data:
            print(f"Se obtuvieron {len(response.data)} reservas de Supabase")
            return response.data
        else:
            print("No se encontraron reservas en Supabase")
            return []
        
    except Exception as e:
        print(f"Error al obtener reservas de Supabase: {str(e)}")
        return []

def obtener_reservas_proximas(fecha_inicio, fecha_fin, restaurant_id=None, limit=None, table_name='reservas'):
    """
    Obtiene las reservas programadas entre dos fechas
    
    Args:
        fecha_inicio: Fecha y hora de inicio (datetime)
        fecha_fin: Fecha y hora de fin (datetime)
        restaurant_id: ID del restaurante (opcional)
        limit: Número máximo de resultados (opcional)
        table_name: Nombre de la tabla a consultar (opcional, por defecto 'reservas')
    
    Returns:
        Lista de reservas en ese rango de fechas
    """
    try:
        # Intentar usar Supabase si está disponible
        try:
            from config import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                supabase = get_supabase_client()
                
                # Convertir fechas a formato ISO para la consulta
                fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
                fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
                
                # Iniciar la consulta
                query = supabase.table(table_name).select('*').gte('fecha', fecha_inicio_str).lte('fecha', fecha_fin_str).neq('estado', 'Cancelada')
                
                # Añadir filtro por restaurante si se proporciona un ID
                if restaurant_id:
                    # Determinar qué nombre de columna usar basado en la tabla
                    id_column = 'restaurante_id' if 'reservas_prod' in table_name else 'restaurant_id'
                    print(f"Using column {id_column} for table {table_name}")
                    query = query.eq(id_column, restaurant_id)
                
                # Limitar resultados si se especifica
                if limit and isinstance(limit, int):
                    query = query.limit(limit)
                
                # Ejecutar la consulta
                response = query.execute()
                
                if response.data:
                    return response.data
                return []
        except Exception as e:
            print(f"Error al buscar reservas próximas en Supabase: {str(e)}")
            
        # Fallback a archivo local
        import os
        import json
        
        # Path al archivo de reservas
        RESERVATIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'reservations.json')
        
        # Verificar si el archivo existe
        if not os.path.exists(RESERVATIONS_FILE):
            return []
            
        # Cargar reservas
        with open(RESERVATIONS_FILE, 'r') as f:
            reservas = json.load(f)
            
        # Filtrar reservas por fecha
        reservas_filtradas = []
        for reserva in reservas:
            if reserva.get('estado', '') == 'Cancelada':
                continue
                
            try:
                # Convertir fecha de la reserva a objeto datetime
                fecha_str = reserva.get('fecha', '')
                if '-' in fecha_str:  # formato YYYY-MM-DD
                    fecha_reserva = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                elif '/' in fecha_str:  # formato DD/MM/YYYY
                    fecha_reserva = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                else:
                    continue
                    
                # Convertir a datetime para comparar con fecha_inicio y fecha_fin
                fecha_reserva_dt = datetime.combine(fecha_reserva, datetime.min.time())
                
                # Verificar si está en el rango
                if fecha_inicio <= fecha_reserva_dt <= fecha_fin:
                    reservas_filtradas.append(reserva)
            except Exception as e:
                print(f"Error al procesar fecha de reserva: {str(e)}")
                continue
                
        return reservas_filtradas
        
    except Exception as e:
        print(f"Error al obtener reservas próximas: {str(e)}")
        print(traceback.format_exc())
        return []

def actualizar_reserva(data, supabase):
    """
    Actualiza una reserva existente en Supabase
    """
    try:
        # Verificar que los datos necesarios estén presentes
        if not data.get('id'):
            return {
                "success": False,
                "error": "ID de reserva no proporcionado",
                "status_code": 400
            }
        
        # Obtener el ID de la reserva
        reserva_id = data.get('id')
        
        # Datos a actualizar
        update_data = {}
        
        # Campos que se pueden actualizar
        campos_actualizables = [
            'nombre', 'email', 'telefono', 'fecha', 'hora', 
            'comensales', 'comentarios', 'estado'
        ]
        
        # Agregar solo los campos que están presentes en la solicitud
        for campo in campos_actualizables:
            if campo in data:
                update_data[campo] = data[campo]
        
        # Si no hay datos para actualizar, retornar error
        if not update_data:
            return {
                "success": False,
                "error": "No se proporcionaron datos para actualizar",
                "status_code": 400
            }
        
        # Actualizar la reserva en Supabase
        response = supabase.table('reservas_prod').update(update_data).eq('id', reserva_id).execute()
        
        # Verificar si la actualización fue exitosa
        if response.data and len(response.data) > 0:
            return {
                "success": True,
                "message": "Reserva actualizada correctamente",
                "reserva": response.data[0]
            }
        else:
            return {
                "success": False,
                "error": "No se encontró la reserva o no se pudo actualizar",
                "status_code": 404
            }
    except Exception as e:
        print(f"Error al actualizar reserva: {str(e)}")
        return {
            "success": False,
            "error": f"Error al procesar la solicitud: {str(e)}",
            "status_code": 500
        }

def buscar_reserva_por_telefono(telefono):
    """
    Busca una reserva por número de teléfono
    
    Args:
        telefono: Número de teléfono a buscar
    
    Returns:
        Diccionario con los datos de la reserva o None si no se encuentra
    """
    try:
        # Normalizar el teléfono para la búsqueda
        telefono_normalizado = telefono.replace('+', '').replace(' ', '')
        
        # Intentar usar Supabase si está disponible
        try:
            from config import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                supabase = get_supabase_client()
                
                # Buscar reservas con este teléfono que no estén canceladas
                response = supabase.table('reservas_prod').select('*').like('telefono', f'%{telefono_normalizado}%').neq('estado', 'Cancelada').order('fecha', desc=False).limit(1).execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]
                return None
        except Exception as e:
            print(f"Error al buscar reserva en Supabase: {str(e)}")
            
        # Fallback a archivo local
        import os
        import json
        
        # Path al archivo de reservas
        RESERVATIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'reservations.json')
        
        # Verificar si el archivo existe
        if not os.path.exists(RESERVATIONS_FILE):
            return None
            
        # Cargar reservas
        with open(RESERVATIONS_FILE, 'r') as f:
            reservas = json.load(f)
            
        # Buscar reserva con este teléfono
        for reserva in reservas:
            tel = reserva.get('telefono', '').replace('+', '').replace(' ', '')
            if telefono_normalizado in tel and reserva.get('estado', '') != 'Cancelada':
                # Convertir fecha si es necesario
                if 'fecha' in reserva and '-' in reserva['fecha']:
                    partes = reserva['fecha'].split('-')
                    if len(partes) == 3:
                        reserva['fecha'] = f"{partes[2]}/{partes[1]}/{partes[0]}"
                return reserva
                
        return None
        
    except Exception as e:
        print(f"Error al buscar reserva por teléfono: {str(e)}")
        print(traceback.format_exc())
        return None

def actualizar_estado_reserva(reserva_id, nuevo_estado):
    """
    Actualiza el estado de una reserva
    
    Args:
        reserva_id: ID de la reserva a actualizar
        nuevo_estado: Nuevo estado ('Confirmada', 'Cancelada', etc.)
    
    Returns:
        Diccionario con el resultado de la operación
    """
    try:
        # Intentar usar Supabase si está disponible
        try:
            from config import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                supabase = get_supabase_client()
                
                # Actualizar estado
                response = supabase.table('reservas_prod').update({'estado': nuevo_estado}).eq('id', reserva_id).execute()
                
                if response.data and len(response.data) > 0:
                    return {"success": True, "message": f"Estado actualizado a {nuevo_estado}"}
                return {"success": False, "error": "No se pudo actualizar la reserva"}
        except Exception as e:
            print(f"Error al actualizar reserva en Supabase: {str(e)}")
            
        # Fallback a archivo local
        import os
        import json
        
        # Path al archivo de reservas
        RESERVATIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'reservations.json')
        
        # Verificar si el archivo existe
        if not os.path.exists(RESERVATIONS_FILE):
            return {"success": False, "error": "Archivo de reservas no encontrado"}
            
        # Cargar reservas
        with open(RESERVATIONS_FILE, 'r') as f:
            reservas = json.load(f)
            
        # Buscar y actualizar reserva
        encontrada = False
        for i, reserva in enumerate(reservas):
            if reserva.get('id') == reserva_id:
                reservas[i]['estado'] = nuevo_estado
                encontrada = True
                break
                
        if not encontrada:
            return {"success": False, "error": "Reserva no encontrada"}
            
        # Guardar cambios
        with open(RESERVATIONS_FILE, 'w') as f:
            json.dump(reservas, f, indent=2)
            
        return {"success": True, "message": f"Estado actualizado a {nuevo_estado}"}
        
    except Exception as e:
        print(f"Error al actualizar estado de reserva: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

def marcar_recordatorio_enviado(reserva_id):
    """
    Marca una reserva como que ya se le envió el recordatorio
    
    Args:
        reserva_id: ID de la reserva
    
    Returns:
        Diccionario con el resultado de la operación
    """
    try:
        # Intentar usar Supabase si está disponible
        try:
            from config import SUPABASE_ENABLED
            if SUPABASE_ENABLED:
                supabase = get_supabase_client()
                
                # Actualizar campo de recordatorio
                response = supabase.table('reservas_prod').update({
                    'recordatorio_enviado': True,
                    'fecha_recordatorio': datetime.now().isoformat()
                }).eq('id', reserva_id).execute()
                
                if response.data and len(response.data) > 0:
                    return {"success": True, "message": "Recordatorio marcado como enviado"}
                return {"success": False, "error": "No se pudo actualizar la reserva"}
        except Exception as e:
            print(f"Error al marcar recordatorio en Supabase: {str(e)}")
            
        # Fallback a archivo local
        import os
        import json
        
        # Path al archivo de reservas
        RESERVATIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'reservations.json')
        
        # Verificar si el archivo existe
        if not os.path.exists(RESERVATIONS_FILE):
            return {"success": False, "error": "Archivo de reservas no encontrado"}
            
        # Cargar reservas
        with open(RESERVATIONS_FILE, 'r') as f:
            reservas = json.load(f)
            
        # Buscar y actualizar reserva
        encontrada = False
        for i, reserva in enumerate(reservas):
            if reserva.get('id') == reserva_id:
                reservas[i]['recordatorio_enviado'] = True
                reservas[i]['fecha_recordatorio'] = datetime.now().isoformat()
                encontrada = True
                break
                
        if not encontrada:
            return {"success": False, "error": "Reserva no encontrada"}
            
        # Guardar cambios
        with open(RESERVATIONS_FILE, 'w') as f:
            json.dump(reservas, f, indent=2)
            
        return {"success": True, "message": "Recordatorio marcado como enviado"}
        
    except Exception as e:
        print(f"Error al marcar recordatorio como enviado: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}