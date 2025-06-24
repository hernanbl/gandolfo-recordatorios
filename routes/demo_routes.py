from flask import Blueprint, redirect, url_for, flash, current_app, render_template
from utils.auth import login_required
from utils.demo_utils import is_demo_restaurant, add_demo_sample_data
import logging

# Crear el blueprint para rutas de demostración
demo_bp = Blueprint('demo', __name__, url_prefix='/admin/demo')
logger = logging.getLogger(__name__)

@demo_bp.route('/reset_data')
@login_required
def reset_demo_data():
    """
    Ruta para regenerar los datos de muestra del restaurante de demostración.
    Solo funciona si el usuario está autenticado y pertenece al restaurante de demostración.
    """
    # Obtener el ID de restaurante de la sesión
    restaurant_id = current_app.config.get('RESTAURANT_ID')
    
    if not restaurant_id or not is_demo_restaurant(restaurant_id):
        flash("Esta funcionalidad solo está disponible para el restaurante de demostración", "error")
        return redirect(url_for('admin.dashboard'))
    
    # YA NO SE DESACTIVA LA FUNCIONALIDAD - EL SCRIPT ES SEGURO (SOLO AÑADE)
    
    # Regenerar los datos de muestra
    logger.info(f"Añadiendo datos de muestra adicionales para el restaurante de demostración {restaurant_id} (Modo Seguro: Solo Añade)")
    success = add_demo_sample_data()
    
    if success:
        flash("¡Nuevos datos de demostración añadidos con éxito! Las reservas existentes no fueron modificadas.", "success")
    else:
        pass # No es necesario un flash genérico aquí si add_demo_sample_data ya lo maneja
    
    # Redirigir al dashboard
    return redirect(url_for('admin.dashboard'))
