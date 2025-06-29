from flask import render_template, request, redirect, url_for, flash, jsonify, session, g
from .admin_routes import admin_bp # Import admin_bp from admin_routes.py
from utils.auth import login_required 
from services.file_service import guardar_datos_json, cargar_datos_json
import os
import json
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Placeholder for dias_semana 
dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Directory for menu files
MENUS_DIRECTORY = os.path.join(os.getcwd(), 'data', 'menus')
INFO_DIRECTORY = os.path.join(os.getcwd(), 'data', 'info')
INFO_DIRECTORY = os.path.join(os.getcwd(), 'data', 'info')

def get_menu_file_path(restaurant_id):
    """Get the correct menu file path for a specific restaurant"""
    return os.path.join(MENUS_DIRECTORY, f"{restaurant_id}_menu.json")

def get_menu(restaurant_id):
    """Load menu from restaurant-specific file"""
    try:
        menu_file_path = get_menu_file_path(restaurant_id)
        if os.path.exists(menu_file_path):
            with open(menu_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading menu for restaurant {restaurant_id}: {e}")
    
    # Return default menu structure
    return {
        "dias_semana": {
            "lunes": {"almuerzo": [], "cena": []},
            "martes": {"almuerzo": [], "cena": []},
            "miércoles": {"almuerzo": [], "cena": []},
            "jueves": {"almuerzo": [], "cena": []},
            "viernes": {"almuerzo": [], "cena": []},
            "sábado": {"almuerzo": [], "cena": []},
            "domingo": {"almuerzo": [], "cena": []}
        },
        "menu_especial": {
            "celiaco": {
                "platos_principales": [],
                "postres": [],
                "nota": ""
            }
        }
    }

@admin_bp.route('/menu/editor', methods=['GET'])
@login_required
def menu_editor():
    # Get current restaurant ID from session
    restaurant_id = session.get('restaurant_id')
    if not restaurant_id:
        flash("Por favor, selecciona un restaurante primero.", "warning")
        return redirect(url_for('admin.select_restaurant'))
    
    menu = get_menu(restaurant_id)
    if 'menu_especial' not in menu:
        menu['menu_especial'] = {
            'celiaco': {
                'platos_principales': [],
                'postres': [],
                'nota': ''
            }
        }
    return render_template('admin/menu_editor.html', 
                          dias_semana=dias_semana,
                          menu=menu)

@admin_bp.route('/menu/guardar', methods=['POST'])
@login_required
def guardar_menu():
    """Save menu changes for the current restaurant"""
    restaurant_id = session.get('restaurant_id')
    if not restaurant_id:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"success": False, "error": "No restaurant selected"})
        flash("Por favor, selecciona un restaurante primero.", "error")
        return redirect(url_for('admin.select_restaurant'))
    
    # Check if this is a JSON request from the new editor
    is_json_request = request.headers.get('Content-Type') == 'application/json'
    
    try:
        if is_json_request:
            # Handle JSON data from the new editor
            menu_data = request.get_json()
            if not menu_data:
                return jsonify({"success": False, "error": "No menu data received"})
        else:
            # Handle form data (legacy support)
            # Initialize menu structure
            menu_data = {
                "dias_semana": {},
                "menu_especial": {
                    "celiaco": {
                        "platos_principales": [],
                        "postres": [],
                        "nota": ""
                    }
                }
            }
            
            # Process each day of the week
            for dia in dias_semana:
                menu_data["dias_semana"][dia] = {
                    "almuerzo": [],
                    "cena": []
                }
                
                # Process almuerzo items
                i = 0
                while True:
                    nombre_key = f"{dia}_almuerzo_nombre_{i}"
                    precio_key = f"{dia}_almuerzo_precio_{i}"
                    
                    if nombre_key not in request.form:
                        break
                        
                    nombre = request.form.get(nombre_key, '').strip()
                    precio = request.form.get(precio_key, '').strip()
                    
                    if nombre:  # Only add if name is not empty
                        menu_data["dias_semana"][dia]["almuerzo"].append({
                            "name": nombre,
                            "price": precio
                        })
                    i += 1
                
                # Process cena items
                i = 0
                while True:
                    nombre_key = f"{dia}_cena_nombre_{i}"
                    precio_key = f"{dia}_cena_precio_{i}"
                    
                    if nombre_key not in request.form:
                        break
                        
                    nombre = request.form.get(nombre_key, '').strip()
                    precio = request.form.get(precio_key, '').strip()
                    
                    if nombre:  # Only add if name is not empty
                        menu_data["dias_semana"][dia]["cena"].append({
                            "name": nombre,
                            "price": precio
                        })
                    i += 1
            
            # Process menu especial (celiaco)
            # Platos principales
            i = 0
            while True:
                nombre_key = f"celiaco_plato_principal_{i}"
                if nombre_key not in request.form:
                    break
                    
                nombre = request.form.get(nombre_key, '').strip()
                if nombre:
                    menu_data["menu_especial"]["celiaco"]["platos_principales"].append(nombre)
                i += 1
            
            # Postres
            i = 0
            while True:
                nombre_key = f"celiaco_postre_{i}"
                if nombre_key not in request.form:
                    break
                    
                nombre = request.form.get(nombre_key, '').strip()
                if nombre:
                    menu_data["menu_especial"]["celiaco"]["postres"].append(nombre)
                i += 1
            
            # Nota del menú celiaco
            menu_data["menu_especial"]["celiaco"]["nota"] = request.form.get("celiaco_nota", "").strip()
        
        # Save to restaurant-specific file
        menu_file_path = get_menu_file_path(restaurant_id)
        os.makedirs(os.path.dirname(menu_file_path), exist_ok=True)
        
        with open(menu_file_path, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, ensure_ascii=False, indent=2)
        
        # Return JSON response for AJAX requests, redirect for form submissions
        if is_json_request:
            return jsonify({"success": True, "message": "Menú guardado exitosamente"})
        else:
            flash("Menú guardado exitosamente", "success")
            return redirect(url_for('admin.menu_editor'))
        
    except Exception as e:
        error_msg = f"Error al guardar el menú: {str(e)}"
        if is_json_request:
            return jsonify({"success": False, "error": error_msg})
        else:
            flash(error_msg, "error")
            return redirect(url_for('admin.menu_editor'))

