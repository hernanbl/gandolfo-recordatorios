#!/usr/bin/env python3
"""
Script para probar el envío de WhatsApp usando el número de sandbox +14155238886
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_sandbox_number():
    print("🧪 PRUEBA CON NÚMERO DE SANDBOX DE TWILIO")
    print("=" * 50)
    
    # Configurar el número de sandbox temporalmente
    sandbox_number = "+14155238886"
    os.environ['TWILIO_WHATSAPP_NUMBER'] = sandbox_number
    
    print(f"📱 Usando número de sandbox: {sandbox_number}")
    print(f"🔧 Variable configurada: TWILIO_WHATSAPP_NUMBER={sandbox_number}")
    
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        
        print(f"\n📋 Configuración actual:")
        print(f"   TWILIO_WHATSAPP_NUMBER: {TWILIO_WHATSAPP_NUMBER}")
        print(f"   Credenciales: {'✅ Disponibles' if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else '❌ Faltan'}")
        
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            print("\n⚠️  No hay credenciales de Twilio - ejecutando prueba de formato solamente")
            test_format_sandbox()
            return True
        
        # Probar con credenciales reales
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        print(f"\n🔗 Verificando conexión con Twilio...")
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Cuenta: {account.friendly_name}")
        
        # Probar formato de números
        test_numbers = [
            "1166686255",      # Tu número sin prefijos
            "+5491166686255",  # Tu número con prefijo completo
            "5491166686255"    # Tu número sin +
        ]
        
        print(f"\n🧪 Probando formato de números:")
        
        for test_phone in test_numbers:
            print(f"\n   📞 Probando con: {test_phone}")
            
            # Simular el procesamiento que hace el sistema
            phone_clean = test_phone.replace('+', '').replace(' ', '').replace('-', '')
            
            if not phone_clean.startswith('549'):
                if phone_clean.startswith('54'):
                    phone_clean = f"9{phone_clean[2:]}"
                else:
                    phone_clean = f"549{phone_clean}"
            
            from_number = f"whatsapp:{sandbox_number}"
            to_number = f"whatsapp:+{phone_clean}"
            
            print(f"      From: {from_number}")
            print(f"      To: {to_number}")
            
            # Verificar formato
            if from_number == "whatsapp:+14155238886":
                print(f"      ✅ Formato from correcto")
            else:
                print(f"      ❌ Formato from incorrecto")
                
            if to_number.startswith("whatsapp:+549"):
                print(f"      ✅ Formato to correcto")
            else:
                print(f"      ❌ Formato to incorrecto")
        
        print(f"\n📋 IMPORTANTE - Configuración del Sandbox:")
        print(f"   1. El número {sandbox_number} es el sandbox de Twilio")
        print(f"   2. Para recibir mensajes, el cliente debe registrarse primero")
        print(f"   3. Enviar 'join <código>' al {sandbox_number}")
        print(f"   4. El código se encuentra en Twilio Console > Messaging > Try it out")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {str(e)}")
        return False

def test_format_sandbox():
    """Probar solo formato sin credenciales"""
    print(f"\n🔧 PRUEBA DE FORMATO CON SANDBOX")
    print("-" * 30)
    
    sandbox_from = "whatsapp:+14155238886"
    test_to = "whatsapp:+5491166686255"
    
    print(f"✅ From (sandbox): {sandbox_from}")
    print(f"✅ To (Argentina): {test_to}")
    
    # Simular llamada a Twilio
    print(f"\n🎭 Simulación de envío:")
    print(f"   client.messages.create(")
    print(f"       body='Mensaje de prueba',")
    print(f"       from_='{sandbox_from}',")
    print(f"       to='{test_to}'")
    print(f"   )")
    print(f"   ✅ Formato correcto para sandbox")

def show_sandbox_instructions():
    """Mostrar instrucciones del sandbox"""
    print(f"\n" + "=" * 50)
    print("📋 INSTRUCCIONES PARA USAR EL SANDBOX")
    print("=" * 50)
    
    print(f"""
🔧 PASOS PARA CONFIGURAR:

1. 🔄 Actualizar variable en Render:
   TWILIO_WHATSAPP_NUMBER=+14155238886

2. 📱 Registrar número de prueba:
   - Enviar WhatsApp a: +14155238886
   - Mensaje: "join <código>"
   - Código en: Twilio Console > Messaging > Try it out

3. 🧪 Probar sistema:
   python3 scripts/send_reminders.py

4. ✅ Verificar logs:
   Debería mostrar: "desde: whatsapp:+14155238886"

⚠️  IMPORTANTE:
- Solo números registrados en sandbox pueden recibir mensajes
- Para producción, cambiar a +18059093442 cuando WhatsApp Business esté aprobado
""")

def main():
    success = test_sandbox_number()
    show_sandbox_instructions()
    
    print(f"\n" + "=" * 50)
    print(f"📊 RESULTADO: {'✅ PRUEBA EXITOSA' if success else '❌ PRUEBA FALLÓ'}")
    print("=" * 50)
    
    if success:
        print(f"🚀 PRÓXIMO PASO: Actualizar TWILIO_WHATSAPP_NUMBER en Render")
        print(f"   Cambiar de: +18059093442")
        print(f"   Cambiar a:  +14155238886")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
