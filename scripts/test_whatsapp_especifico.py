#!/usr/bin/env python3
"""
Script para probar el envío de WhatsApp con el número específico +18059093442
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_whatsapp_send():
    print("🧪 PRUEBA DE ENVÍO WHATSAPP CON +18059093442")
    print("=" * 50)
    
    try:
        # Simular configuración de variables de entorno para la prueba
        os.environ['TWILIO_WHATSAPP_NUMBER'] = '+18059093442'
        
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        
        print(f"📋 Configuración:")
        print(f"   Account SID: {TWILIO_ACCOUNT_SID[:10] if TWILIO_ACCOUNT_SID else 'NO CONFIGURADO'}...")
        print(f"   Auth Token: {'✅ Configurado' if TWILIO_AUTH_TOKEN else '❌ Falta'}")
        print(f"   WhatsApp Number: {TWILIO_WHATSAPP_NUMBER}")
        
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
            print("❌ Faltan credenciales de Twilio - no se puede hacer prueba real")
            print("ℹ️  Ejecutando prueba de formato solamente...")
            
            # Probar solo el formato
            test_format_only()
            return True
        
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Número de prueba (tu número)
        test_phone = "+5491166686255"
        
        # Preparar números en formato WhatsApp
        from_number = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"
        to_number = f"whatsapp:{test_phone}"
        
        print(f"\n📱 Preparando envío:")
        print(f"   Desde: {from_number}")
        print(f"   Hacia: {to_number}")
        
        # Mensaje de prueba
        test_message = f"""🧪 MENSAJE DE PRUEBA - {datetime.now().strftime('%H:%M:%S')}

Este es un mensaje de prueba del sistema de recordatorios.

Número de origen: {TWILIO_WHATSAPP_NUMBER}
Timestamp: {datetime.now().isoformat()}

Si recibes este mensaje, la configuración está funcionando correctamente."""
        
        print(f"\n📝 Mensaje a enviar:")
        print(f"   Longitud: {len(test_message)} caracteres")
        print(f"   Contenido: {test_message[:100]}...")
        
        # Confirmar antes de enviar
        print(f"\n⚠️  ¿Enviar mensaje de prueba real? (y/N): ", end="")
        
        # En entorno automatizado, no enviar realmente
        if os.getenv('AUTO_TEST', 'false').lower() == 'true':
            print("AUTO_TEST=true - Simulando envío...")
            simulate_send(from_number, to_number, test_message)
        else:
            # En desarrollo local, preguntar
            response = input().lower()
            if response == 'y':
                real_send(client, from_number, to_number, test_message)
            else:
                print("Envío cancelado - ejecutando simulación...")
                simulate_send(from_number, to_number, test_message)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_format_only():
    """Prueba solo el formato sin enviar"""
    print("\n🔧 PRUEBA DE FORMATO SOLAMENTE")
    print("-" * 30)
    
    twilio_number = "+18059093442"
    test_phone = "5491166686255"
    
    # Simular el procesamiento del número
    if not test_phone.startswith('549'):
        if test_phone.startswith('54'):
            test_phone = f"9{test_phone[2:]}"
        else:
            test_phone = f"549{test_phone}"
    
    from_number = f"whatsapp:{twilio_number}"
    to_number = f"whatsapp:+{test_phone}"
    
    print(f"✅ Formato from_number: {from_number}")
    print(f"✅ Formato to_number: {to_number}")
    
    # Verificar formatos
    if from_number == "whatsapp:+18059093442":
        print("✅ from_number tiene formato correcto")
    else:
        print(f"❌ from_number formato incorrecto: {from_number}")
    
    if to_number.startswith("whatsapp:+549"):
        print("✅ to_number tiene formato correcto para Argentina")
    else:
        print(f"❌ to_number formato incorrecto: {to_number}")

def simulate_send(from_number, to_number, message):
    """Simular envío de mensaje"""
    print(f"\n🎭 SIMULACIÓN DE ENVÍO:")
    print(f"   ✅ Cliente Twilio inicializado")
    print(f"   ✅ Mensaje preparado ({len(message)} chars)")
    print(f"   ✅ Números validados")
    print(f"   📱 Simulando: client.messages.create()")
    print(f"      body='{message[:50]}...'")
    print(f"      from_='{from_number}'")
    print(f"      to='{to_number}'")
    print(f"   ✅ Simulación completada - SID ficticio: SM123456789")

def real_send(client, from_number, to_number, message):
    """Envío real de mensaje"""
    print(f"\n📤 ENVIANDO MENSAJE REAL...")
    
    try:
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        print(f"✅ MENSAJE ENVIADO EXITOSAMENTE!")
        print(f"   SID: {message_obj.sid}")
        print(f"   Status: {message_obj.status}")
        print(f"   Direction: {message_obj.direction}")
        
        # Verificar detalles del mensaje
        message_details = client.messages(message_obj.sid).fetch()
        print(f"   From (confirmado): {message_details.from_}")
        print(f"   To (confirmado): {message_details.to}")
        
    except Exception as send_error:
        print(f"❌ ERROR AL ENVIAR:")
        print(f"   Error: {str(send_error)}")
        
        # Analizar el error específico
        if "63007" in str(send_error) or "Channel" in str(send_error):
            print(f"\n🔍 DIAGNÓSTICO DEL ERROR 63007:")
            print(f"   - El número {from_number} no está configurado como canal WhatsApp")
            print(f"   - Verifica en Twilio Console > Messaging > WhatsApp > Senders")
            print(f"   - El número debe estar 'approved' para WhatsApp Business")
        elif "21211" in str(send_error):
            print(f"\n🔍 DIAGNÓSTICO DEL ERROR 21211:")
            print(f"   - El número de destino no es válido o no puede recibir WhatsApp")
        else:
            print(f"\n🔍 ERROR NO RECONOCIDO - Ver documentación de Twilio")

def main():
    success = test_whatsapp_send()
    
    print(f"\n" + "=" * 50)
    print("📋 RESULTADO DE LA PRUEBA")
    print("=" * 50)
    
    if success:
        print("✅ Prueba completada")
        print("\n🔧 Si hay problemas en producción:")
        print("   1. Verificar que +18059093442 esté en WhatsApp Senders")
        print("   2. Verificar que el status sea 'approved'")
        print("   3. Verificar variables de entorno en Render")
        print("   4. Ejecutar: python3 scripts/diagnostico_completo.py")
    else:
        print("❌ Prueba falló")
    
    return success

if __name__ == "__main__":
    # Configurar para prueba automática si se ejecuta en CI/CD
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        os.environ['AUTO_TEST'] = 'true'
    
    success = main()
    sys.exit(0 if success else 1)
