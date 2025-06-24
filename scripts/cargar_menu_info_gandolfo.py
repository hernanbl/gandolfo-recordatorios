import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from db.supabase_client import get_supabase_client

# Configura el nombre del restaurante a actualizar
target_name = "Gandolfo Restó"

# Carga el archivo JSON de info
data_dir = os.path.join(os.path.dirname(__file__), '../data/processed')
info_path = os.path.join(data_dir, 'restaurant_info.json')

with open(info_path, 'r', encoding='utf-8') as f:
    info_json = json.load(f)

# Extrae los campos específicos
descripcion = info_json.get('description')
ubicacion = info_json.get('location')
metodos_pago = info_json.get('payment_methods')
promociones = info_json.get('payment_promotions')

# Elimina los campos que van por separado para info_json
info_json_export = dict(info_json)
for k in ['description', 'location', 'payment_methods', 'payment_promotions']:
    info_json_export.pop(k, None)

supabase = get_supabase_client()

# Busca el restaurante Gandolfo
response = supabase.table('restaurantes').select('*').ilike('nombre', f'%{target_name}%').execute()
if not hasattr(response, 'data') or not response.data:
    print(f"No se encontró el restaurante '{target_name}' en Supabase.")
    exit(1)
restaurante = response.data[0]
restaurante_id = restaurante['id']

# Actualiza las columnas info_json, metodos_pago, promociones, ubicacion y descripcion
update_response = supabase.table('restaurantes').update({
    'info_json': info_json_export,
    'metodos_pago': metodos_pago,
    'promociones': promociones,
    'ubicacion': ubicacion,
    'descripcion': descripcion
}).eq('id', restaurante_id).execute()

if hasattr(update_response, 'data') and update_response.data:
    print(f"Datos de info cargados correctamente en el restaurante '{target_name}'.")
else:
    print("Error al actualizar los datos de info en Supabase.")
