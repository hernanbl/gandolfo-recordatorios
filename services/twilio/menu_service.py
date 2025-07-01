import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

MENUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'menus')

def get_menu_for_day(restaurant_id, day_of_week):
    """
    Obtiene el menú para un día específico de la semana desde el archivo JSON del restaurante.
    """
    try:
        menu_file_path = os.path.join(MENUS_DIR, f"{restaurant_id}_menu.json")
        if not os.path.exists(menu_file_path):
            logger.warning(f"No se encontró el archivo de menú para el restaurante {restaurant_id}")
            return None

        with open(menu_file_path, 'r', encoding='utf-8') as f:
            menu_data = json.load(f)

        daily_menu = menu_data.get('dias_semana', {}).get(day_of_week.lower(), {})
        return daily_menu

    except Exception as e:
        logger.error(f"Error al obtener el menú para el día {day_of_week}: {e}")
        return None