@admin_bp.route('/calendar', methods=['GET'])
@login_required
def calendar():
    """Mostrar calendario de reservas"""
    restaurant_id = session.get('restaurant_id')
    restaurant_name = session.get('restaurant_name', 'Restaurante')
    
    if not restaurant_id:
        flash("Por favor, selecciona un restaurante primero.", "warning")
        return redirect('/admin/crear_restaurante')
    
    # Cargar eventos reales desde la base de datos
    events = []
    try:
        from db.supabase_client import supabase
        from datetime import datetime, timedelta
        
        # Obtener reservas para los próximos 30 días
        now = datetime.now()
        start_date = now.date()
        end_date = start_date + timedelta(days=30)
        
        # Consultar reservas
        response = supabase.table('reservas_prod').select('*').eq('restaurante_id', restaurant_id).gte('fecha', start_date.isoformat()).lte('fecha', end_date.isoformat()).execute()
        
        if response.data:
            for reserva in response.data:
                event = {
                    'id': reserva.get('id'),
                    'title': f"{reserva.get('nombre_cliente', 'Sin nombre')} - {reserva.get('personas', 0)} personas",
                    'start': f"{reserva.get('fecha')}T{reserva.get('hora', '00:00')}",
                    'backgroundColor': get_event_color(reserva.get('estado', 'Pendiente')),
                    'borderColor': get_event_color(reserva.get('estado', 'Pendiente')),
                    'extendedProps': {
                        'cliente': reserva.get('nombre_cliente', 'Sin nombre'),
                        'telefono': reserva.get('telefono', ''),
                        'personas': reserva.get('personas', 0),
                        'estado': reserva.get('estado', 'Pendiente'),
                        'comentarios': reserva.get('comentarios', '')
                    }
                }
                events.append(event)
    except Exception as e:
        logger.error(f"Error cargando eventos del calendario: {e}")
        flash("Error al cargar las reservas del calendario.", "error")
    
    return render_template('admin/calendar.html', 
                          restaurant_name=restaurant_name,
                          restaurant_id=restaurant_id,
                          events=events)

