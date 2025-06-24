import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Inicializar cliente Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Inicializando cliente Supabase...")

    # IDs de los restaurantes
    restaurant_ids = [
        'e0f20795-d325-4af1-8603-1c52050048db',  # Gandolfo
        '6a117059-4c96-4e48-8fba-a59c71fd37cf'   # Ostende
    ]

    for restaurant_id in restaurant_ids:
        try:
            # Actualizar el estado del restaurante a activo
            response = supabase.table('restaurantes').update({
                'estado': 'activo'
            }).eq('id', restaurant_id).execute()

            if response.data:
                logger.info(f"Restaurante {restaurant_id} activado exitosamente")
            else:
                logger.error(f"No se pudo activar el restaurante {restaurant_id}")

        except Exception as e:
            logger.error(f"Error al activar restaurante {restaurant_id}: {str(e)}")

if __name__ == "__main__":
    main()
