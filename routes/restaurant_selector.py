"""
Módulo para la selección de restaurantes.
Añade funcionalidad para cambiar entre diferentes restaurantes en el sistema.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from db.supabase_client import supabase
from utils.auth import login_required
import logging

logger = logging.getLogger(__name__)

# Crear el blueprint
restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

@restaurant_bp.route('/select', methods=['GET', 'POST'])
@login_required
def select_restaurant():
    """
    Página para seleccionar un restaurante.
    GET: Muestra la lista de restaurantes disponibles
    POST: Cambia el restaurante seleccionado
    """
    # Log de estado actual de la solicitud
    logger.info(f"Entrando a select_restaurant. Método: {request.method}, Referrer: {request.referrer}")
    logger.info(f"Parámetros: {dict(request.args)}")
    logger.info(f"Estado actual de sesión: {dict(session)}")
    
    user_id_from_session = session.get('user_id') # This is public.usuarios.id
    
    if not user_id_from_session:
        flash("Debes iniciar sesión para seleccionar un restaurante", "error")
        return redirect(url_for('admin.login'))

    # Get the actual admin_id (auth.users.id) to be used for querying 'restaurantes' table
    try:
        user_profile_response = supabase.table('usuarios').select('auth_user_id').eq('id', user_id_from_session).single().execute()
        if not user_profile_response.data or not user_profile_response.data.get('auth_user_id'):
            logger.error(f"Could not retrieve auth_user_id for session user_id: {user_id_from_session}")
            flash("Error de perfil de usuario. No se pudo verificar la identidad.", "error")
            return redirect(url_for('admin.login'))
        actual_admin_id = user_profile_response.data['auth_user_id']
        logger.info(f"Session user_id '{user_id_from_session}' maps to auth_user_id (admin_id for restaurantes): '{actual_admin_id}'")
    except Exception as e:
        logger.error(f"Error fetching auth_user_id for session user_id {user_id_from_session}: {e}")
        flash("Error al obtener detalles del perfil de usuario.", "error")
        return redirect(url_for('admin.login'))
    
    # Si viene de login con parámetro from_login=1, ajustar la sesión
    # Esto evita que la sesión tenga residuos de una sesión anterior
    from_login = request.args.get('from_login')
    if from_login == '1':
        logger.info("Viniendo desde el login, limpiando sesión excepto datos básicos de usuario")
        # Guardar datos esenciales del usuario
        saved_user_id = session.get('user_id')
        saved_username = session.get('nombre_usuario')
        saved_email = session.get('user_email')
        # Limpiar toda la sesión para evitar problemas con datos residuales
        session.clear()
        # Restaurar solo datos básicos
        session['user_id'] = saved_user_id
        session['nombre_usuario'] = saved_username
        session['user_email'] = saved_email
        # Redirigir al dashboard que manejará el caso de restaurante no seleccionado
        return redirect(url_for('admin.dashboard'))
    
    # Controlar el ciclo de redirección entre select_restaurant y crear_restaurante
    # Incrementar contador de redirecciones (para detectar bucles)
    session['redirect_count'] = session.get('redirect_count', 0) + 1
    
    # Si detectamos muchas redirecciones, podemos estar en un ciclo
    if session.get('redirect_count', 0) > 3:
        logger.warning("Posible ciclo de redirección detectado. Reseteando contador y mostrando página de selección vacía.")
        session['redirect_count'] = 0
        flash("Se ha detectado un problema en la navegación. Por favor, crea un restaurante o contacta al soporte.", "warning")
        return render_template('admin/select_restaurant.html',
                              restaurantes=[],
                              current_restaurant_id=None,
                              username=session.get('nombre_usuario', 'Usuario'),
                              mensaje="Hubo un problema al cargar tus restaurantes.")
    
    # Si es POST, cambiar el restaurante seleccionado
    if request.method == 'POST':
        # Resetear contador de redirecciones en POST válido
        session['redirect_count'] = 0
        restaurant_id = request.form.get('restaurant_id')
        
        if not restaurant_id:
            flash("Por favor, selecciona un restaurante válido", "error")
            return redirect(url_for('restaurant.select_restaurant'))
            
        try:
            # Verificar si el restaurante existe Y pertenece al usuario actual (using actual_admin_id)
            response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).eq('admin_id', actual_admin_id).single().execute()
            
            if not response.data:
                flash("No tienes permiso para acceder a este restaurante o no existe", "error")
                return redirect(url_for('restaurant.select_restaurant'))
            
            # Guardar el restaurante en la sesión
            session['restaurant_id'] = restaurant_id
            session['restaurant_name'] = response.data.get('nombre', 'Restaurante sin nombre')
            
            flash(f"Restaurante '{session['restaurant_name']}' seleccionado correctamente", "success")
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            logger.error(f"Error al cambiar el restaurante: {e}")
            flash(f"Error al cambiar el restaurante: {e}", "error")
    
    # Si es GET o hubo un error en el POST, mostrar la página de selección
    try:
        # Obtener solo los restaurantes que pertenecen al usuario actual (using actual_admin_id)
        response = supabase.table('restaurantes').select('*').eq('admin_id', actual_admin_id).execute()
        
        # Limpiar mensajes flash antiguos para evitar duplicados
        session.pop('_flashes', None)
        
        if not response.data or len(response.data) == 0:
            # Sin restaurantes
            logger.info(f"Usuario con auth_user_id {actual_admin_id} no tiene restaurantes asociados")
            # Verificar si viene de crear_restaurante para evitar bucle
            referrer = request.referrer or ""
            coming_from_create = "restaurantes/nuevo" in referrer
            
            if coming_from_create:
                # Si viene de crear_restaurante, mostrar página vacía en lugar de redirigir
                flash("No tienes restaurantes asociados a tu cuenta. Crea uno nuevo.", "warning")
                restaurantes = []
            else:
                # Si no viene de crear_restaurante, redireccionar directamente a crear_restaurante
                # sin contar redirecciones para evitar bucles
                logger.info("Usuario sin restaurantes. Redirigiendo directamente a crear_restaurante")
                session.pop('redirect_count', None)  # Quitar contador para evitar bucles
                flash("No tienes restaurantes asociados a tu cuenta. Crea uno nuevo.", "warning")
                return redirect(url_for('admin.crear_restaurante'))
        elif len(response.data) == 1:
            # Si el usuario tiene exactamente un restaurante, seleccionarlo automáticamente
            logger.info(f"Usuario con auth_user_id {actual_admin_id} tiene un único restaurante. Seleccionando automáticamente.")
            restaurant = response.data[0]
            session['restaurant_id'] = restaurant['id']
            session['restaurant_name'] = restaurant.get('nombre', 'Restaurante sin nombre')
            flash(f"Se ha seleccionado automáticamente tu restaurante: {session['restaurant_name']}", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            # Ordenar restaurantes - primero los activos, luego por nombre
            logger.info(f"Usuario con auth_user_id {actual_admin_id} tiene {len(response.data)} restaurantes. Mostrando lista de selección.")
            restaurantes = sorted(response.data, key=lambda x: (
                0 if (x.get('estado') == 'activo' or (x.get('activo', False) and not x.get('estado'))) else 1, 
                x.get('nombre', '')
            ))
            
    except Exception as e:
        logger.error(f"Error al obtener la lista de restaurantes para auth_user_id {actual_admin_id}: {e}")
        flash(f"Error al obtener la lista de restaurantes: {e}", "error")
        restaurantes = []
    
    # Mostrar la página de selección con la lista de restaurantes
    return render_template('admin/select_restaurant.html', 
                          restaurantes=restaurantes,
                          current_restaurant_id=session.get('restaurant_id'),
                          username=session.get('nombre_usuario', 'Usuario'),
                          mensaje="Estás viendo solo los restaurantes asociados a tu cuenta")