def get_event_color(estado):
    """Obtener color del evento basado en el estado"""
    colors = {
        'Pendiente': '#ffc107',  # amarillo
        'Confirmada': '#28a745',  # verde
        'Confirmado': '#28a745',  # verde
        'Cancelada': '#dc3545',   # rojo
        'Cancelado': '#dc3545',   # rojo
        'No asistió': '#6c757d'   # gris
    }
    return colors.get(estado, '#007bff')  # azul por defecto

@admin_bp.route('/reservations', methods=['GET'])
@login_required  
def reservations():
    """Mostrar gestión de reservas"""
    restaurant_id = session.get('restaurant_id')
    restaurant_name = session.get('restaurant_name', 'Restaurante')
    
    if not restaurant_id:
        flash("Por favor, selecciona un restaurante primero.", "warning")
        return redirect('/admin/crear_restaurante')
    
    # Cargar reservas reales desde la base de datos
    reservas = []
    proximas_reservas = []
    try:
        from db.supabase_client import supabase
        from datetime import datetime, timedelta
        
        # Obtener todas las reservas del restaurante
        response = supabase.table('reservas_prod').select('*').eq('restaurante_id', restaurant_id).order('fecha', desc=False).order('hora', desc=False).execute()
        
        if response.data:
            now = datetime.now()
            today = now.date()
            
            for reserva in response.data:
                try:
                    fecha_reserva = datetime.strptime(reserva.get('fecha', ''), '%Y-%m-%d').date()
                    # Separar en reservas pasadas y próximas
                    if fecha_reserva >= today:
                        proximas_reservas.append(reserva)
                    reservas.append(reserva)
                except ValueError:
                    # Si hay error en el formato de fecha, agregar a la lista general
                    reservas.append(reserva)
            
            logger.info(f"Cargadas {len(reservas)} reservas totales, {len(proximas_reservas)} próximas")
    except Exception as e:
        logger.error(f"Error cargando reservas: {e}")
        flash("Error al cargar las reservas.", "error")
    
    return render_template('admin/reservations.html',
                          restaurant_name=restaurant_name,
                          restaurant_id=restaurant_id,
                          reservas=reservas,
                          proximas_reservas=proximas_reservas)

@admin_bp.route('/menu_editor', methods=['GET'])
@login_required
def menu_editor_redirect():
    """Redirección a la ruta correcta del editor de menú"""
    return redirect('/admin/menu/editor')

from pytz import all_timezones
from db.supabase_client import supabase

@admin_bp.route('/location_editor_page', methods=['GET'])
@login_required
def location_editor_page():
    """Editor de información del restaurante/ubicación"""
    restaurant_id = session.get('restaurant_id')
    restaurant_name = session.get('restaurant_name', 'Restaurante')
    
    if not restaurant_id:
        flash("Por favor, selecciona un restaurante primero.", "warning")
        return redirect('/admin/crear_restaurante')
    
    zona_horaria_actual = None
    try:
        response = supabase.table('restaurantes').select('zona_horaria').eq('id', restaurant_id).single().execute()
        if response.data:
            zona_horaria_actual = response.data.get('zona_horaria')
    except Exception as e:
        logger.error(f"Error al cargar la zona horaria actual para el editor de ubicación: {e}", exc_info=True)
        flash("Error al cargar la configuración de la zona horaria.", "error")

    return render_template('admin/location_editor.html',
                          restaurant_name=restaurant_name,
                          restaurant_id=restaurant_id,
                          all_timezones=all_timezones,
                          zona_horaria_actual=zona_horaria_actual)

