from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash, g
import logging
from utils.demo_utils import is_demo_restaurant

# Using a logger specific to this module.
# Flask's flash, url_for etc., rely on an active app context when the decorated route is executed.
logger = logging.getLogger('utils.auth')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Using Flask's global request, session, etc.
        # These require an active application context when called.
        # At decoration time, it's fine. At call time (when the decorated route is hit),
        # Flask ensures an app context is present.
        
        # Using a more specific logger name for clarity if needed.
        current_logger = logging.getLogger('utils.auth.login_required')
        current_logger.debug(f"Accessing {request.path}. Session keys: {list(session.keys())}")        # Verificar si es el restaurante de demostración y compartirlo con la plantilla
        restaurant_id = session.get('restaurant_id') or session.get('current_restaurant_id')
        g.is_demo_restaurant = is_demo_restaurant(restaurant_id) if restaurant_id else False
        
        # Check if user is logged in
        if 'user_id' not in session or 'username' not in session:
            current_logger.warning(f"'user_id' or 'username' not in session for {request.path}. Session: {dict(session)}. Redirecting to admin.login.")
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
              # For API endpoints that might be protected by this, return JSON
            if request.is_json or \
               (request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json' and \
                request.accept_mimetypes.best_match(['application/json', 'text/html']) != 'text/html'):
                return jsonify(message="Autenticación requerida."), 401
            # Use direct URL instead of url_for to avoid BuildError
            return redirect('/admin/login?next=' + request.url)        # Check if a restaurant is selected (only for paths that aren't the restaurant selection page itself, 
        # the login page, create restaurant page, or other critical pages)
        if not restaurant_id and \
           request.path != '/restaurant/select' and \
           request.path != '/admin/login' and \
           request.path != '/admin/crear_restaurante' and \
           '/admin/select_restaurant' not in request.path and \
           '/admin/crear_restaurante' not in request.path:
            current_logger.info(f"No restaurant selected for {request.path}. Session: {dict(session)}. Redirecting to restaurant selector.")
            flash("Por favor, selecciona un restaurante para continuar.", "warning")
            return redirect('/restaurant/select?next=' + request.url)
        
        current_logger.debug(f"User {session.get('username')} (ID: {session.get('user_id')}) authorized for {request.path}.")
        return f(*args, **kwargs)
    return decorated_function
