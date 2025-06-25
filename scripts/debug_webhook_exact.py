#!/usr/bin/env python3
"""
Script para debuggear exactamente qué pasa cuando llega un mensaje al webhook
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.supabase_client import supabase_client
from utils.session_manager import get_session
from utils.phone_utils import get_phone_variants
from services.twilio.reminder_handler import handle_reminder_response

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Volumes/AUDIO/gandolfo-recordatorios/logs/webhook_debug.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def debug_webhook_exact_flow():
    """
    Simula exactamente lo que hace el webhook cuando recibe un mensaje
    """
    print("🔍 DEBUGGER DEL WEBHOOK - SIMULACIÓN EXACTA")
    print("="*60)
    
    # Datos que llegan del webhook real (según los logs de WhatsApp)
    original_phone = "whatsapp:+5491166686255"  # Formato que envía Twilio
    message_body = "1"  # Tu respuesta
    
    print(f"📱 Número original del webhook: {original_phone}")
    print(f"💬 Mensaje recibido: '{message_body}'")
    
    # PASO 1: Limpiar el número (igual que hace el webhook real)
    phone_number = original_phone.replace('whatsapp:', '')
    print(f"📞 Número limpiado: {phone_number}")
    
    # PASO 2: Buscar en TODOS los restaurantes (como hace el webhook real)
    print(f"\n🔍 PASO 2: Buscando sesión en todos los restaurantes...")
    
    restaurants = [
        {'id': 'e0f20795-d325-4af1-8603-1c52050048db', 'nombre': 'Gandolfo restó'},
        {'id': '6a117059-4c96-4e48-8fba-a59c71fd37cf', 'nombre': 'Ostende restó'},
        {'id': '4a6f6088-61a6-44a2-aa75-5161e1f3cad1', 'nombre': 'Elsie restaurante'}
    ]
    
    session_found = None
    restaurant_found = None
    
    for restaurant in restaurants:
        restaurant_id = restaurant['id']
        restaurant_name = restaurant['nombre']
        
        print(f"  🏪 Probando {restaurant_name} (ID: {restaurant_id})")
        
        # Obtener variantes del teléfono
        phone_variants = get_phone_variants(phone_number)
        print(f"    📞 Variantes a probar: {phone_variants}")
        
        for variant in phone_variants:
            session = get_session(variant, restaurant_id)
            if session:
                print(f"    ✅ SESIÓN ENCONTRADA en {restaurant_name} para variante: {variant}")
                print(f"    📋 Datos de sesión: {json.dumps(session, indent=4, default=str)}")
                
                # Verificar si es un recordatorio
                reminder_data = session.get('reminder_data', {})
                if reminder_data and reminder_data.get('is_reminder'):
                    print(f"    🎯 ES UN RECORDATORIO ACTIVO!")
                    session_found = session
                    restaurant_found = restaurant
                    break
                else:
                    print(f"    ⚠️ Sesión encontrada pero no es recordatorio activo")
            else:
                print(f"    ❌ No hay sesión para variante: {variant}")
        
        if session_found:
            break
    
    if not session_found:
        print("\n❌ NO SE ENCONTRÓ SESIÓN DE RECORDATORIO EN NINGÚN RESTAURANTE")
        print("🔄 El webhook procederá con flujo normal de nuevo restaurante")
        return
    
    print(f"\n✅ SESIÓN DE RECORDATORIO ENCONTRADA EN: {restaurant_found['nombre']}")
    
    # PASO 3: Procesar la respuesta de recordatorio
    print(f"\n🎯 PASO 3: Procesando respuesta de recordatorio...")
    
    try:
        # Crear configuración de restaurante
        restaurant_config = {
            'id': restaurant_found['id'],
            'nombre': restaurant_found['nombre'],
            'nombre_restaurante': restaurant_found['nombre']
        }
        
        print(f"🏪 Configuración del restaurante: {restaurant_config}")
        
        # Llamar al handler de recordatorios
        result = handle_reminder_response(message_body, phone_number, restaurant_config)
        
        print(f"📊 RESULTADO DEL HANDLER: {result}")
        
        # PASO 4: Verificar estado final de la reserva
        print(f"\n🔍 PASO 4: Verificando estado de la reserva...")
        
        reserva_id = session_found['reminder_data'].get('reserva_id')
        if reserva_id:
            reserva_result = supabase_client.table("reservas_prod").select("*").eq('id', reserva_id).execute()
            if reserva_result.data:
                reserva = reserva_result.data[0]
                print(f"📋 Estado final de la reserva:")
                print(f"   ID: {reserva['id']}")
                print(f"   Estado: {reserva['estado']}")
                print(f"   Cliente: {reserva['nombre_cliente']}")
                print(f"   Recordatorio respondido: {reserva.get('recordatorio_respondido', 'N/A')}")
            else:
                print(f"❌ No se pudo obtener el estado de la reserva {reserva_id}")
        
    except Exception as e:
        print(f"❌ ERROR procesando respuesta: {str(e)}")
        logger.error(f"Error en debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_webhook_exact_flow()