@admin_bp.route('/get_restaurant_info', methods=['GET'])
@login_required
def get_restaurant_info():
    """Obtener información del restaurante"""
    restaurant_id = session.get('restaurant_id')
    
    if not restaurant_id:
        return jsonify({"success": False, "error": "No restaurant selected"})
    
    try:
        # Primero intentar cargar desde archivo JSON específico del restaurante
        info_file_path = os.path.join(INFO_DIRECTORY, f"{restaurant_id}_info.json")
        
        if os.path.exists(info_file_path):
            with open(info_file_path, 'r', encoding='utf-8') as f:
                restaurant_info = json.load(f)
                logger.info(f"Info del restaurante cargada desde archivo: {info_file_path}")
                return jsonify({"success": True, "data": restaurant_info})
        
        # Si no existe el archivo, intentar cargar desde la base de datos
        from db.supabase_client import supabase
        
        # Obtener información básica del restaurante desde la tabla restaurantes
        response = supabase.table('restaurantes').select('*, politicas').eq('id', restaurant_id).execute()
        
        if response.data and len(response.data) > 0:
            restaurant_db = response.data[0]
            
            # Crear estructura de datos por defecto con información de la BD
            restaurant_info = {
                "name": restaurant_db.get('nombre', ''),
                "description": restaurant_db.get('descripcion', ''),
                "location": {
                    "address": restaurant_db.get('direccion', ''),
                    "google_maps_link": restaurant_db.get('google_maps_link', '')
                },
                "contact": {
                    "phone": restaurant_db.get('telefono', ''),
                    "email": restaurant_db.get('email', '')
                },
                "como_llegar": {
                    "texto_transporte_publico": restaurant_db.get('transporte_publico', ''),
                    "texto_auto": restaurant_db.get('como_llegar_auto', '')
                },
                "opening_hours": get_default_opening_hours(),
                "payment_methods": [],
                "promotions": [],
                "policies": restaurant_db.get('politicas', get_default_restaurant_info()['policies']), # Load policies from DB, or use default
                "config": {
                    "activo": restaurant_db.get('estado') == 'activo',
                    "mostrar_ubicacion_mapa": True
                }
            }
            
            # Guardar en archivo para futuras consultas
            os.makedirs(INFO_DIRECTORY, exist_ok=True)
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(restaurant_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Info del restaurante creada desde BD y guardada en: {info_file_path}")
            return jsonify({"success": True, "data": restaurant_info})
        
        # Si no hay datos en BD, devolver estructura por defecto
        default_info = get_default_restaurant_info()
        return jsonify({"success": True, "data": default_info})
        
    except Exception as e:
        logger.error(f"Error al obtener información del restaurante: {e}")
        return jsonify({"success": False, "error": str(e)})

def get_default_opening_hours():
    """Obtener horarios por defecto"""
    return {
        "lunes": {"open": "12:00", "close": "23:00", "is_closed": False},
        "martes": {"open": "12:00", "close": "23:00", "is_closed": False},
        "miercoles": {"open": "12:00", "close": "23:00", "is_closed": False},
        "jueves": {"open": "12:00", "close": "23:00", "is_closed": False},
        "viernes": {"open": "12:00", "close": "23:00", "is_closed": False},
        "sabado": {"open": "12:00", "close": "23:00", "is_closed": False},
        "domingo": {"open": "12:00", "close": "16:00", "is_closed": False}
    }

def get_default_restaurant_info():
    """Obtener información por defecto del restaurante"""
    return {
        "name": "",
        "description": "",
        "location": {
            "address": "",
            "google_maps_link": ""
        },
        "contact": {
            "phone": "",
            "email": ""
        },
        "como_llegar": {
            "texto_transporte_publico": "",
            "texto_auto": ""
        },
        "opening_hours": get_default_opening_hours(),
        "payment_methods": [],
        "promotions": [],
        "policies": {
            "pets": {
                "allowed": False,
                "restrictions": "",
                "description": ""
            },
            "children": {
                "allowed": True,
                "description": "",
                "amenities": []
            },
            "accessibility": {
                "wheelchair_accessible": False,
                "braille_menu": False,
                "description": ""
            },
            "dietary_options": {
                "vegetarian": False,
                "vegan": False,
                "gluten_free": False,
                "description": ""
            },
            "parking": {
                "available": False,
                "type": "propio",
                "description": ""
            },
            "dress_code": {
                "required": False,
                "style": "casual",
                "description": ""
            },
            "smoking": {
                "allowed": False,
                "outdoor_allowed": False,
                "description": ""
            },
            "cancellation": {
                "advance_notice_hours": 4,
                "policy": "",
                "description": ""
            },
            "noise_level": {
                "level": "moderado",
                "description": ""
            },
            "group_reservations": {
                "max_size": 20,
                "advance_booking_required": False,
                "description": ""
            }
        },
        "config": {
            "activo": True,
            "mostrar_ubicacion_mapa": True
        }
    }

@admin_bp.route('/location_editor', methods=['POST'])
@login_required
def save_restaurant_info():
    """Guardar información del restaurante"""
    restaurant_id = session.get('restaurant_id')
    
    if not restaurant_id:
        return jsonify({"success": False, "error": "No restaurant selected"})
    
    try:
        # Recopilar datos del formulario
        restaurant_info = {
            "name": request.form.get('name', ''),
            "description": request.form.get('description', ''),
            "location": json.loads(request.form.get('location', '{}')),
            "contact": json.loads(request.form.get('contact', '{}')),
            "como_llegar": json.loads(request.form.get('como_llegar', '{}')),
            "opening_hours": json.loads(request.form.get('opening_hours', '{}')),
            "payment_methods": json.loads(request.form.get('payment_methods', '[]')),
            "promotions": json.loads(request.form.get('promotions', '[]')),
            "config": json.loads(request.form.get('config', '{}')),
            "timezone": request.form.get('timezone', ''),
            "policies": json.loads(request.form.get('policies', '{}'))
        }
        
        # Guardar en archivo JSON específico del restaurante
        info_file_path = os.path.join(INFO_DIRECTORY, f"{restaurant_id}_info.json")
        os.makedirs(INFO_DIRECTORY, exist_ok=True)
        
        with open(info_file_path, 'w', encoding='utf-8') as f:
            json.dump(restaurant_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Información del restaurante guardada en: {info_file_path}")
        
        # También actualizar campos básicos en la base de datos
        try:
            
            update_data = {
                'nombre': restaurant_info.get('name', ''),
                'descripcion': restaurant_info.get('description', ''),
                'direccion': restaurant_info.get('location', {}).get('address', ''),
                'telefono': restaurant_info.get('contact', {}).get('phone', ''),
                'email': restaurant_info.get('contact', {}).get('email', ''),
                'zona_horaria': restaurant_info.get('timezone', ''),
                'politicas': restaurant_info.get('policies', {})
            }
            
            # Filtrar campos vacíos
            update_data = {k: v for k, v in update_data.items() if v}
            
            if update_data:
                response = supabase.table('restaurantes').update(update_data).eq('id', restaurant_id).execute()
                logger.info(f"Información básica del restaurante actualizada en BD")
                
        except Exception as e:
            logger.warning(f"No se pudo actualizar la BD, pero el archivo se guardó: {e}")
        
        return jsonify({"success": True, "message": "Información del restaurante guardada correctamente"})
        
    except Exception as e:
        logger.error(f"Error al guardar información del restaurante: {e}")
        return jsonify({"success": False, "error": str(e)})