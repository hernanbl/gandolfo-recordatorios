#!/usr/bin/env python3
"""
Script para verificar la configuración de Twilio y validar el número de WhatsApp.
"""

import sys
import os

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        from twilio.rest import Client
        
        print("🔧 VERIFICACIÓN DE CONFIGURACIÓN DE TWILIO")
        print("=" * 50)
        
        # Verificar variables de entorno
        print("📋 Variables de entorno:")
        print(f"  TWILIO_ACCOUNT_SID: {'✅ Configurado' if TWILIO_ACCOUNT_SID else '❌ Falta'}")
        print(f"  TWILIO_AUTH_TOKEN: {'✅ Configurado' if TWILIO_AUTH_TOKEN else '❌ Falta'}")
        print(f"  TWILIO_WHATSAPP_NUMBER: {'✅ Configurado' if TWILIO_WHATSAPP_NUMBER else '❌ Falta'}")
        
        if TWILIO_WHATSAPP_NUMBER:
            print(f"  Número configurado: {TWILIO_WHATSAPP_NUMBER}")
        
        print()
        
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
            print("❌ Error: Faltan variables de entorno requeridas para Twilio")
            return False
        
        # Verificar conexión con Twilio
        print("🔗 Verificando conexión con Twilio...")
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            # Verificar que la cuenta sea válida
            account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
            print(f"✅ Conexión exitosa con Twilio")
            print(f"  Cuenta: {account.friendly_name}")
            print(f"  Status: {account.status}")
            
            # Verificar números de WhatsApp disponibles
            print("\n📱 Verificando números de WhatsApp:")
            incoming_phone_numbers = client.incoming_phone_numbers.list()
            whatsapp_numbers = []
            
            for number in incoming_phone_numbers:
                capabilities = number.capabilities
                if capabilities and capabilities.get('sms'):  # WhatsApp usa la capacidad SMS
                    whatsapp_numbers.append(number.phone_number)
                    print(f"  📞 Número disponible: {number.phone_number}")
            
            if not whatsapp_numbers:
                print("  ⚠️  No se encontraron números con capacidad WhatsApp")
            
            # Verificar si el número configurado está en la lista
            configured_number = TWILIO_WHATSAPP_NUMBER.replace('whatsapp:', '').replace('+', '')
            if whatsapp_numbers:
                for available_number in whatsapp_numbers:
                    if configured_number in available_number.replace('+', ''):
                        print(f"✅ El número configurado {TWILIO_WHATSAPP_NUMBER} está disponible")
                        return True
                        
                print(f"❌ El número configurado {TWILIO_WHATSAPP_NUMBER} NO está en los números disponibles")
                print("   Números disponibles:")
                for num in whatsapp_numbers:
                    print(f"     - {num}")
                return False
            
        except Exception as e:
            print(f"❌ Error conectando con Twilio: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando módulos: {str(e)}")
        print("   Asegúrate de que las dependencias estén instaladas: pip install twilio")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
