"""
Módulo para la selección de restaurantes.
Añade funcionalidad para cambiar entre diferentes restaurantes en el sistema.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from db.supabase_client import supabase
from utils.auth import login_required
import logging

logger = logging.getLogger(__name__)

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

@restaurant_bp.route('/select', methods=['GET', 'POST'])
@login_required
def select_restaurant():
    """
    Página para seleccionar un restaurante.
    GET: Muestra la lista de restaurantes disponibles
    POST: Cambia el restaurante seleccionado
    """
    user_id = session.get('user_id')
    
    if not user_id:
        flash("Debes iniciar sesión para seleccionar un restaurante", "error")
        return redirect(url_for('admin.login'))
    
    # Si viene del login, simplemente vaciar las cookies de sesión excepto user_id
    # y redirigir al dashboard, que se encargará de enviar al usuario a crear restaurante
    from_login = request.args.get('from_login')
    if from_login == '1':
        # Limpiar la sesión pero mantener el user_id
        saved_user_id = session.get('user_id')
        saved_username = session.get('nombre_usuario')
        saved_email = session.get('user_email')
        # Limpiar sesión
        session.clear()
        # Restaurar datos básicos del usuario
        session['user_id'] = saved_user_id
        session['nombre_usuario'] = saved_username
        session['user_email'] = saved_email
        return redirect(url_for('admin.dashboard'))
    
    # Si es POST, cambiar el restaurante seleccionado
    if request.method == 'POST':
        restaurant_id = request.form.get('restaurant_id')
        
        if not restaurant_id:
            flash("Por favor, selecciona un restaurante válido", "error")
            return redirect(url_for('restaurant.select_restaurant'))
            
        try:
            # Verificar si el restaurante existe Y pertenece al usuario actual
            response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).eq('admin_id', user_id).single().execute()
            
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
        # Obtener solo los restaurantes que pertenecen al usuario actual
        response = supabase.table('restaurantes').select('*').eq('admin_id', user_id).execute()
        
        if not response.data:
            # Verificar si viene de crear_restaurante para evitar bucle
            referrer = request.referrer or ""
            coming_from_create = "restaurantes/nuevo" in referrer
            
            if coming_from_create:
                # Si viene de crear_restaurante, mostrar página vacía en lugar de redirigir
                flash("No tienes restaurantes asociados a tu cuenta. Crea uno nuevo.", "warning")
                restaurantes = []
            else:
                # Si no viene de crear_restaurante, redirigir a la página de creación
                flash("No tienes restaurantes asociados a tu cuenta", "warning")
                return redirect(url_for('admin.crear_restaurante'))
        else:
            # Ordenar restaurantes - primero los activos
            restaurantes = sorted(response.data, key=lambda x: (
                0 if (x.get('estado') == 'activo' or (not x.get('estado') and x.get('activo', False))) else 1, 
                x.get('nombre', '')
            ))
        
    except Exception as e:
        logger.error(f"Error al obtener la lista de restaurantes: {e}")
        flash(f"Error al obtener la lista de restaurantes: {e}", "error")
        restaurantes = []
    
    return render_template('admin/select_restaurant.html', 
                         restaurantes=restaurantes,
                         current_restaurant_id=session.get('restaurant_id'),
                         username=session.get('nombre_usuario', 'Usuario'),
                         mensaje="Estás viendo solo los restaurantes asociados a tu cuenta")
