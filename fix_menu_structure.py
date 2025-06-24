#!/usr/bin/env python3
import json
import os

# Path to the menu file
menu_file = "/Volumes/AUDIO/gandolfo/data/menus/4a6f6088-61a6-44a2-aa75-5161e1f3cad1_menu.json"

# New menu structure compatible with editor
new_menu = {
    "restaurant_id": "4a6f6088-61a6-44a2-aa75-5161e1f3cad1",
    "restaurant_name": "Elsie restaurante",
    "dias_semana": {
        "lunes": {
            "almuerzo": [
                {
                    "nombre": "Entrada de Ejemplo",
                    "descripcion": "Descripción de la entrada de ejemplo",
                    "precio": 0,
                    "disponible": True
                },
                {
                    "nombre": "Plato Principal de Ejemplo",
                    "descripcion": "Descripción del plato principal de ejemplo", 
                    "precio": 0,
                    "disponible": True
                }
            ],
            "cena": [
                {
                    "nombre": "Plato de Cena de Ejemplo",
                    "descripcion": "Descripción del plato de cena",
                    "precio": 0,
                    "disponible": True
                }
            ]
        },
        "martes": {"almuerzo": [], "cena": []},
        "miércoles": {"almuerzo": [], "cena": []},
        "jueves": {"almuerzo": [], "cena": []},
        "viernes": {"almuerzo": [], "cena": []},
        "sábado": {"almuerzo": [], "cena": []},
        "domingo": {"almuerzo": [], "cena": []}
    },
    "menu_especial": {
        "celiaco": {
            "platos_principales": [
                {
                    "nombre": "Plato sin TACC de ejemplo",
                    "descripcion": "Descripción del plato sin gluten",
                    "precio": 0,
                    "disponible": True
                }
            ],
            "postres": [],
            "nota": "Todos nuestros platos sin TACC son preparados en área libre de contaminación cruzada."
        }
    },
    "last_updated": "2025-06-15T12:00:00"
}

# Write the new menu structure
with open(menu_file, 'w', encoding='utf-8') as f:
    json.dump(new_menu, f, indent=2, ensure_ascii=False)

print(f"Menu file updated: {menu_file}")
