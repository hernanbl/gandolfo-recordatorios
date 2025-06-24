#!/usr/bin/env python
"""
Script simple para verificar la configuración de reservas.
"""

import sys
import os

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import RESERVAS_TABLE, USE_PROD_TABLES, SUPABASE_ENABLED
    from utils.demo_utils import get_reservas_table
    
    print("== VERIFICACIÓN DE CONFIGURACIÓN ==")
    print(f"USE_PROD_TABLES: {USE_PROD_TABLES}")
    print(f"RESERVAS_TABLE configurado como: {RESERVAS_TABLE}")
    print(f"SUPABASE_ENABLED: {SUPABASE_ENABLED}")
    
    # Verificar configuración para diferentes IDs de restaurantes
    restaurantes = {
        'gandolfo': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'ostende': 'e0f20795-d325-4af1-8603-1c52050048db'
    }
    
    for nombre, id in restaurantes.items():
        tabla, usa_restaurante_id = get_reservas_table(id)
        print(f"Restaurante {nombre} ({id}): usa tabla '{tabla}' con campo {'restaurante_id' if usa_restaurante_id else 'restaurant_id'}")

except ImportError as e:
    print(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
