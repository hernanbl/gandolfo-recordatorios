from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import json
import os
import uuid
from functools import wraps
from db.supabase_client import supabase
from services.db.supabase import get_supabase_client, execute_with_retry  # Import robust service
from services.reservas_service import actualizar_estado_reserva
# Usaremos obtener_reservas_proximas directamente desde services.reservas.db
from services.file_service import guardar_datos_json, cargar_datos_json
import logging
import copy
# Import the new central login_required from utils.auth
from utils.auth import login_required
# Importar utilidades para el modo demo
from utils.demo_utils import is_demo_restaurant, get_demo_restaurant_info, get_reservas_table

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

# Paths for menu files
DEFAULT_MENU_FILE = os.path.join(os.getcwd(), 'data', 'processed', 'menu.json')
MENUS_DIRECTORY = os.path.join(os.getcwd(), 'data', 'menus')
INFO_DIRECTORY = os.path.join(os.getcwd(), 'data', 'info')  # Added INFO_DIRECTORY

# Home landing page route
@admin_bp.route('/', methods=['GET'])
def home():
    """Home landing page for new users"""
    return render_template('home.html')

# API endpoint para obtener configuración de Supabase
@admin_bp.route('/api/config', methods=['GET'])
def get_config():
    """Return Supabase configuration for frontend"""
    from config import SUPABASE_URL, SUPABASE_KEY
    return jsonify({
        "supabase_url": SUPABASE_URL,
        "supabase_key": SUPABASE_KEY
    })

