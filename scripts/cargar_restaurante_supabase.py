import os
import json
from db.supabase_client import supabase_client

# Ruta al archivo JSON
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', 'restaurant_info.json')

# Leer datos del JSON
def cargar_datos_restaurante():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    data = cargar_datos_restaurante()
    nombre = data.get('name', '').strip()
    direccion = data.get('location', {}).get('address', '').strip()
    telefono = data.get('contact', {}).get('phone', '').strip()

    if not nombre:
        print('El nombre del restaurante es obligatorio.')
        return

    # Buscar si ya existe
    response = supabase_client.table('restaurantes').select('id').eq('nombre', nombre).execute()
    if hasattr(response, 'data') and response.data:
        print(f"Ya existe un restaurante con el nombre '{nombre}'. No se realiza ninguna acción.")
        return

    # Insertar nuevo restaurante
    insert_data = {
        'nombre': nombre,
        'direccion': direccion,
        'telefono': telefono,
        'estado': 'activo'
    }
    insert_response = supabase_client.table('restaurantes').insert(insert_data).execute()
    if hasattr(insert_response, 'data') and insert_response.data:
        print(f"Restaurante '{nombre}' dado de alta en Supabase.")
        restaurant_id = insert_response.data[0]['id']

        # Crear directorio de menús si no existe
        menus_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'menus')
        os.makedirs(menus_dir, exist_ok=True)

        # Cargar plantilla de menú
        menu_template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', 'menu.json')
        with open(menu_template_path, 'r', encoding='utf-8') as f_template:
            menu_data = json.load(f_template)

        # Guardar nuevo archivo de menú
        new_menu_file_path = os.path.join(menus_dir, f"{restaurant_id}_menu.json")
        with open(new_menu_file_path, 'w', encoding='utf-8') as f_new_menu:
            json.dump(menu_data, f_new_menu, ensure_ascii=False, indent=2)
        print(f"Archivo de menú creado en: {new_menu_file_path}")

    else:
        print(f"Error al dar de alta el restaurante: {insert_response}")

if __name__ == '__main__':
    main()
