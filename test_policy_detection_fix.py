#!/usr/bin/env python3
"""
Test para verificar la detección de políticas después del fix
"""

import logging
import sys
import os
import json

# Configurar el path para importar módulos
sys.path.append(os.path.abspath('.'))

from services.twilio.handler import handle_whatsapp_message, ensure_restaurant_data_loaded

# Configurar logging para ver los detalles
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_policy_detection():
    """Test de detección de políticas específicas"""
    
    # Crear configuración de restaurante de prueba basada en Ostende
    restaurant_config = {
        'id': 'ostende',
        'nombre_restaurante': 'Ostende restó',
        'twilio_number': '+18059093442',
        'info_json': {
            "name": "Ostende restó",
            "description": "⭐ Somos un restaurante clásico ubicado en CABA.",
            "location": {
                "address": "Ostende 2393, CABA",
                "google_maps_link": "https://www.google.com.ar/maps/place/Islandia+2397/@-34.3653654,-58.7662235,17z"
            },
            "contact": {
                "phone": "116-268-1222",
                "email": "resto@vivacom.com.ar",
                "whatsapp": "+18059093442"
            },
            "policies": {
                "pets": {
                    "allowed": True,
                    "restrictions": "Solo en la terraza o patio exterior",
                    "description": "Nos encanta recibir a las mascotas de nuestros clientes en nuestra terraza al aire libre. ¡Esperamos verte con tu compañero peludo! 🐾"
                },
                "children": {
                    "allowed": True,
                    "description": "Contamos con menú infantil y ambiente familiar",
                    "amenities": ["menú infantil", "ambiente familiar", "sillas altas disponibles"]
                },
                "smoking": {
                    "allowed": False,
                    "outdoor_allowed": True,
                    "description": "No se permite fumar en el interior. Está permitido fumar en la terraza al aire libre."
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "braille_menu": False,
                    "description": "Contamos con acceso para sillas de ruedas. Para necesidades especiales, por favor contactanos con anticipación."
                },
                "dietary_options": {
                    "vegetarian": True,
                    "vegan": True,
                    "gluten_free": True,
                    "description": "Contamos con opciones vegetarianas, veganas y sin gluten (sin TACC). Por favor, informanos sobre alergias o restricciones alimentarias al hacer tu reserva para que podamos preparar algo especial para vos."
                },
                "parking": {
                    "available": True,
                    "type": "propio",
                    "description": "Contamos con estacionamiento propio para clientes"
                },
                "dress_code": {
                    "required": False,
                    "style": "casual",
                    "description": "Ambiente casual y relajado. Vení como te sientas cómodo."
                },
                "cancellation": {
                    "advance_notice_hours": 4,
                    "policy": "Las reservas pueden cancelarse hasta 4 horas antes sin cargo",
                    "description": "Para cancelar o modificar tu reserva, contactanos hasta 4 horas antes del horario reservado."
                }
            }
        }
    }
    
    logger.info(f"🏪 Testeando con restaurante: {restaurant_config.get('nombre_restaurante')}")
    logger.info(f"📊 Info JSON disponible: {bool(restaurant_config.get('info_json'))}")
    
    # Verificar que las políticas estén en el JSON
    info = restaurant_config.get('info_json', {})
    policies = info.get('policies', {})
    logger.info(f"📋 Políticas disponibles en JSON: {list(policies.keys())}")
    
    # Test cases que fallaban antes
    test_cases = [
        "Se puede fumar en Ostende?",
        "Se puede ir con niños?", 
        "Puedo llevar mi perro?",
        "Tienen estacionamiento?",
        "Como hay que vestirse?",
        "Política de cancelación?"
    ]
    
    fake_number = "whatsapp:+5491123456789"
    
    for i, test_message in enumerate(test_cases, 1):
        logger.info(f"\n🧪 TEST {i}: '{test_message}'")
        logger.info("=" * 50)
        
        try:
            # Simular el procesamiento del mensaje (sin enviar realmente)
            result = handle_whatsapp_message(
                message=test_message,
                from_number=fake_number,
                restaurant_config=restaurant_config
            )
            
            logger.info(f"✅ TEST {i} completado")
            
        except Exception as e:
            logger.error(f"❌ TEST {i} falló: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("\n🏁 Todos los tests completados")

if __name__ == "__main__":
    test_policy_detection()
