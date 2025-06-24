# Utility script to fix restaurant status field discrepancy
# This fixes the mismatch between 'activo' and 'estado' fields in restaurant entries
from db.supabase_client import supabase
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_restaurant_status():
    try:
        # Get all restaurants
        response = supabase.table('restaurantes').select('*').execute()
        
        if not response.data:
            logger.info("No restaurants found in the database.")
            return
            
        logger.info(f"Found {len(response.data)} restaurants to check.")
        updated_count = 0
        
        for restaurant in response.data:
            restaurant_id = restaurant.get('id')
            
            # Check if estado is missing or doesn't match activo
            needs_update = False
            
            # Case 1: No estado field but has activo field
            if 'estado' not in restaurant and 'activo' in restaurant:
                new_estado = 'activo' if restaurant['activo'] else 'no-activo'
                needs_update = True
            
            # Case 2: Estado field exists but doesn't match activo field
            elif 'estado' in restaurant and 'activo' in restaurant:
                current_estado = restaurant['estado']
                should_be_estado = 'activo' if restaurant['activo'] else 'no-activo'
                
                if current_estado != should_be_estado:
                    new_estado = should_be_estado
                    needs_update = True
            
            # Case 3: No estado field but has config.activo
            elif 'estado' not in restaurant and restaurant.get('config', {}).get('activo') is not None:
                config_activo = restaurant['config'].get('activo')
                new_estado = 'activo' if config_activo else 'no-activo'
                needs_update = True
                
            # Update the restaurant if needed
            if needs_update:
                try:
                    supabase.table('restaurantes').update({'estado': new_estado}).eq('id', restaurant_id).execute()
                    logger.info(f"Updated restaurant {restaurant_id}: set estado={new_estado}")
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update restaurant {restaurant_id}: {str(e)}")
        
        logger.info(f"Restaurant status fix complete. Updated {updated_count} restaurants.")
        
    except Exception as e:
        logger.error(f"Error executing restaurant status fix: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting restaurant status field fix script...")
    fix_restaurant_status()
    logger.info("Script completed.")
