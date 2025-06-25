#!/usr/bin/env python3
"""
Script para probar directamente el webhook con respuestas de recordatorio
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.supabase_client import supabase_client
from utils.session_manager import get_session, save_session
from services.twilio.reminder_handler import handle_reminder_response

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Volumes/AUDIO/gandolfo-recordatorios/logs/webhook_test.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def test_webhook_reminder_response():
    """
    Prueba directa del flujo de respuesta de recordatorio
    """
    print("🧪 PROBANDO RESPUESTA DE RECORDATORIO AL WEBHOOK")
    print("="*50)
    
    # Datos de prueba
    test_phone = "+5491123456789"
    test_response = "1"  # Confirmación
    
    # Paso 1: Crear una reserva de prueba
    print("\n📋 PASO 1: Creando reserva de prueba...")
    
    reserva_data = {
        'restaurante_id': 'e0f20795-d325-4af1-8603-1c52050048db',  # Gandolfo restó
        'fecha': '2025-06-26',
        'hora': '20:00',
        'personas': 2,
        'nombre_cliente': 'Test Webhook Usuario',
        'telefono': test_phone,
        'email': 'test.webhook@ejemplo.com',
        'estado': 'Confirmada',
        'origen': 'test_webhook_simulation',
        'comentarios': f'Reserva de prueba para webhook test - {datetime.now()}'
    }
    
    result = supabase_client.table("reservas_prod").insert(reserva_data).execute()
    
    if not result.data:
        print("❌ ERROR: No se pudo crear la reserva de prueba")
        return
    
    reservation_id = result.data[0]['id']
    print(f"✅ Reserva creada: ID {reservation_id}")
    
    # Paso 2: Configurar sesión como si se hubiera enviado un recordatorio
    print("\n💾 PASO 2: Configurando sesión de recordatorio...")
    
    session_data = {
        'reminder_data': {
            'reserva_id': reservation_id,  # CRÍTICO: Usar 'reserva_id' no 'reservation_id'
            'reservation_id': reservation_id,  # Mantener ambos por compatibilidad
            'restaurant_id': reserva_data['restaurante_id'],
            'is_reminder': True,  # CRÍTICO: El sistema busca este campo
            'confirmation_pending': True,
            'sent_at': datetime.now().isoformat()
        },
        'waiting_for_reminder_response': True,
        'last_interaction': datetime.now().isoformat()
    }
    
    save_session(test_phone, session_data, reserva_data['restaurante_id'])
    print(f"✅ Sesión configurada para {test_phone}")
    
    # Paso 3: Verificar que la sesión se guardó correctamente
    print("\n🔍 PASO 3: Verificando sesión...")
    
    retrieved_session = get_session(test_phone, reserva_data['restaurante_id'])
    if retrieved_session:
        print(f"✅ Sesión recuperada: {json.dumps(retrieved_session, indent=2, default=str)}")
    else:
        print("❌ ERROR: No se pudo recuperar la sesión")
        return
    
    # Paso 4: Simular respuesta del webhook
    print(f"\n📱 PASO 4: Simulando respuesta '{test_response}' al webhook...")
    
    # Crear objeto simulado de Flask request
    class MockRequest:
        def __init__(self, phone, message):
            self.form = {
                'From': phone,
                'Body': message,
                'MessageSid': f'test_webhook_{datetime.now().timestamp()}',
                'AccountSid': 'test_account_sid'
            }
        
        def get_json(self):
            return None
    
    # Simular la llamada al webhook
    mock_request = MockRequest(test_phone, test_response)
    
    try:
        # Llamar directamente a la función del webhook
        logger.info(f"🎯 INICIANDO PROCESAMIENTO DE WEBHOOK para {test_phone} con mensaje '{test_response}'")
        
        # Simular el procesamiento que hace handle_incoming_message
        phone_number = mock_request.form.get('From', '').replace('whatsapp:', '')
        message_body = mock_request.form.get('Body', '').strip()
        
        logger.info(f"📞 Número procesado: {phone_number}")
        logger.info(f"💬 Mensaje procesado: '{message_body}'")
        
        # Recuperar sesión nuevamente para el procesamiento
        session = get_session(phone_number, reserva_data['restaurante_id'])
        logger.info(f"📋 Sesión para webhook: {session}")
        
        if session and session.get('waiting_for_reminder_response'):
            logger.info("🎯 DETECTADO: Usuario esperando respuesta de recordatorio")
            
            # Crear configuración de restaurante
            restaurant_config = {
                'id': reserva_data['restaurante_id'],
                'nombre': 'Gandolfo restó'
            }
            
            # Procesar la respuesta usando la función directa
            result = handle_reminder_response(message_body, phone_number, restaurant_config)
            
            if result:
                print(f"✅ RESPUESTA PROCESADA EXITOSAMENTE")
                print(f"📊 Resultado: {result}")
            else:
                print(f"❌ ERROR procesando respuesta")
        else:
            print(f"❌ ERROR: No se detectó sesión de recordatorio activa")
    
    except Exception as e:
        logger.error(f"❌ ERROR en webhook test: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
    
    # Paso 5: Verificar el estado final de la reserva
    print(f"\n🔍 PASO 5: Verificando estado final de la reserva...")
    
    final_result = supabase_client.table("reservas_prod").select("*").eq('id', reservation_id).execute()
    
    if final_result.data:
        final_reservation = final_result.data[0]
        final_estado = final_reservation.get('estado')
        print(f"📊 Estado final de la reserva: {final_estado}")
        
        if test_response == "1" and final_estado == "Confirmada":
            print("✅ ÉXITO: Reserva confirmada correctamente")
        elif test_response == "2" and final_estado == "Cancelada":
            print("✅ ÉXITO: Reserva cancelada correctamente")
        else:
            print(f"⚠️ ADVERTENCIA: Estado esperado vs actual no coincide")
    else:
        print("❌ ERROR: No se pudo verificar el estado final")
    
    # Paso 6: Limpieza
    print(f"\n🧹 PASO 6: Limpieza...")
    cleanup = input("¿Eliminar reserva de prueba? (y/n): ").strip().lower()
    
    if cleanup == 'y':
        delete_result = supabase_client.table("reservas_prod").delete().eq('id', reservation_id).execute()
        if delete_result.data:
            print("✅ Reserva de prueba eliminada")
        else:
            print("⚠️ No se pudo eliminar la reserva de prueba")
    else:
        print(f"📌 Reserva conservada: ID {reservation_id}")
    
    print("\n✅ Test del webhook completado!")

if __name__ == "__main__":
    test_webhook_reminder_response()
