import json
import os

def guardar_datos_json(filepath, data):
    """Guarda datos en un archivo JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def cargar_datos_json(filepath):
    """Carga datos desde un archivo JSON."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)