from flask import Blueprint, render_template, redirect, url_for, session, current_app
import json
import os
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_ENABLED
from utils.auth import login_required
from db.supabase_client import get_supabase_client
from routes.admin_routes import DEFAULT_RESTAURANT_DATA

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    # Si ya está logueado, redirigir al dashboard del admin
    if 'user_id' in session and 'restaurant_id' in session:
        return redirect(url_for('admin.dashboard'))
    
    # Si no está logueado, mostrar el home con registro/login
    return render_template('home.html')

@web_bp.route('/reservas')
@login_required
def reservas():
    from services.reservas_service import obtener_reservas
    from app import supabase
    
    # Obtener reservas
    reservas_data = obtener_reservas(supabase)
    
    # Pasar las credenciales de Supabase y los datos de reservas al template
    return render_template('reservas.html',
                          supabase_url=SUPABASE_URL,
                          supabase_key=SUPABASE_KEY,
                          supabase_enabled=SUPABASE_ENABLED,
                          reservas=reservas_data)

@web_bp.route('/login')
def login():
    # Si ya está autenticado, redirigir a reservas
    if 'user_id' in session:
        return redirect(url_for('web.reservas'))
    return render_template('login.html')

@web_bp.route('/registro')
def registro():
    # Si ya está autenticado, redirigir a reservas
    if 'user_id' in session:
        return redirect(url_for('web.reservas'))
    return render_template('registro.html')

@web_bp.route('/logout')
def logout():
    # Eliminar datos de sesión
    session.pop('user_id', None)
    session.pop('user_email', None)
    return redirect(url_for('web.login'))