# Google OAuth callback route
@admin_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Display the auth callback page that will handle the OAuth tokens in JavaScript"""
    return render_template('admin/auth_callback.html')

# Process Google user data from frontend
@admin_bp.route('/auth/process-google-user', methods=['POST'])
def process_google_user():
    """Process Google user data received from frontend JavaScript"""
    try:
        # Limpiar mensajes flash anteriores para evitar confusión
        session.pop('_flashes', None)
        
        data = request.get_json()
        
        if not data or not data.get('user_id') or not data.get('email'):
            return jsonify({"success": False, "error": "Datos de usuario incompletos"})
        
        user_id = data['user_id']
        email = data['email']
        full_name = data.get('full_name', email.split('@')[0])
        
        logger.info(f"Procesando usuario de Google: {email}")
        
        # Verificar si el usuario ya existe en la tabla usuarios
        existing_user = supabase.table('usuarios').select('*').eq('auth_user_id', user_id).execute()
        
        if not existing_user.data:
            # Crear nuevo usuario en la tabla usuarios
            user_data = {
                "auth_user_id": str(user_id),
                "email": email,
                "nombre": full_name,
                "rol": "admin"
            }
            
            usuarios_response = supabase.table('usuarios').insert(user_data).execute()
            logger.info(f"Nuevo usuario Google creado: {email}")
            
            # Obtener el ID del usuario creado
            created_user = usuarios_response.data[0] if usuarios_response.data else None
            user_id_from_session = created_user['id'] if created_user else None
        else:
            user_id_from_session = existing_user.data[0]['id']
            logger.info(f"Usuario Google existente: {email}")
        
        # Configurar la sesión
        session['auth_user_id'] = user_id
        session['user_id'] = user_id_from_session
        session['user_email'] = email
        session['nombre_usuario'] = full_name
        session['username'] = full_name
        
        # Buscar si el usuario tiene restaurantes
        restaurantes = supabase.table('restaurantes').select('id, nombre').eq('admin_id', str(user_id)).execute()
        
        if restaurantes.data and len(restaurantes.data) > 0:
            # Usuario tiene restaurantes
            if len(restaurantes.data) == 1:
                session['restaurant_id'] = restaurantes.data[0]['id']
                session['restaurant_name'] = restaurantes.data[0]['nombre']
                return jsonify({
                    "success": True, 
                    "redirect_to": "/admin/dashboard",
                    "message": f"¡Bienvenido de vuelta! Restaurante: {restaurantes.data[0]['nombre']}"
                })
            else:
                return jsonify({
                    "success": True, 
                    "redirect_to": "/admin/crear_restaurante"
                })
        else:
            # Usuario no tiene restaurantes, crear uno
            # No usar flash message aquí, usar sessionStorage en el frontend
            return jsonify({
                "success": True, 
                "redirect_to": "/admin/crear_restaurante",
                "message": f"¡Bienvenido {full_name}! Vamos a configurar tu restaurante."
            })
            
    except Exception as e:
        logger.error(f"Error procesando usuario de Google: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Error interno del servidor"})

# Adding the missing admin.login route
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        logger.info(f"Estado de sesión ANTES del login: {dict(session)}")
        return render_template('admin/login.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    logger.info(f"Intento de login con email: {email}")
    
    # MÉTODO SUPABASE AUTH: Usar autenticación de Supabase con servicio robusto
    try:
        # Obtener cliente Supabase robusto
        supabase_client = get_supabase_client()
        
        if not supabase_client:
            logger.error("❌ No se pudo obtener cliente Supabase")
            flash("Error de configuración del servidor. Verifique las variables de entorno Supabase.", "error")
            return render_template('admin/login.html')
        
        if not hasattr(supabase_client, 'auth'):
            logger.error("❌ Cliente Supabase no tiene módulo de autenticación")
            flash("Error de configuración del servidor. Cliente Supabase incompleto.", "error")
            return render_template('admin/login.html')
        
        logger.info("✅ Cliente Supabase obtenido correctamente")
        
        # Intentar login con Supabase Auth usando el servicio robusto
        def perform_auth():
            return supabase_client.auth.sign_in(
                email=email,
                password=password
            )
        
        auth_result = execute_with_retry(perform_auth, max_retries=2)
        
        if not auth_result:
            logger.error("❌ Error en autenticación: login falló")
            flash("Credenciales incorrectas o error de conexión. Intente nuevamente.", "error")
            return render_template('admin/login.html')
        
        # Verificar el resultado de autenticación
        user_data = None
        auth_user_id = None
        
        if hasattr(auth_result, 'user') and auth_result.user:
            auth_user_id = auth_result.user.id
            user_email = auth_result.user.email
            logger.info(f"✅ Login exitoso con Supabase Auth para: {email}")
        elif hasattr(auth_result, 'id'):
            # Resultado directo del usuario
            auth_user_id = auth_result.id
            user_email = getattr(auth_result, 'email', email)
            logger.info(f"✅ Login exitoso (usuario directo) para: {email}")
        else:
            logger.error("❌ Resultado de autenticación no contiene usuario válido")
            flash("Error en el proceso de autenticación. Intente nuevamente.", "error")
            return render_template('admin/login.html')
        
        # Buscar el usuario en nuestra tabla usuarios usando servicio robusto
        def find_user():
            return supabase_client.table('usuarios').select('*').eq('auth_user_id', auth_user_id).execute()
        
        result = execute_with_retry(find_user, max_retries=2)
        
        if not result:
            logger.error("❌ Error buscando usuario en base de datos")
            flash("Error de conexión con la base de datos. Intente nuevamente.", "error")
            return render_template('admin/login.html')
            
        if result.data:
            user = result.data[0]
            
            # Configurar sesión
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['username'] = user.get('nombre', email.split('@')[0])  # Cambiar a 'username'
            session['nombre_usuario'] = user.get('nombre', email.split('@')[0])  # Agregar también nombre_usuario para compatibilidad
            session['auth_user_id'] = auth_user_id
            
            # Verificar restaurantes - usar auth_user_id ya que admin_id en restaurantes apunta a auth.users
            def find_restaurants():
                return supabase_client.table('restaurantes').select('*').eq('admin_id', auth_user_id).execute()
            
            restaurantes_result = execute_with_retry(find_restaurants, max_retries=2)
            
            if not restaurantes_result:
                logger.warning("⚠️  Error obteniendo restaurantes del usuario")
                restaurantes = []
            else:
                restaurantes = restaurantes_result.data
            
            if not restaurantes:
                logger.info("Usuario sin restaurantes, redirigiendo a crear restaurante")
                return redirect('/admin/crear_restaurante')
            elif len(restaurantes) == 1:
                session['restaurant_id'] = restaurantes[0]['id']
                session['restaurant_name'] = restaurantes[0]['nombre']
                logger.info(f"Usuario con un restaurante: {restaurantes[0]['nombre']}")
                return redirect('/admin/dashboard')
            else:
                logger.info("Usuario con múltiples restaurantes, redirigiendo a selección")
                return redirect('/admin/crear_restaurante')
        else:
            logger.warning(f"❌ Usuario autenticado pero no encontrado en tabla usuarios: {email}")
            flash("Usuario autenticado pero no configurado en el sistema. Contacte al administrador.", "error")
            return render_template('admin/login.html')
            
    except Exception as e:
        logger.error(f"Error en login con Supabase Auth: {str(e)}")
        # Si es error de credenciales inválidas
        if "Invalid login credentials" in str(e) or "APIError" in str(e):
            flash("Credenciales incorrectas. Verifique su email y contraseña.", "error")
            return render_template('admin/login.html')
        else:
            flash("Error interno del servidor. Intente nuevamente más tarde.", "error")
            return render_template('admin/login.html')
    
    # Si llegamos aquí, mostrar el formulario de login nuevamente
    return render_template('admin/login.html')

@admin_bp.route('/register-admin', methods=['GET', 'POST'])
def register():
    """Register new admin user"""
    if request.method == 'POST':
        username = request.form.get('username')  # Email
        nombre = request.form.get('nombre')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        logger.info(f"Intento de registro con email: {username}, nombre: {nombre}")
        
        # Validación básica
        if not username or not nombre or not password or not confirm_password:
            return render_template('admin/register.html', error="Todos los campos son obligatorios")
        
        if password != confirm_password:
            return render_template('admin/register.html', error="Las contraseñas no coinciden")
        
        if len(password) < 6:
            return render_template('admin/register.html', error="La contraseña debe tener al menos 6 caracteres")
        
        try:
            # Usar servicio robusto de Supabase
            supabase_client = get_supabase_client()
            
            if not supabase_client:
                logger.error("❌ No se pudo obtener cliente Supabase durante registro")
                return render_template('admin/register.html', error="Error de configuración del servidor. Por favor contacte al administrador.")
            
            # Verificar si el email ya existe usando servicio robusto
            def check_existing_user():
                return supabase_client.table('usuarios').select('*').eq('email', username).execute()
            
            existing_user = execute_with_retry(check_existing_user, max_retries=2)
            
            if not existing_user:
                logger.error("❌ Error verificando usuario existente")
                return render_template('admin/register.html', error="Error de conexión. Intente nuevamente.")
                
            if existing_user.data:
                return render_template('admin/register.html', error="Ya existe un usuario con este email")
            
            # Crear usuario en auth.users usando Supabase Auth con servicio robusto
            def create_auth_user():
                return supabase_client.auth.sign_up(
                    email=username,
                    password=password
                )
            
            auth_response = execute_with_retry(create_auth_user, max_retries=2)
            
            if not auth_response:
                logger.error("❌ Error creando usuario en Supabase Auth")
                return render_template('admin/register.html', error="Error creando usuario. Intente nuevamente.")
            
            if auth_response.user:
                logger.info(f"Usuario creado en auth.users: {auth_response.user.id}")
                # Crear entrada en la tabla usuarios
                user_data = {
                    "auth_user_id": str(auth_response.user.id),  # Convertir UUID a string
                    "email": username,
                    "nombre": nombre,
                    "rol": "admin"
                    # Quitar "activo": True - la columna no existe
                }
                
                logger.info(f"Intentando insertar en tabla usuarios: {user_data}")
                usuarios_response = supabase.table('usuarios').insert(user_data).execute()
                logger.info(f"Respuesta de inserción en usuarios: {usuarios_response.data}")
                
                if usuarios_response.data:
                    logger.info(f"Usuario registrado exitosamente: {username}")
                    
                    # Auto-login: Establecer sesión
                    user_id = usuarios_response.data[0]['id']
                    session['user_id'] = user_id
                    session['email'] = username
                    session['nombre'] = nombre
                    session['nombre_usuario'] = nombre  # Para compatibilidad con el template
                    session['username'] = nombre       # Para compatibilidad con el template
                    session['rol'] = 'admin'
                    session['is_authenticated'] = True
                    
                    logger.info(f"Usuario auto-logueado después del registro: {dict(session)}")
                    logger.info(f"Redirigiendo a crear_restaurante...")
                    
                    # Redirigir a crear restaurante con mensaje de bienvenida
                    flash(f"¡Bienvenido {nombre}! Ahora vamos a configurar tu restaurante.", "success")
                    return redirect('/admin/crear_restaurante?from_register=true')
                else:
                    logger.error("Error: No se pudo insertar en tabla usuarios")
                    return render_template('admin/register.html', error="Error al crear el perfil de usuario")
            else:
                logger.error(f"Error al crear usuario en auth.users: {auth_response}")
                error_msg = "Error al crear la cuenta de usuario"
                if hasattr(auth_response, 'error') and auth_response.error:
                    error_msg = f"Error: {auth_response.error.message}"
                    logger.error(f"Error específico: {auth_response.error.message}")
                return render_template('admin/register.html', error=error_msg)
                
        except Exception as e:
            logger.error(f"Error en registro de usuario: {e}", exc_info=True)
            return render_template('admin/register.html', error="Error interno del servidor")
    
    # GET request - mostrar formulario de registro
    return render_template('admin/register.html')

DEFAULT_RESTAURANT_DATA = {
    "name": "Nombre no definido",
    "description": "Descripción no disponible.",
    "location": {
        "address": "", "city": "", "postal_code": "", "country": "",
        "latitude": None, "longitude": None, "google_maps_link": ""
    },
    "contact": {
        "phone": "", "email": "", "website": "", "whatsapp": ""
    },
    "opening_hours": {  # MODIFIED structure and day names
        day: {"is_closed": False, "slots": [{"open": "09:00", "close": "17:00"}]}
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    },
    "capacity": {
        "max_capacity": 0,
        "tables_indoor": 0,
        "tables_outdoor": 0
    },
    "cuisine_type": [],
    "price_range": "$$",
    "payment_methods": ["efectivo"],
    "promotions": [],
    "reservations_policy": "",
    "cancellation_policy": "",
    "dress_code": "",
    "children_policy": "",
    "pet_policy": "",
    "accessibility": {
        "wheelchair_accessible": False,
        "braille_menu": False
    },
    "special_features": [],
    "parking_info": "",
    "public_transport_access": "",
    "social_media": {
        "facebook": "", "instagram": "", "twitter": ""
    },
    "images": {
        "logo_url": "", "banner_url": "", "gallery": []
    },
    "settings": {
        "allow_online_reservations": True,
        "reservation_confirmation_message": "Tu reserva ha sido confirmada.",
        "max_party_size_online": 8,
        "min_notice_hours_online_reservacion": 2
    },
    "legal": {
        "privacy_policy_url": "", "terms_of_service_url": ""
    },
    "como_llegar": {
        "texto_transporte_publico": "",
        "texto_auto": ""
    },
    "config": {
        "activo": True,
        "mostrar_ubicacion_mapa": True
    }
}

import os
import json

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_id_from_session = session.get('user_id') # This is public.usuarios.id
    nombre_usuario = session.get('nombre_usuario', 'Usuario')
    
    logger.info(f"Dashboard: Estado de sesión al inicio: {dict(session)}")

    # Initialize status variables
    status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
    status_counts = [0, 0, 0, 0]  # Initialize with zeros

    # Get the actual admin_id (auth.users.id) to be used for querying 'restaurantes' table
    actual_admin_id = None
    if user_id_from_session:
        try:
            user_profile_response = supabase.table('usuarios').select('auth_user_id').eq('id', user_id_from_session).single().execute()
            if user_profile_response.data and user_profile_response.data.get('auth_user_id'):
                actual_admin_id = user_profile_response.data['auth_user_id']
                logger.info(f"Dashboard: Session user_id '{user_id_from_session}' maps to auth_user_id (admin_id for restaurantes): '{actual_admin_id}'")
            else:
                logger.error(f"Dashboard: Could not retrieve auth_user_id for session user_id: {user_id_from_session}")
                flash("Error de perfil de usuario. No se pudo verificar la identidad.", "error")
                return redirect('/admin/login')
        except Exception as e:
            logger.error(f"Dashboard: Error fetching auth_user_id for session user_id {user_id_from_session}: {e}")
            flash("Error al obtener detalles del perfil de usuario.", "error")
            return redirect('/admin/login')
    else:
        # This case should ideally be caught by @login_required, but as a safeguard:
        logger.error("Dashboard: user_id not found in session even after @login_required.")
        flash("Error de sesión. Por favor, inicia sesión de nuevo.", "error")
        return redirect('/admin/login')

    current_restaurant_id = session.get('restaurant_id')
    logger.info(f"Dashboard check: user_id_from_session='{user_id_from_session}', actual_admin_id='{actual_admin_id}', current_restaurant_id_from_session='{current_restaurant_id}'")

    if current_restaurant_id:
        try:
            logger.info(f"Dashboard: Verificando validez del restaurante en sesión: {current_restaurant_id} para actual_admin_id {actual_admin_id}")
            # Use actual_admin_id for verification
            response = supabase.table('restaurantes').select('id, nombre').eq('id', current_restaurant_id).eq('admin_id', actual_admin_id).execute()
            
            if response.data and len(response.data) == 1:
                restaurant_data = response.data[0]
                logger.info(f"Dashboard: Restaurante {restaurant_data['nombre']} ({current_restaurant_id}) es válido y está en sesión. Renderizando dashboard.")
                session['restaurant_name'] = restaurant_data.get('nombre', 'Restaurante sin nombre')
            else:
                if not response.data or len(response.data) == 0:
                    logger.warning(f"Dashboard: Restaurante en sesión ({current_restaurant_id}) no encontrado para actual_admin_id {actual_admin_id} o no pertenece al usuario. Limpiando de sesión.")
                elif len(response.data) > 1:
                    logger.error(f"Dashboard: Múltiples restaurantes encontrados para ID {current_restaurant_id} y actual_admin_id {actual_admin_id}. Esto es inesperado. Limpiando de sesión.")
                
                session.pop('restaurant_id', None)
                session.pop('restaurant_name', None)
                current_restaurant_id = None
        except Exception as e:
            logger.error(f"Dashboard: Excepción crítica verificando restaurante en sesión: {e}. Limpiando de sesión.", exc_info=True)
            session.pop('restaurant_id', None)
            session.pop('restaurant_name', None)
            current_restaurant_id = None

    if not current_restaurant_id:
        logger.info(f"Dashboard: No hay restaurante válido en sesión para el usuario con actual_admin_id: '{actual_admin_id}'. Buscando restaurantes asociados.")
        try:
            logger.info(f"Dashboard: Querying 'restaurantes' table for admin_id = '{actual_admin_id}' (type: {type(actual_admin_id)}).")
            # Select without 'activo' initially, derive it from 'estado' later
            # Use actual_admin_id for querying restaurants
            restaurants_response = supabase.table('restaurantes').select('id, nombre, estado, admin_id').eq('admin_id', actual_admin_id).execute()
            
            if hasattr(restaurants_response, 'data') and hasattr(restaurants_response, 'error') and hasattr(restaurants_response, 'status_code'):
                 logger.info(f"Dashboard: Supabase raw response object: status_code={restaurants_response.status_code}, error={restaurants_response.error}, data_length={len(restaurants_response.data) if restaurants_response.data else 0}")
            else:
                 logger.info(f"Dashboard: Supabase raw response object (structure might be different): {restaurants_response}")

            user_restaurants = []
            if restaurants_response and restaurants_response.data:
                user_restaurants = restaurants_response.data
            
            logger.info(f"Dashboard: Parsed {len(user_restaurants)} restaurants for actual_admin_id '{actual_admin_id}'. Restaurants data: {user_restaurants}")

            # Process and derive 'activo' from 'estado'
            user_restaurants_processed = []
            if restaurants_response and restaurants_response.data:
                raw_restaurants = restaurants_response.data
                for r_data in raw_restaurants:
                    r_data['activo'] = (r_data.get('estado') == 'activo') # Derive 'activo'
                    user_restaurants_processed.append(r_data)
            
            logger.info(f"Dashboard: Parsed and processed {len(user_restaurants_processed)} restaurants for actual_admin_id '{actual_admin_id}'. Restaurants data: {user_restaurants_processed}")

            if not user_restaurants_processed:
                logger.info(f"Dashboard: Usuario con actual_admin_id {actual_admin_id} no tiene restaurantes (según la consulta procesada). Redirigiendo a crear_restaurante.")
                flash("No tienes restaurantes registrados o no se pudieron cargar. Crea tu primer restaurante para comenzar.", "info")
                session['from_dashboard_no_restaurants'] = True
                return redirect('/admin/crear_restaurante')
            
            elif len(user_restaurants_processed) == 1:
                selected_restaurant = user_restaurants_processed[0]
                session['restaurant_id'] = selected_restaurant['id']
                session['restaurant_name'] = selected_restaurant.get('nombre', 'Restaurante sin nombre')
                current_restaurant_id = selected_restaurant['id']
                logger.info(f"Dashboard: Usuario con actual_admin_id {actual_admin_id} tiene 1 restaurante.")
                flash(f"Trabajando con tu restaurante: {session['restaurant_name']}.", "success")
                # No redirigir, simplemente continuar para renderizar el dashboard
            
            else: # Múltiples restaurantes
                logger.info(f"Dashboard: Usuario con actual_admin_id {actual_admin_id} tiene {len(user_restaurants_processed)} restaurantes. Redirigiendo a admin.crear_restaurante.")
                flash("Tienes varios restaurantes. Por favor, selecciona con cuál deseas trabajar.", "info")
                return redirect('/admin/crear_restaurante')
                
        except Exception as e:
            logger.error(f"Dashboard: Error al obtener restaurantes para actual_admin_id {actual_admin_id}: {e}", exc_info=True)
            flash("Error al cargar la información de tus restaurantes. Intenta de nuevo.", "error")
            return redirect('/admin/crear_restaurante') 

    # 3. Si llegamos aquí, tenemos un current_restaurant_id válido (ya sea de sesión o recién asignado)
    # Proceder a cargar datos y renderizar el dashboard
    logger.info(f"Dashboard: Renderizando para usuario {user_id_from_session}, restaurante {session.get('restaurant_name')} ({current_restaurant_id})")
    
    demo_mode = is_demo_restaurant(current_restaurant_id)
    proximas_reservas_lista = []
    total_reservas_hoy = 0
    total_reservas_semana = 0
    total_reservas_mes = 0
    
    logger.info(f"Cargando dashboard para restaurant_id={current_restaurant_id}, demo_mode={demo_mode}")

    try:
        if demo_mode:
            demo_info = get_demo_restaurant_info() # Removed current_restaurant_id argument
            proximas_reservas_lista = demo_info.get('proximas_reservas', [])
            total_reservas_hoy = demo_info.get('total_reservas_hoy', 0)
            total_reservas_semana = demo_info.get('total_reservas_semana', 0)
            total_reservas_mes = demo_info.get('total_reservas_mes', 0)
        else:
            now = datetime.now(timezone.utc)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # For created_at comparisons (timestamps) - Card "Resumen"
            start_of_day_ts = start_of_day.isoformat()
            end_of_day_ts = (start_of_day + timedelta(days=1)).isoformat()

            start_of_week_dt = start_of_day - timedelta(days=now.weekday())
            start_of_week_ts = start_of_week_dt.isoformat()
            end_of_week_ts = (start_of_week_dt + timedelta(days=7)).isoformat()

            start_of_month_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_month_ts = start_of_month_dt.isoformat()
            end_of_month_ts = (start_of_month_dt + relativedelta(months=1)).isoformat()

            # For fecha comparisons (dates) - Card "Estado de Reservas" & other charts
            today_date_iso = start_of_day.date().isoformat() 
            
            # For 'fecha' based monthly charts (distinct from 'Resumen' card's created_at logic)
            legacy_month_start_date = start_of_day.replace(day=1).date()
            legacy_month_end_date = (start_of_day.replace(day=1) + relativedelta(months=1)).date()
            legacy_month_start_date_iso = legacy_month_start_date.isoformat()
            legacy_month_end_date_iso = legacy_month_end_date.isoformat()
            
            logger.info(f"[Estado de Reservas] Buscando reservas desde {legacy_month_start_date_iso} hasta {legacy_month_end_date_iso}")

            try:
                # from services.reservas.db import obtener_reservas_proximas as get_proximas # Not used here
                reservas_table = 'reservas_prod'
                id_column = 'restaurante_id'
                created_at_column = 'created_at' # For "Resumen" card
                fecha_column = 'fecha' # For "Estado de Reservas" and other charts

                logger.info(f"Consultando reservas en tabla {reservas_table} para restaurante {current_restaurant_id}")

                # Card "Estado de Reservas" (for TODAY using 'fecha')
                today_card_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
                today_card_status_counts = [0, 0, 0, 0]
                today_card_status_map = {
                    'pendiente': 0,
                    'Pendiente': 0,
                    'PENDIENTE': 0,
                    'confirmada': 1,
                    'confirmado': 1,
                    'Confirmada': 1,
                    'Confirmado': 1,
                    'CONFIRMADA': 1,
                    'CONFIRMADO': 1,
                    'cancelada': 2,
                    'cancelado': 2,
                    'Cancelada': 2,
                    'Cancelado': 2,
                    'CANCELADA': 2,
                    'CANCELADO': 2,
                    'no asistio': 3,
                    'no_asistio': 3,
                    'No asistio': 3,
                    'No asistió': 3,
                    'NO ASISTIO': 3,
                    'NO ASISTIÓ': 3
                }
                
                estado_rows_for_today_card_data = []
                try:
                    # Debug current state
                    logger.info(f"[Estado de Reservas] Querying for today ({today_date_iso})")
                    logger.info(f"[Estado de Reservas] Restaurant ID: {current_restaurant_id}")
                    
                    # First get all reservations regardless of date to check data
                    test_query = (supabase.table(reservas_table)
                        .select('estado, fecha')
                        .eq(id_column, current_restaurant_id)
                        .execute())
                    
                    if hasattr(test_query, 'data'):
                        logger.info(f"[Estado de Reservas] Total reservations found: {len(test_query.data)}")
                        if test_query.data:
                            logger.info(f"[Estado de Reservas] Sample reservation: {test_query.data[0]}")
                            # Log unique estados found
                            estados = set(r.get('estado', '').strip().lower() for r in test_query.data if r.get('estado'))
                            logger.info(f"[Estado de Reservas] Unique estados found: {estados}")
                    
                        # Get current month's reservations for the status card
                    all_reservas_response = (supabase.table(reservas_table)
                        .select('*')
                        .eq(id_column, current_restaurant_id)
                        .gte(fecha_column, legacy_month_start_date_iso)
                        .lt(fecha_column, legacy_month_end_date_iso)
                        .execute())

                    # Log raw data for debugging
                    if hasattr(all_reservas_response, 'data') and all_reservas_response.data:
                        estado_rows_for_today_card_data = all_reservas_response.data
                        logger.info(f"[Estado de Reservas] Found {len(estado_rows_for_today_card_data)} reservations for current month")
                        # Log each reservation's estado for debugging
                        for idx, res in enumerate(estado_rows_for_today_card_data):
                            logger.info(f"[Estado de Reservas] Reservation {idx + 1}: estado='{res.get('estado')}', fecha='{res.get('fecha')}'")
                    else:
                        logger.info("[Estado de Reservas] No reservations found for current month")
                except Exception as e_usuarios:
                    logger.error(f"[Estado de Reservas] Error fetching data: {e_usuarios}", exc_info=True)

                today_card_status_counts = [0, 0, 0, 0] 
                # Reset counters
                today_card_status_counts = [0, 0, 0, 0]
                
                if estado_rows_for_today_card_data:
                    estado_processed = {}  # For debugging
                    for record in estado_rows_for_today_card_data:
                        estado = record.get('estado', '')
                        if estado:
                            estado_original = estado
                            estado = estado.strip()
                            
                            # Map estados directamente sin normalización
                            status_index = None
                            
                            # Pendiente
                            if estado in ['Pendiente', 'PENDIENTE', 'pendiente']:
                                status_index = 0
                            # Confirmada/Confirmado
                            elif estado in ['Confirmada', 'CONFIRMADA', 'confirmada', 'Confirmado', 'CONFIRMADO', 'confirmado']:
                                status_index = 1
                            # Cancelada/Cancelado
                            elif estado in ['Cancelada', 'CANCELADA', 'cancelada', 'Cancelado', 'CANCELADO', 'cancelado']:
                                status_index = 2
                            # No asistió
                            elif estado in ['No asistió', 'NO ASISTIÓ', 'no asistió', 'No asistio', 'NO ASISTIO', 'no asistio']:
                                status_index = 3
            
                            if status_index is not None:
                                today_card_status_counts[status_index] += 1
                                estado_processed[estado] = estado_processed.get(estado, 0) + 1
                                logger.info(f"[Estado de Reservas] Procesado estado: {estado_original} -> índice {status_index} -> {today_card_status_labels[status_index]}")
                            else:
                                logger.warning(f"[Estado de Reservas] Estado no reconocido: {estado_original}")
    
                    # Log detailed estado processing
                    logger.info(f"[Estado de Reservas] Processed estados (raw): {estado_processed}")
                    logger.info(f"[Estado de Reservas] Final counts by estado: {dict(zip(today_card_status_labels, today_card_status_counts))}")
                    logger.info(f"[Estado de Reservas] Total reservations processed: {sum(today_card_status_counts)}")
                
                logger.info(f"[Estado de Reservas] Final counts: {dict(zip(today_card_status_labels, today_card_status_counts))}")

                # Card "Resumen" (Counts using 'created_at')
                logger.info(f"Querying for 'Resumen' card using '{created_at_column}'")

                # Hoy (created_at)
                logger.info(f"Resumen - Hoy: Querying {created_at_column} between {start_of_day_ts} and {end_of_day_ts}")
                count_response_hoy = (supabase.table(reservas_table)
                    .select('id', count='exact')
                    .eq(id_column, current_restaurant_id)
                    .gte(created_at_column, start_of_day_ts)
                    .lt(created_at_column, end_of_day_ts)
                    .execute())
                total_reservas_hoy = count_response_hoy.count if hasattr(count_response_hoy, 'count') and count_response_hoy.count is not None else 0
                logger.info(f"Resumen - Hoy: Found {total_reservas_hoy} reservations (using {created_at_column})")

                # Semana (created_at)
                logger.info(f"Resumen - Semana: Querying {created_at_column} between {start_of_week_ts} and {end_of_week_ts}")
                count_response_semana = (supabase.table(reservas_table)
                    .select('id', count='exact')
                    .eq(id_column, current_restaurant_id)
                    .gte(created_at_column, start_of_week_ts)
                    .lt(created_at_column, end_of_week_ts)
                    .execute())
                total_reservas_semana = count_response_semana.count if hasattr(count_response_semana, 'count') and count_response_semana.count is not None else 0
                logger.info(f"Resumen - Semana: Found {total_reservas_semana} reservations (using {created_at_column})")
                
                # Mes (created_at)
                logger.info(f"Resumen - Mes: Querying {created_at_column} between {start_of_month_ts} and {end_of_month_ts}")
                count_response_mes = (supabase.table(reservas_table)
                    .select('id', count='exact')
                    .eq(id_column, current_restaurant_id)
                    .gte(created_at_column, start_of_month_ts)
                    .lt(created_at_column, end_of_month_ts)
                    .execute())
                total_reservas_mes = count_response_mes.count if hasattr(count_response_mes, 'count') and count_response_mes.count is not None else 0
                logger.info(f"Resumen - Mes: Found {total_reservas_mes} reservations (using {created_at_column})")

                logger.info(f"Resumen de conteos ({created_at_column}) - hoy: {total_reservas_hoy}, semana: {total_reservas_semana}, mes: {total_reservas_mes}")

                # Monthly status chart (using 'fecha')
                monthly_chart_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"] 
                monthly_chart_status_counts = [0, 0, 0, 0] 
                monthly_chart_status_map = {
                    'pendiente': 0,
                    'Pendiente': 0,
                    'PENDIENTE': 0,
                    'confirmada': 1,
                    'confirmado': 1,
                    'Confirmada': 1,
                    'Confirmado': 1,
                    'CONFIRMADA': 1,
                    'CONFIRMADO': 1,
                    'cancelada': 2,
                    'cancelado': 2,
                    'Cancelada': 2,
                    'Cancelado': 2,
                    'CANCELADA': 2,
                    'CANCELADO': 2,
                    'no asistio': 3,
                    'no_asistio': 3,
                    'No asistio': 3,
                    'No asistió': 3,
                    'NO ASISTIO': 3,
                    'NO ASISTIÓ': 3
                }
                try:
                    logger.info(f"Querying for monthly status chart using '{fecha_column}' between {legacy_month_start_date_iso} and {legacy_month_end_date_iso}")
                    estado_rows_for_monthly_chart = (supabase.table(reservas_table)
                        .select('estado')
                        .eq(id_column, current_restaurant_id)
                        .gte(fecha_column, legacy_month_start_date_iso)
                        .lt(fecha_column, legacy_month_end_date_iso)
                        .execute())

                    if hasattr(estado_rows_for_monthly_chart, 'data') and estado_rows_for_monthly_chart.data:
                        _internal_monthly_chart_counter = {}
                        for record in estado_rows_for_monthly_chart.data:
                            estado_db = record.get('estado', '').strip()
                            estado_original = estado_db
                            estado_db = estado_db.lower()
                            
                            # Map estados directamente sin normalización
                            status_index = None
                            
                            # Pendiente
                            if estado_db in ['pendiente']:
                                status_index = 0
                            # Confirmada/Confirmado
                            elif estado_db in ['confirmada', 'confirmado']:
                                status_index = 1
                            # Cancelada/Cancelado
                            elif estado_db in ['cancelada', 'cancelado']:
                                status_index = 2
                            # No asistió
                            elif estado_db in ['no asistió', 'no asistio']:
                                status_index = 3

                            if status_index is not None:
                                monthly_chart_status_counts[status_index] += 1
                                logger.info(f"[Monthly Chart] Procesado estado: {estado_original} -> índice {status_index} -> {monthly_chart_status_labels[status_index]}")
                            else:
                                logger.warning(f"[Monthly Chart] Estado no reconocido: {estado_original}")
                        
                        logger.info(f"[Monthly Chart] Final counts: {dict(zip(monthly_chart_status_labels, monthly_chart_status_counts))}")
                    logger.info(f"Monthly chart status_counts: {monthly_chart_status_counts}")
                except Exception as e:
                    logger.error(f"Error processing monthly status chart data (using {fecha_column}): {e}", exc_info=True)
                    monthly_chart_status_counts = [0,0,0,0]

                # Top Clientes chart data (using confirmed reservations)
                top_clientes_labels_chart = []
                top_clientes_counts_chart = []
                try:
                    logger.info("[Top Clientes] Starting query")
                    
                    three_months_ago_dt_chart = start_of_month_dt - relativedelta(months=3)
                    today_dt_chart = now.date()
                    three_months_ago_iso_chart = three_months_ago_dt_chart.date().isoformat()
                    today_iso_chart = today_dt_chart.isoformat()

                    logger.info(f"Calculando top clientes desde {three_months_ago_iso_chart} hasta {today_iso_chart}")
                    
                    # Query all reservations for the date range with the correct column name
                    raw_response = (supabase.table(reservas_table)
                        .select('nombre_cliente, estado, fecha')  # Using correct column name 'nombre_cliente'
                        .eq(id_column, current_restaurant_id)
                        .gte(fecha_column, three_months_ago_iso_chart)
                        .lt(fecha_column, today_iso_chart)
                        .execute())

                    if hasattr(raw_response, 'data') and raw_response.data:
                        logger.info(f"[Top Clientes] Found {len(raw_response.data)} total reservations")
                        
                        client_confirmations = {}
                        for res in raw_response.data:
                            estado = res.get('estado', '').strip().lower()
                            # Only count confirmed reservations
                            if estado in ['confirmada', 'confirmado']:
                                client_name = res.get('nombre_cliente', 'Sin nombre').strip()  # Using correct column name
                                if client_name:
                                    client_confirmations[client_name] = client_confirmations.get(client_name, 0) + 1
                                    logger.info(f"Confirmed reservation - Cliente: {client_name}, Estado: {estado}")
            
                        logger.info(f"[Top Clientes] Client confirmations: {client_confirmations}")
            
                        # Convert to sorted list and take top 5
                        sorted_clients = sorted(client_confirmations.items(), key=lambda x: x[1], reverse=True)[:5]
                        if sorted_clients:
                            # Unzip the sorted pairs into two lists
                            top_clientes_labels_chart = [name for name, _ in sorted_clients]
                            top_clientes_counts_chart = [count for _, count in sorted_clients]
                            logger.info(f"[Top Clientes] Final data: {dict(zip(top_clientes_labels_chart, top_clientes_counts_chart))}")
                        else:
                            logger.info("[Top Clientes] No confirmed reservations found for any client")
                    else:
                        logger.info("[Top Clientes] No reservations data found")

                except Exception as e:
                    logger.error(f"[Top Clientes] Error processing chart data: {e}", exc_info=True)
                    top_clientes_labels_chart = []
                    top_clientes_counts_chart = []

                # Daily data for current month chart (using 'fecha')
                dias_labels_chart = []
                reservas_counts_daily_chart = [] 
                personas_counts_diarias_chart = [] 
                ocupacion_diaria_pct_chart = [] 
                try:
                    current_chart_day_dt = start_of_month_dt 
                    while current_chart_day_dt.date() <= now.date(): 
                        day_label_for_chart = current_chart_day_dt.strftime('%d/%m')
                        dias_labels_chart.append(day_label_for_chart)
                        
                        day_iso_start = current_chart_day_dt.date().isoformat()
                        day_iso_end = (current_chart_day_dt.date() + timedelta(days=1)).isoformat()

                        logger.debug(f"Daily chart: querying '{fecha_column}' between {day_iso_start} and {day_iso_end}")
                        day_reservas_for_chart = (supabase.table(reservas_table)
                            .select('id, personas')
                            .eq(id_column, current_restaurant_id)
                            .gte(fecha_column, day_iso_start)
                            .lt(fecha_column, day_iso_end)
                            .execute())

                        reservas_count_for_day = len(day_reservas_for_chart.data) if hasattr(day_reservas_for_chart, 'data') and day_reservas_for_chart.data else 0
                        personas_count_for_day = sum(r.get('personas', 0) for r in (day_reservas_for_chart.data or []))
                        
                        reservas_counts_daily_chart.append(reservas_count_for_day)
                        personas_counts_diarias_chart.append(personas_count_for_day)
                        
                        # Get max_capacity from restaurant-specific info file
                        restaurant_info = {}
                        try:
                            info_file_path = os.path.join(current_app.root_path, 'data', 'info', f'{current_restaurant_id}_info.json')
                            with open(info_file_path, 'r') as f:
                                restaurant_info = json.load(f)
                            max_capacity = int(restaurant_info.get('capacity', {}).get('max_capacity', 100))
                            logger.debug(f"Max capacity loaded from {info_file_path}: {max_capacity}")
                        except Exception as e:
                            logger.warning(f"Could not load max_capacity from restaurant info file for {current_restaurant_id}, using default 100: {e}")
                            max_capacity = 100
                        
                        # Debug logging para investigar el problema de ocupación
                        ocupacion_pct_for_day = (personas_count_for_day / max_capacity * 100) if max_capacity > 0 else 0
                        logger.info(f"DEBUG OCUPACIÓN - Día: {current_chart_day_dt.strftime('%Y-%m-%d')}, Personas: {personas_count_for_day}, Max Capacity: {max_capacity}, Ocupación %: {ocupacion_pct_for_day:.1f}")
                        
                        ocupacion_diaria_pct_chart.append(round(ocupacion_pct_for_day, 1))
                        
                        current_chart_day_dt += timedelta(days=1)
                    logger.info(f"Datos diarios (chart - {fecha_column}) generados - días: {len(dias_labels_chart)}")
                except Exception as e:
                    logger.error(f"Error processing daily chart data (using {fecha_column}): {e}", exc_info=True)
                    dias_labels_chart, reservas_counts_daily_chart, personas_counts_diarias_chart, ocupacion_diaria_pct_chart = [], [], [], []
                
                # Monthly Trend chart (using 'fecha')
                month_labels_trend = []
                reservation_trend_counts = []
                confirmed_trend_counts = []
                pending_trend_counts = []
                no_asistio_trend_counts = []
                canceladas_trend_counts = []
                try:
                    for i in range(5, -1, -1):
                        month_start_dt_trend = start_of_month_dt - relativedelta(months=i)
                        month_end_dt_trend = month_start_dt_trend + relativedelta(months=1)
                        
                        month_label_for_trend = month_start_dt_trend.strftime('%B %Y')
                        month_labels_trend.append(month_label_for_trend)
                        
                        month_start_iso_trend = month_start_dt_trend.date().isoformat()
                        month_end_iso_trend = month_end_dt_trend.date().isoformat()

                        total_response_trend = (supabase.table(reservas_table)
                            .select('id', count='exact')
                            .eq(id_column, current_restaurant_id)
                            .gte(fecha_column, month_start_iso_trend)
                            .lt(fecha_column, month_end_iso_trend)
                            .execute())
                        reservation_trend_counts.append(total_response_trend.count if hasattr(total_response_trend, 'count') and total_response_trend.count is not None else 0)
                        
                        month_estado_rows_trend = (supabase.table(reservas_table)
                            .select('estado')
                            .eq(id_column, current_restaurant_id)
                            .gte(fecha_column, month_start_iso_trend)
                            .lt(fecha_column, month_end_iso_trend)
                            .execute())
                        
                        estado_counts_map_for_trend = {'pendiente': 0, 'confirmada': 0, 'cancelada': 0, 'no_asistio': 0}
                        if hasattr(month_estado_rows_trend, 'data') and month_estado_rows_trend.data:
                            for record in month_estado_rows_trend.data:
                                estado_db_trend = record.get('estado', '').strip().lower()
                                if estado_db_trend == "no asistio": # Handle space
                                    estado_db_trend = "no_asistio"
                                if estado_db_trend in estado_counts_map_for_trend:
                                    estado_counts_map_for_trend[estado_db_trend] += 1
                        
                        confirmed_trend_counts.append(estado_counts_map_for_trend['confirmada'])
                        pending_trend_counts.append(estado_counts_map_for_trend['pendiente'])
                        no_asistio_trend_counts.append(estado_counts_map_for_trend['no_asistio'])
                        canceladas_trend_counts.append(estado_counts_map_for_trend['cancelada'])
                    logger.info(f"Monthly trend data (using {fecha_column}) generated for {len(month_labels_trend)} months.")
                except Exception as e:
                    logger.error(f"Error generating monthly trend data (using {fecha_column}): {e}", exc_info=True)
                    month_labels_trend, reservation_trend_counts, confirmed_trend_counts, pending_trend_counts, no_asistio_trend_counts, canceladas_trend_counts = [],[],[],[],[],[]

                # Top Clients chart (using 'fecha')
                top_clientes_labels_chart = []
                top_clientes_counts_chart = []
                try:
                    three_months_ago_dt_chart = start_of_month_dt - relativedelta(months=3)
                    today_dt_chart = now.date()
                    three_months_ago_iso_chart = three_months_ago_dt_chart.date().isoformat()
                    today_iso_chart = today_dt_chart.isoformat()

                    logger.info(f"Calculando top clientes desde {three_months_ago_iso_chart} hasta {today_iso_chart}")
                    logger.info(f"Buscando top clientes con: restaurant_id={current_restaurant_id}, desde={three_months_ago_iso_chart}, hasta={today_iso_chart}")

                    # Add detailed debug logging for top clientes query
                    logger.info(f"Top clientes - Comprobando la tabla '{reservas_table}'")
                    test_response = (supabase.table(reservas_table)
                        .select('nombre_cliente, estado, fecha')  # Changed to use correct column name
                        .eq(id_column, current_restaurant_id)
                        .execute())
                    logger.info(f"Total reservations for restaurant: {len(test_response.data) if hasattr(test_response, 'data') and test_response.data else 0}")
                    
                    test_response_confirmed = (supabase.table(reservas_table)
                        .select('nombre_cliente, estado, fecha')
                        .eq(id_column, current_restaurant_id)
                        .eq('estado', 'Confirmada')
                        .execute())
                    logger.info(f"Total confirmed reservations for restaurant: {len(test_response_confirmed.data) if hasattr(test_response_confirmed, 'data') and test_response_confirmed.data else 0}")
                    if hasattr(test_response_confirmed, 'data') and test_response_confirmed.data:
                        logger.info(f"Sample confirmed reservation: {test_response_confirmed.data[0]}")

                    # Debug date filters
                    logger.info(f"Filtros de fecha: {fecha_column} >= {three_months_ago_iso_chart} and < {today_iso_chart}")

                    # Query all reservations for the date range first
                    top_clients_response = (supabase.table(reservas_table)
                        .select('nombre_cliente, estado, fecha')  # Changed to use correct column name
                        .eq(id_column, current_restaurant_id)
                        .gte(fecha_column, three_months_ago_iso_chart)
                        .lt(fecha_column, today_iso_chart)
                        .execute())

                    logger.info(f"Total reservations found: {len(top_clients_response.data) if hasattr(top_clients_response, 'data') else 0}")

                    if hasattr(top_clients_response, 'data') and top_clients_response.data:
                        client_confirmations = {}
                        for res in top_clients_response.data:
                            estado = res.get('estado', '').strip().lower()
                            # Only count confirmed reservations
                            # Case-insensitive check for 'Confirmada' status
                            if estado in ['confirmada', 'confirmado', 'Confirmada', 'Confirmado']:
                                client_name = res.get('nombre_cliente', 'Sin nombre').strip()
                                fecha = res.get('fecha', '')
                                if client_name and client_name != 'Sin nombre':
                                    client_confirmations[client_name] = client_confirmations.get(client_name, 0) + 1
                                    logger.info(f"Confirmed reservation - Cliente: {client_name}, Fecha: {fecha}, Estado: {estado}")
                                
                        logger.info(f"Top clientes encontrados: {client_confirmations}")
                        
                        sorted_clients = sorted(client_confirmations.items(), key=lambda item: item[1], reverse=True)[:8] # Top 8
                        for name, count_val in sorted_clients:
                            top_clientes_labels_chart.append(name)
                            top_clientes_counts_chart.append(count_val)
                    logger.info(f"Top clients data (using {fecha_column}) generated: {len(top_clientes_labels_chart)} clients.")
                except Exception as e:
                    logger.error(f"Error generating top clients data (using {fecha_column}): {e}", exc_info=True)
                    top_clientes_labels_chart, top_clientes_counts_chart = [], []

                # Obtener próximas reservas
                try:
                    logger.info("Obteniendo próximas reservas para el dashboard")
                    proximas_response = supabase.table(reservas_table).select('*').eq(id_column, current_restaurant_id).gte('fecha', now.date().isoformat()).neq('estado', 'Cancelada').order('fecha', desc=False).order('hora', desc=False).limit(10).execute()
                    
                    if proximas_response.data:
                        proximas_reservas_lista = proximas_response.data
                        logger.info(f"Cargadas {len(proximas_reservas_lista)} próximas reservas para el dashboard")
                    else:
                        proximas_reservas_lista = []
                        logger.info("No se encontraron próximas reservas")
                except Exception as e:
                    logger.error(f"Error obteniendo próximas reservas: {e}", exc_info=True)
                    proximas_reservas_lista = []
                
                logger.info(f"Dashboard data preparation complete.")
                
            except Exception as e:
                logger.error(f"Critical error during dashboard data preparation block: {e}", exc_info=True)
                # Initialize all potentially undefined variables to safe defaults for the template
                today_card_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
                today_card_status_counts = [0,0,0,0]
                total_reservas_hoy, total_reservas_semana, total_reservas_mes = 0,0,0
                monthly_chart_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
                monthly_chart_status_counts = [0,0,0,0]
                dias_labels_chart, reservas_counts_daily_chart, personas_counts_diarias_chart, ocupacion_diaria_pct_chart = [],[],[],[]
                month_labels_trend, reservation_trend_counts, confirmed_trend_counts, pending_trend_counts, no_asistio_trend_counts, canceladas_trend_counts = [],[],[],[],[],[]
                top_clientes_labels_chart, top_clientes_counts_chart = [], []

    except Exception as e: # Outer try-except for restaurant loading logic
        logger.error(f"Outer error fetching dashboard data (restaurant loading phase) for restaurant {current_restaurant_id}: {e}", exc_info=True)
        flash(f"Error al cargar datos del dashboard: {e}", "error")
        # Safe defaults for all template variables if outer error
        nombre_usuario = session.get('nombre_usuario', 'Usuario')
        proximas_reservas_lista = []
        today_card_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
        today_card_status_counts = [0,0,0,0]
        total_reservas_hoy, total_reservas_semana, total_reservas_mes = 0,0,0
        monthly_chart_status_labels = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
        monthly_chart_status_counts = [0,0,0,0]
        dias_labels_chart, reservas_counts_daily_chart, personas_counts_diarias_chart, ocupacion_diaria_pct_chart = [],[],[],[]
        month_labels_trend, reservation_trend_counts, confirmed_trend_counts, pending_trend_counts, no_asistio_trend_counts, canceladas_trend_counts = [],[],[],[],[],[]
        top_clientes_labels_chart, top_clientes_counts_chart = [], []
        demo_mode = False # Assume not demo mode on error
        current_month_label_for_template = datetime.now(timezone.utc).strftime('%B %Y')
        # Ensure next_url is defined in this error path if it's used in render_template
        next_url = '/admin/dashboard' # Default redirect or error page


    current_month_label_for_template = datetime.now(timezone.utc).strftime('%B %Y')

    # Ensure all variables passed to render_template are defined
    # These will take values from the 'try' block if successful, or defaults from 'except' blocks if errors occurred.
    
    # For "Resumen" card (counts by created_at)
    # today_count, week_count, month_count will be total_reservas_hoy, etc.

    # For "Estado de Reservas" card (today's status by fecha)
    # status_labels, status_counts will be today_card_status_labels, etc.
    
    # For other charts (ensure they use the chart-specific suffixed variables)

    return render_template('admin/dashboard.html',
                           nombre_usuario=session.get('nombre_usuario', 'Usuario'), # Ensure nombre_usuario is always defined
                           restaurant_name=session.get('restaurant_name', 'N/A'),
                           proximas_reservas=proximas_reservas_lista if 'proximas_reservas_lista' in locals() else [],
                           
                           # For "Resumen" card (counts by created_at)
                           today_count=total_reservas_hoy if 'total_reservas_hoy' in locals() else 0,
                           week_count=total_reservas_semana if 'total_reservas_semana' in locals() else 0,
                           month_count=total_reservas_mes if 'total_reservas_mes' in locals() else 0,

                           # For "Estado de Reservas" card (today's status by fecha)
                           status_labels=today_card_status_labels if 'today_card_status_labels' in locals() else ["Pendiente", "Confirmada", "Cancelada", "No asistió"], 
                           status_counts=today_card_status_counts if 'today_card_status_counts' in locals() else [0,0,0,0],
                           
                           # For "Evolución" (Monthly Trend chart - by fecha)
                           month_labels=month_labels_trend if 'month_labels_trend' in locals() else [],
                           reservation_trend=reservation_trend_counts if 'reservation_trend_counts' in locals() else [],
                           confirmed_trend=confirmed_trend_counts if 'confirmed_trend_counts' in locals() else [],
                           pending_trend=pending_trend_counts if 'pending_trend_counts' in locals() else [],
                           no_asistio_trend=no_asistio_trend_counts if 'no_asistio_trend_counts' in locals() else [],
                           canceladas_trend=canceladas_trend_counts if 'canceladas_trend_counts' in locals() else [],
                           
                           # For "Reservas Diarias" chart (by fecha)
                           dias_labels=dias_labels_chart if 'dias_labels_chart' in locals() else [],
                           reservas_counts=reservas_counts_daily_chart if 'reservas_counts_daily_chart' in locals() else [], 
                           personas_counts_diarias=personas_counts_diarias_chart if 'personas_counts_diarias_chart' in locals() else [], 
                           ocupacion_diaria_pct=ocupacion_diaria_pct_chart if 'ocupacion_diaria_pct_chart' in locals() else [], 
                           
                           # For "Top Clientes" chart (by fecha)
                           top_clientes_labels=top_clientes_labels_chart if 'top_clientes_labels_chart' in locals() else [],
                           top_clientes_counts=top_clientes_counts_chart if 'top_clientes_counts_chart' in locals() else [],
                           
                           current_month_label=current_month_label_for_template,
                           demo_mode=demo_mode if 'demo_mode' in locals() else False,
                           tiene_datos=( (total_reservas_hoy if 'total_reservas_hoy' in locals() else 0) + 
                                         (total_reservas_semana if 'total_reservas_semana' in locals() else 0) + 
                                         (total_reservas_mes if 'total_reservas_mes' in locals() else 0) > 0),
                           next_url=next_url if 'next_url' in locals() else '/admin/dashboard' # Ensure next_url is defined
                           )

@admin_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session
    session.clear()
    flash("Has cerrado sesión exitosamente.", "success")
    return redirect('/admin/login')

@admin_bp.route('/crear_restaurante', methods=['GET', 'POST'])
@login_required
def crear_restaurante():
    if request.method == 'GET':
        return render_template('admin/restaurantes/nuevo.html')
    
    # POST - crear restaurante
    flash("Funcionalidad de crear restaurante en desarrollo", "info")
    return redirect('/admin/dashboard')

@admin_bp.route('/feedback', methods=['GET'])
@login_required
def feedback():
    """Mostrar feedback de clientes"""
    restaurant_id = session.get('restaurant_id')
    restaurant_name = session.get('restaurant_name', 'Restaurante')
    
    if not restaurant_id:
        flash("Por favor, selecciona un restaurante primero.", "warning")
        return redirect(url_for('admin.select_restaurant'))
    
    # Cargar feedback desde Supabase
    feedbacks = []
    estadisticas = {
        'total_feedbacks': 0,
        'promedio_puntuacion': 0,
        'distribuccion_puntuaciones': [0, 0, 0, 0, 0],  # índices 0-4 para puntuaciones 1-5
        'porcentajes_puntuaciones': [0, 0, 0, 0, 0]  # porcentajes calculados
    }
    
    try:
        from db.supabase_client import supabase
        
        # Obtener todos los feedbacks del restaurante
        response = supabase.table('feedback').select('*').eq('restaurante_id', restaurant_id).order('fecha_feedback', desc=True).execute()
        
        if response.data:
            feedbacks = response.data
            
            # Procesar fechas para convertir strings a datetime objects
            for feedback in feedbacks:
                if feedback.get('fecha_feedback') and isinstance(feedback['fecha_feedback'], str):
                    try:
                        # Convertir string a datetime
                        from datetime import datetime
                        feedback['fecha_feedback'] = datetime.fromisoformat(feedback['fecha_feedback'].replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"Error convirtiendo fecha {feedback['fecha_feedback']}: {e}")
                        feedback['fecha_feedback'] = None
            
            estadisticas['total_feedbacks'] = len(feedbacks)
            
            # Calcular estadísticas
            puntuaciones = [f.get('puntuacion', 0) for f in feedbacks if f.get('puntuacion')]
            if puntuaciones:
                estadisticas['promedio_puntuacion'] = round(sum(puntuaciones) / len(puntuaciones), 1)
                
                # Distribución de puntuaciones
                for puntuacion in puntuaciones:
                    if 1 <= puntuacion <= 5:
                        estadisticas['distribuccion_puntuaciones'][puntuacion - 1] += 1
                
                # Calcular porcentajes
                total = estadisticas['total_feedbacks']
                if total > 0:
                    for i in range(5):
                        count = estadisticas['distribuccion_puntuaciones'][i]
                        porcentaje = (count / total * 100) if total > 0 else 0
                        estadisticas['porcentajes_puntuaciones'][i] = round(porcentaje, 1)
        
        logger.info(f"Feedback: Cargados {len(feedbacks)} feedbacks para restaurante {restaurant_id}")
        
    except Exception as e:
        logger.error(f"Error cargando feedback: {e}")
        flash("Error al cargar los feedbacks", "error")
    
    # Debug info
    debug_info = {
        'session_restaurant_id': session.get('restaurant_id'),
        'session_keys': list(session.keys()),
        'feedbacks_count': len(feedbacks),
        'estadisticas': estadisticas
    }
    
    return render_template('admin/feedback.html',
                         restaurant_name=restaurant_name or 'Restaurante',
                         username=session.get('nombre_usuario', session.get('username', 'Usuario')),
                         feedbacks=feedbacks or [],
                         estadisticas=estadisticas or {})

@admin_bp.route('/api/update_reservation', methods=['POST'])
@login_required
def update_reservation():
    """API endpoint to update reservation status from admin interface"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Expected JSON data'}), 400
        
        data = request.json
        reserva_id = data.get('id')
        nuevo_estado = data.get('estado')
        
        if not reserva_id or not nuevo_estado:
            return jsonify({
                'success': False, 
                'error': 'ID de reserva y nuevo estado son requeridos'
            }), 400
            
        # Call the service function to update reservation status
        resultado = actualizar_estado_reserva(reserva_id, nuevo_estado)
        
        if resultado.get('success'):
            return jsonify({
                'success': True,
                'message': resultado.get('message', 'Estado actualizado correctamente')
            })
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Error al actualizar estado')
            }), 400
            
    except Exception as e:
        logger.error(f"Error updating reservation status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
