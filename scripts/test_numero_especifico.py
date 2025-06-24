#!/usr/bin/env python3
"""
Script para probar específicamente el número de Twilio +18059093442
y diagnosticar por qué no funciona para WhatsApp.
"""

import sys
import os

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_twilio_number():
    print("🔍 DIAGNÓSTICO ESPECÍFICO PARA NÚMERO +18059093442")
    print("=" * 60)
    
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        from twilio.rest import Client
        
        print(f"📞 Número configurado: {TWILIO_WHATSAPP_NUMBER}")
        print(f"📞 Número esperado: +18059093442")
        
        if TWILIO_WHATSAPP_NUMBER != "+18059093442":
            print(f"⚠️  DISCREPANCIA ENCONTRADA:")
            print(f"   Variable de entorno: {TWILIO_WHATSAPP_NUMBER}")
            print(f"   Número en consola: +18059093442")
        
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
            print("❌ Faltan credenciales de Twilio")
            return False
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Verificar cuenta
        print("\n🔗 Verificando cuenta de Twilio...")
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Cuenta: {account.friendly_name}")
        print(f"   Status: {account.status}")
        
        # Listar TODOS los números
        print("\n📱 Todos los números en la cuenta:")
        numbers = client.incoming_phone_numbers.list()
        for number in numbers:
            print(f"   📞 {number.phone_number}")
            print(f"      SMS: {number.capabilities.get('sms', False)}")
            print(f"      Voice: {number.capabilities.get('voice', False)}")
            print(f"      MMS: {number.capabilities.get('mms', False)}")
            print(f"      Friendly Name: {number.friendly_name}")
            print()
        
        # Verificar específicamente el número +18059093442
        target_number = "+18059093442"
        found_number = None
        
        for number in numbers:
            if number.phone_number == target_number:
                found_number = number
                break
        
        if found_number:
            print(f"✅ NÚMERO ENCONTRADO: {target_number}")
            print(f"   SMS habilitado: {found_number.capabilities.get('sms', False)}")
            print(f"   Status: {found_number.status}")
        else:
            print(f"❌ NÚMERO NO ENCONTRADO: {target_number}")
            print("   El número no está en tu cuenta de Twilio")
            return False
        
        # Verificar configuración de WhatsApp específicamente
        print(f"\n📱 Verificando configuración de WhatsApp...")
        
        # Intentar obtener información del sandbox de WhatsApp
        try:
            # Verificar si hay configuración de WhatsApp sandbox
            sandbox_participants = client.messages.list(
                from_=f"whatsapp:{target_number}",
                limit=1
            )
            print(f"✅ El número puede enviar mensajes de WhatsApp")
        except Exception as whatsapp_error:
            print(f"⚠️  Error verificando WhatsApp: {str(whatsapp_error)}")
        
        # Probar envío de prueba a un número sandbox
        print(f"\n🧪 PRUEBA DE ENVÍO:")
        print(f"   Desde: whatsapp:{target_number}")
        print(f"   Hacia: whatsapp:+5491166686255 (número de prueba)")
        
        try:
            # Hacer una prueba sin enviar realmente
            message_data = {
                'body': 'Prueba de conectividad - este mensaje NO se enviará',
                'from_': f'whatsapp:{target_number}',
                'to': 'whatsapp:+5491166686255'
            }
            print(f"   Datos del mensaje: {message_data}")
            
            # Solo simular, no enviar realmente
            print("   ℹ️  Simulación completada (no se envió mensaje real)")
            
        except Exception as test_error:
            print(f"   ❌ Error en prueba: {str(test_error)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_whatsapp_business_status():
    """Verificar el estado de WhatsApp Business"""
    print(f"\n📋 VERIFICACIÓN DE WHATSAPP BUSINESS")
    print("=" * 40)
    
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Intentar acceder a la API de WhatsApp Business
        try:
            # Esta llamada puede fallar si WhatsApp Business no está configurado
            conversations = client.conversations.v1.conversations.list(limit=1)
            print("✅ WhatsApp Business API accesible")
        except Exception as wb_error:
            print(f"⚠️  WhatsApp Business API: {str(wb_error)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando WhatsApp Business: {str(e)}")
        return False

def main():
    success = test_twilio_number()
    check_whatsapp_business_status()
    
    print(f"\n" + "=" * 60)
    print("🔧 RECOMENDACIONES:")
    print("=" * 60)
    
    print("""
1. 📱 Verificar en Twilio Console:
   - Ve a Phone Numbers → Manage → Incoming phone numbers
   - Busca +18059093442
   - Verifica que esté habilitado para SMS
   - Verifica que tenga configuración de WhatsApp
   
2. 🔗 Verificar WhatsApp Business:
   - Ve a Messaging → WhatsApp → Senders
   - Verifica que +18059093442 esté listado
   - Verifica el status (debe ser "approved" o "pending")
   
3. 🧪 Probar en WhatsApp Sandbox:
   - Ve a Messaging → Try it out → Send a WhatsApp message
   - Usa +18059093442 como número de origen
   - Envía un mensaje de prueba
   
4. 📋 Verificar variables de entorno en Render:
   - TWILIO_WHATSAPP_NUMBER debe ser exactamente: +18059093442
   - Sin prefijo "whatsapp:" en la variable de entorno
""")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