@web_bp.route('/restaurante/<restaurant_id>')
def restaurante_public_page(restaurant_id):
    current_app.logger.info(f"ENTERING restaurante_public_page for ID: {restaurant_id}")
    supabase_client = get_supabase_client()
    
    restaurant_config = {} # Initialize as a dictionary

    menus_base_dir = os.path.join(current_app.root_path, 'data', 'menus')

    # 1. Fetch Restaurant Configuration
    try:
        if supabase_client:
            response = supabase_client.table('restaurantes').select('*').eq('id', restaurant_id).single().execute()
            if response.data:
                restaurant_config = response.data
                current_app.logger.info(f"Supabase config loaded for {restaurant_id}: {restaurant_config}")
            else:
                current_app.logger.warn(f"No config in Supabase for {restaurant_id}. Using DEFAULT_RESTAURANT_DATA.")
                if isinstance(DEFAULT_RESTAURANT_DATA, dict):
                    restaurant_config = DEFAULT_RESTAURANT_DATA.copy()
                else:
                    current_app.logger.error("DEFAULT_RESTAURANT_DATA is not a dict. Using minimal fallback.")
                    restaurant_config = {} 
        else:
            current_app.logger.error("Supabase client not available. Using DEFAULT_RESTAURANT_DATA.")
            if isinstance(DEFAULT_RESTAURANT_DATA, dict):
                restaurant_config = DEFAULT_RESTAURANT_DATA.copy()
            else:
                current_app.logger.error("DEFAULT_RESTAURANT_DATA is not a dict. Using minimal fallback.")
                restaurant_config = {}
    except Exception as e:
        current_app.logger.error(f"Error fetching/processing restaurant config for {restaurant_id}: {e}. Using DEFAULT_RESTAURANT_DATA.")
        if isinstance(DEFAULT_RESTAURANT_DATA, dict):
            restaurant_config = DEFAULT_RESTAURANT_DATA.copy()
        else:
            current_app.logger.error("DEFAULT_RESTAURANT_DATA is not a dict during exception. Using minimal fallback.")
            restaurant_config = {}

    # Ensure essential ID and a base name are present
    restaurant_config['id'] = restaurant_id 
    restaurant_config.setdefault('name', f"Restaurante (ID: {restaurant_id} - Datos por Defecto)")
    # The mapping logic below handles .get('nombre', .get('name', ...))

    # 2. Load Menu Data
    menu_data_for_chatbot = {}
    menu_file_path = os.path.join(menus_base_dir, f"{restaurant_id}_menu.json")
    try:
        if os.path.exists(menu_file_path):
            with open(menu_file_path, 'r', encoding='utf-8') as f:
                full_menu_json = json.load(f)
            
            dias_semana_es = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
            dia_actual_idx = datetime.now().weekday()
            dia_json = dias_semana_es[dia_actual_idx]

            if full_menu_json and 'dias_semana' in full_menu_json and dia_json in full_menu_json['dias_semana']:
                menu_del_dia = full_menu_json['dias_semana'][dia_json]
                menu_data_for_chatbot['almuerzo_hoy'] = menu_del_dia.get('almuerzo', [])
                cena_info = menu_del_dia.get('cena', "cerrado")
                menu_data_for_chatbot['cena_hoy'] = cena_info if isinstance(cena_info, list) or cena_info == "cerrado" else str(cena_info)
                
                current_app.logger.info(f"[RESTAURANTE_PAGE] Menu data for chatbot - {restaurant_id} - {dia_json}: almuerzo={len(menu_data_for_chatbot['almuerzo_hoy']) if isinstance(menu_data_for_chatbot['almuerzo_hoy'], list) else 'not_list'}, cena={len(menu_data_for_chatbot['cena_hoy']) if isinstance(menu_data_for_chatbot['cena_hoy'], list) else 'not_list'}")
            else:
                current_app.logger.warn(f"[RESTAURANTE_PAGE] Menu structure issue for {restaurant_id}: full_menu_json exists: {bool(full_menu_json)}, has dias_semana: {'dias_semana' in full_menu_json if full_menu_json else False}, has {dia_json}: {dia_json in full_menu_json.get('dias_semana', {}) if full_menu_json else False}")
            
            if full_menu_json and 'menu_especial' in full_menu_json and 'celiaco' in full_menu_json['menu_especial']:
                menu_data_for_chatbot['menu_sin_tacc'] = full_menu_json['menu_especial']['celiaco']
            
            # Log final menu data
            current_app.logger.info(f"[RESTAURANTE_PAGE] Final menu_data_for_chatbot for {restaurant_id}: {menu_data_for_chatbot}")
        else:
            current_app.logger.warn(f"No menu file for {restaurant_id} at {menu_file_path}")
    except Exception as e:
        current_app.logger.error(f"Error loading/processing menu for {restaurant_id}: {e}")

    # 3. Prepare Data for Template and JavaScript (with robust fallbacks)
    
    # Parse info_json if it exists and is a string
    parsed_info_json = {}
    info_json_str = restaurant_config.get('info_json')
    if isinstance(info_json_str, str):
        try:
            parsed_info_json = json.loads(info_json_str)
            current_app.logger.info(f"Successfully parsed info_json for {restaurant_id}")
        except json.JSONDecodeError as e_json:
            current_app.logger.error(f"Error decoding info_json for {restaurant_id}: {e_json}")
    elif isinstance(info_json_str, dict): # If it's already a dict (e.g. from DEFAULT_RESTAURANT_DATA)
        parsed_info_json = info_json_str
        current_app.logger.info(f"Using pre-parsed info_json (likely from defaults) for {restaurant_id}")

    r_name = restaurant_config.get('nombre', restaurant_config.get('name', f"Restaurante {restaurant_id}"))
    
    r_address = restaurant_config.get('direccion') # Primary source from Supabase 'direccion'
    if not r_address: # Fallback to 'address' (e.g. from defaults) or 'address_components'
        r_address = restaurant_config.get('address')
        if not r_address:
            # Try from parsed_info_json.location.address if available
            location_info = parsed_info_json.get('location', {})
            r_address = location_info.get('address') # e.g. "Av. Corrientes 1236, CABA"
            
            if not r_address: # If still no address, construct from address_components
                addr_comp = restaurant_config.get('address_components', {})
                if isinstance(addr_comp, dict):
                    street = addr_comp.get('street', '')
                    number = addr_comp.get('number', '')
                    city = addr_comp.get('city', '')
                    parts = [p for p in [street, number, city] if p]
                    r_address = ", ".join(parts) if parts else 'Dirección no disponible'
                else: 
                    r_address = 'Dirección no disponible (datos inválidos)'
        if not r_address: # Final fallback
             r_address = 'Dirección no disponible'

    r_phone = restaurant_config.get('telefono') # Primary source from Supabase 'telefono'
    if not r_phone: 
        # Fallback to contact.phone from parsed_info_json or restaurant_config.contact (if default data)
        contact_details = parsed_info_json.get('contact', restaurant_config.get('contact', {}))
        r_phone = contact_details.get('phone', 'Teléfono no disponible')

    r_whatsapp = restaurant_config.get('whatsapp') # Check direct column first (future-proofing)
    if not r_whatsapp: # Fallback to contact.whatsapp from parsed_info_json or restaurant_config.contact
        contact_details = parsed_info_json.get('contact', restaurant_config.get('contact', {}))
        r_whatsapp = contact_details.get('whatsapp') # Get value, could be None or empty
    
    if not r_whatsapp: # If None or empty string from any source
        r_whatsapp = 'WhatsApp no disponible'


    r_opening_hours = restaurant_config.get('opening_hours', {}) # Check direct column first
    if not r_opening_hours or not isinstance(r_opening_hours, dict) or not r_opening_hours: # if empty or not a dict
        r_opening_hours = parsed_info_json.get('opening_hours', {}) # Fallback to parsed_info_json
    
    if not r_opening_hours or not isinstance(r_opening_hours, dict) or not r_opening_hours: # Final fallback if still not good
         r_opening_hours = {"info": "Horarios no disponibles"}


    r_reservations_policy = restaurant_config.get('reservations_policy', 'Consulte nuestras políticas de reserva.')
    # Could also try to get this from parsed_info_json if a field is defined
    
    # Payment Methods from 'metodos_pago' (Supabase) or 'payment_methods' (defaults)
    r_payment_methods_raw = restaurant_config.get('metodos_pago', restaurant_config.get('payment_methods'))
    if r_payment_methods_raw is None: 
        r_payment_methods_raw = ['Efectivo'] # Default if key is missing entirely

    if isinstance(r_payment_methods_raw, str):
        try:
            loaded_methods = json.loads(r_payment_methods_raw)
            r_payment_methods = loaded_methods if isinstance(loaded_methods, list) else [r_payment_methods_raw]
        except json.JSONDecodeError:
            r_payment_methods = [r_payment_methods_raw] # Treat as single string method if not JSON
    elif isinstance(r_payment_methods_raw, list):
        r_payment_methods = r_payment_methods_raw
    else:
        r_payment_methods = [str(r_payment_methods_raw)] # Fallback for other types

    chatbot_js_config = {
        'restaurantId': restaurant_id,
        'restaurantName': r_name,
        'contactPhone': r_phone,
        'contactWhatsapp': r_whatsapp,
        'address': r_address,
        'openingHours': r_opening_hours,
        'menuData': menu_data_for_chatbot,
        'reservationsPolicy': r_reservations_policy,
        'paymentMethods': r_payment_methods,
    }

    final_display_info = {
        'id': restaurant_id,
        'name': r_name,
        'phone': r_phone,
        'whatsapp': r_whatsapp,
        'address': r_address,
        'opening_hours': r_opening_hours if isinstance(r_opening_hours, dict) else {},
        'reservations_policy': r_reservations_policy,
        'payment_methods': r_payment_methods,
    }
    current_app.logger.info(f"Final display info for {restaurant_id}: {final_display_info}")
    current_app.logger.info(f"Chatbot JS config for {restaurant_id}: {chatbot_js_config}")

    return render_template('web/restaurante_page.html', 
                           restaurant_display_info=final_display_info,
                           chatbot_js_config=chatbot_js_config)

@web_bp.route('/bot/<restaurant_id>')
def chatbot_page(restaurant_id):
    current_app.logger.info(f"ENTERING chatbot_page for ID: {restaurant_id}")
    supabase_client = get_supabase_client()
    
    restaurant_config = {} 

    menus_base_dir = os.path.join(current_app.root_path, 'data', 'menus')
    info_base_dir = os.path.join(current_app.root_path, 'data', 'info')


    # 1. Fetch Restaurant Configuration from Supabase
    try:
        if supabase_client:
            response = supabase_client.table('restaurantes').select('*').eq('id', restaurant_id).single().execute()
            if response.data:
                restaurant_config = response.data
                current_app.logger.info(f"[DEBUG] Supabase RAW response for {restaurant_id}: {response}")
                current_app.logger.info(f"[DEBUG] logo_url value: {response.data.get('logo_url')}")
                current_app.logger.info(f"Supabase config loaded for chatbot {restaurant_id}: {restaurant_config}")
            else:
                current_app.logger.warn(f"No config in Supabase for chatbot {restaurant_id}. Will use defaults or try local files.")
                restaurant_config = {'id': restaurant_id} # Start with ID
        else:
            current_app.logger.error("Supabase client not available for chatbot. Will use defaults or try local files.")
            restaurant_config = {'id': restaurant_id}
    except Exception as e:
        current_app.logger.error(f"Error fetching restaurant config from Supabase for chatbot {restaurant_id}: {e}. Will use defaults or try local files.")
        restaurant_config = {'id': restaurant_id}

    # 2. Load Local Info JSON if Supabase info_json is missing or incomplete
    # (Supabase 'info_json' column is expected to be a JSON string)
    parsed_info_json = {}
    if 'info_json' in restaurant_config and isinstance(restaurant_config['info_json'], str):
        try:
            parsed_info_json = json.loads(restaurant_config['info_json'])
            current_app.logger.info(f"Successfully parsed info_json from Supabase for chatbot {restaurant_id}")
        except json.JSONDecodeError as e_json:
            current_app.logger.error(f"Error decoding info_json from Supabase for chatbot {restaurant_id}: {e_json}. Trying local file.")
            parsed_info_json = {} # Reset if parsing failed
    elif 'info_json' in restaurant_config and isinstance(restaurant_config['info_json'], dict):
         parsed_info_json = restaurant_config['info_json'] # Already a dict
         current_app.logger.info(f"Using pre-parsed info_json from Supabase data for chatbot {restaurant_id}")


    if not parsed_info_json: # If Supabase didn't provide it or it was invalid
        local_info_file_path = os.path.join(info_base_dir, f"{restaurant_id}_info.json")
        if os.path.exists(local_info_file_path):
            try:
                with open(local_info_file_path, 'r', encoding='utf-8') as f:
                    parsed_info_json = json.load(f)
                current_app.logger.info(f"Loaded local info.json for chatbot {restaurant_id} from {local_info_file_path}")
            except Exception as e_file:
                current_app.logger.error(f"Error loading local info.json for chatbot {restaurant_id}: {e_file}")
        else:
            current_app.logger.warn(f"No local info.json found for chatbot {restaurant_id} at {local_info_file_path}")

    # Fallback to DEFAULT_RESTAURANT_DATA if parsed_info_json is still empty
    if not parsed_info_json and isinstance(DEFAULT_RESTAURANT_DATA, dict):
        current_app.logger.info(f"Using DEFAULT_RESTAURANT_DATA as fallback for info_json for chatbot {restaurant_id}")
        parsed_info_json = DEFAULT_RESTAURANT_DATA.copy() # Use a copy
    elif not parsed_info_json:
        current_app.logger.error(f"DEFAULT_RESTAURANT_DATA is not a dict or not available. Minimal info for chatbot {restaurant_id}")
        parsed_info_json = {}


    # 3. Load Menu Data (local file only for now as per existing logic)
    menu_data_for_chatbot = {}
    menu_file_path = os.path.join(menus_base_dir, f"{restaurant_id}_menu.json")
    try:
        if os.path.exists(menu_file_path):
            with open(menu_file_path, 'r', encoding='utf-8') as f:
                full_menu_json = json.load(f)
            
            dias_semana_es = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
            dia_actual_idx = datetime.now().weekday()
            dia_json = dias_semana_es[dia_actual_idx]

            if full_menu_json and 'dias_semana' in full_menu_json and dia_json in full_menu_json['dias_semana']:
                menu_del_dia = full_menu_json['dias_semana'][dia_json]
                menu_data_for_chatbot['almuerzo_hoy'] = menu_del_dia.get('almuerzo', [])
                cena_info = menu_del_dia.get('cena', "cerrado")
                menu_data_for_chatbot['cena_hoy'] = cena_info if isinstance(cena_info, list) or cena_info == "cerrado" else str(cena_info)
                
                current_app.logger.info(f"[CHATBOT_PAGE] Menu data for chatbot - {restaurant_id} - {dia_json}: almuerzo={len(menu_data_for_chatbot['almuerzo_hoy']) if isinstance(menu_data_for_chatbot['almuerzo_hoy'], list) else 'not_list'}, cena={len(menu_data_for_chatbot['cena_hoy']) if isinstance(menu_data_for_chatbot['cena_hoy'], list) else 'not_list'}")
            else:
                current_app.logger.warn(f"[CHATBOT_PAGE] Menu structure issue for {restaurant_id}: full_menu_json exists: {bool(full_menu_json)}, has dias_semana: {'dias_semana' in full_menu_json if full_menu_json else False}, has {dia_json}: {dia_json in full_menu_json.get('dias_semana', {}) if full_menu_json else False}")
            
            if full_menu_json and 'menu_especial' in full_menu_json and 'celiaco' in full_menu_json['menu_especial']:
                menu_data_for_chatbot['menu_sin_tacc'] = full_menu_json['menu_especial']['celiaco']
            
            # Log final menu data
            current_app.logger.info(f"[CHATBOT_PAGE] Final menu_data_for_chatbot for {restaurant_id}: {menu_data_for_chatbot}")
        else:
            current_app.logger.warn(f"No menu file for chatbot {restaurant_id} at {menu_file_path}")
    except Exception as e:
        current_app.logger.error(f"Error loading/processing menu for chatbot {restaurant_id}: {e}")

    # 4. Consolidate and Prepare Data for Template
    # Prioritize Supabase direct columns, then parsed_info_json, then hardcoded defaults.

    r_name = restaurant_config.get('nombre') or parsed_info_json.get('name', f"Restaurante {restaurant_id}")
    r_logo_url = restaurant_config.get('logo_url') # From Supabase
    current_app.logger.info(f"[DEBUG] restaurant_config completo: {restaurant_config}")
    current_app.logger.info(f"[DEBUG] r_logo_url después de get: {r_logo_url}")
    if not r_logo_url and 'brand' in parsed_info_json and isinstance(parsed_info_json['brand'], dict): # Check local info.json
        r_logo_url = parsed_info_json['brand'].get('logo_url')
        current_app.logger.info(f"[DEBUG] r_logo_url después de fallback: {r_logo_url}")
    
    r_address = restaurant_config.get('direccion')
    if not r_address:
        loc_info = parsed_info_json.get('location', {})
        r_address = loc_info.get('address', 'Dirección no disponible')

    r_phone = restaurant_config.get('telefono')
    if not r_phone:
        contact_info = parsed_info_json.get('contact', {})
        r_phone = contact_info.get('phone', 'Teléfono no disponible')

    r_whatsapp = restaurant_config.get('whatsapp')
    if not r_whatsapp:
        contact_info = parsed_info_json.get('contact', {})
        r_whatsapp = contact_info.get('whatsapp', 'WhatsApp no disponible')
        
    # Opening Hours: Supabase direct column (expected as JSON string or dict) -> parsed_info_json -> default
    r_opening_hours = restaurant_config.get('opening_hours')
    if isinstance(r_opening_hours, str):
        try:
            r_opening_hours = json.loads(r_opening_hours)
        except json.JSONDecodeError:
            current_app.logger.error(f"Error decoding opening_hours from Supabase string for {restaurant_id}")
            r_opening_hours = None
    if not isinstance(r_opening_hours, dict) or not r_opening_hours: # If not a dict or empty
        r_opening_hours = parsed_info_json.get('opening_hours', {"info": "Horarios no disponibles"})


    r_reservations_policy = restaurant_config.get('reservations_policy', 'Consulte nuestras políticas de reserva.')
    
    # Payment Methods: Supabase direct column (JSON string or list) -> parsed_info_json -> default
    r_payment_methods_raw = restaurant_config.get('metodos_pago')
    if not r_payment_methods_raw: # Fallback to parsed_info_json if Supabase field is empty
        r_payment_methods_raw = parsed_info_json.get('payment_methods')

    if r_payment_methods_raw is None: 
        r_payment_methods = ['Efectivo'] # Default if key is missing entirely
    elif isinstance(r_payment_methods_raw, str):
        try:
            loaded_methods = json.loads(r_payment_methods_raw)
            r_payment_methods = loaded_methods if isinstance(loaded_methods, list) else [r_payment_methods_raw]
        except json.JSONDecodeError:
            r_payment_methods = [pm.strip() for pm in r_payment_methods_raw.split(',')] if r_payment_methods_raw else ['Efectivo']
    elif isinstance(r_payment_methods_raw, list):
        r_payment_methods = r_payment_methods_raw
    else:
        r_payment_methods = [str(r_payment_methods_raw)]


    chatbot_js_config = {
        'restaurantId': restaurant_id,
        'restaurantName': r_name,
        'contactPhone': r_phone,
        'contactWhatsapp': r_whatsapp,
        'address': r_address,
        'openingHours': r_opening_hours, # This should be the structured dict
        'menuData': menu_data_for_chatbot,
        'reservationsPolicy': r_reservations_policy,
        'paymentMethods': r_payment_methods,
        'supabaseUrl': current_app.config.get('SUPABASE_URL'),
        'supabaseKey': current_app.config.get('SUPABASE_KEY'),
        'supabaseEnabled': current_app.config.get('SUPABASE_ENABLED')
    }

    restaurant_display_info = {
        'id': restaurant_id,
        'name': r_name,
        'logo_url': r_logo_url, # Pass logo to template
        # Add any other fields needed directly by the template but not by chatbot.js
    }
    
    current_app.logger.info(f"Chatbot JS config for {restaurant_id}: {chatbot_js_config}")
    current_app.logger.info(f"Restaurant display info for chatbot page {restaurant_id}: {restaurant_display_info}")

    return render_template('web/chatbot_page.html', 
                           restaurant_display_info=restaurant_display_info,
                           chatbot_js_config=chatbot_js_config,
                           now=datetime.utcnow()) # For footer year
