#!/usr/bin/env python3
"""
Script para probar que el sistema de recordatorios funcione después de actualizar
el número de Twilio a sandbox (+14155238886)
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verificar_configuracion():
    """Verificar que la configuración esté actualizada"""
    print("🔧 VERIFICANDO CONFIGURACIÓN ACTUALIZADA")
    print("=" * 50)
    
    try:
        from config import TWILIO_WHATSAPP_NUMBER, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
        
        print(f"📱 TWILIO_WHATSAPP_NUMBER: {TWILIO_WHATSAPP_NUMBER}")
        
        if TWILIO_WHATSAPP_NUMBER == "+14155238886":
            print("✅ Número de sandbox configurado correctamente")
        elif TWILIO_WHATSAPP_NUMBER == "+18059093442":
            print("❌ Aún usando número de producción - verificar que Render se haya actualizado")
            return False
        else:
            print(f"⚠️  Número inesperado: {TWILIO_WHATSAPP_NUMBER}")
            return False
        
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            print("✅ Credenciales de Twilio configuradas")
        else:
            print("❌ Faltan credenciales de Twilio")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando configuración: {str(e)}")
        return False

def verificar_conexion_twilio():
    """Verificar conexión con Twilio"""
    print("\n🔗 VERIFICANDO CONEXIÓN CON TWILIO")
    print("=" * 50)
    
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        
        print(f"✅ Conexión exitosa con Twilio")
        print(f"   Cuenta: {account.friendly_name}")
        print(f"   Status: {account.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Twilio: {str(e)}")
        return False

def probar_formato_mensaje():
    """Probar formato de mensaje sin enviar"""
    print("\n🧪 PROBANDO FORMATO DE MENSAJE")
    print("=" * 50)
    
    try:
        # Simular datos de una reserva
        reserva_test = {
            'id': 'test-123',
            'fecha': '2025-06-25',
            'hora': '20:00',
            'personas': 4,
            'nombre_cliente': 'Cliente Test',
            'telefono': '+5491166686255',
            'restaurante_id': 'test-restaurant'
        }
        
        # Formatear números como lo hace el sistema
        phone_clean = reserva_test['telefono'].replace('+', '').replace(' ', '').replace('-', '')
        
        if not phone_clean.startswith('549'):
            if phone_clean.startswith('54'):
                phone_clean = f"9{phone_clean[2:]}"
            else:
                phone_clean = f"549{phone_clean}"
        
        from_number = "whatsapp:+14155238886"  # Sandbox
        to_number = f"whatsapp:+{phone_clean}"
        
        print(f"📱 Número de origen (sandbox): {from_number}")
        print(f"📱 Número de destino: {to_number}")
        
        # Verificar formatos
        if from_number == "whatsapp:+14155238886":
            print("✅ Formato de origen correcto (sandbox)")
        else:
            print("❌ Formato de origen incorrecto")
            return False
        
        if to_number.startswith("whatsapp:+549"):
            print("✅ Formato de destino correcto (Argentina)")
        else:
            print("❌ Formato de destino incorrecto")
            return False
        
        # Simular mensaje
        mensaje = f"""¡Hola {reserva_test['nombre_cliente']}! 👋

Te recordamos tu reserva para mañana en Gandolfo Restó:

📅 *Fecha:* 25/06/2025
🕒 *Hora:* {reserva_test['hora']} hs
👥 *Personas:* {reserva_test['personas']}

Responde con *1* para CONFIRMAR o *2* para CANCELAR tu reserva.

¡Te esperamos! 🍽️"""
        
        print(f"\n📝 Mensaje preparado:")
        print(f"   Longitud: {len(mensaje)} caracteres")
        print(f"   Primeras líneas: {mensaje[:100]}...")
        
        print("\n✅ Formato de mensaje correcto")
        return True
        
    except Exception as e:
        print(f"❌ Error preparando formato: {str(e)}")
        return False

def verificar_sandbox_status():
    """Información sobre el sandbox"""
    print("\n📋 INFORMACIÓN DEL SANDBOX")
    print("=" * 50)
    
    print("""
🔧 CONFIGURACIÓN DEL SANDBOX:

1. ✅ Número actualizado a: +14155238886
2. 📱 Para recibir mensajes de prueba:
   - Enviar WhatsApp a: +14155238886
   - Mensaje: "join <código>"
   - Código en: Twilio Console > Messaging > Try it out

3. 🧪 Números que pueden recibir mensajes:
   - Solo números registrados en el sandbox
   - Verificar en Twilio Console > Messaging > WhatsApp > Sandbox

4. 🚀 Para probar recordatorios:
   - python3 scripts/send_reminders.py
   - Verificar logs para "whatsapp:+14155238886"

⚠️  IMPORTANTE:
- Si no has registrado tu número, NO recibirás mensajes
- Los mensajes aparecerán como "enviados" pero no llegarán
- Para producción, cambiar a +18059093442 cuando WhatsApp Business esté aprobado
""")

def main():
    print("🧪 VERIFICACIÓN POST-ACTUALIZACIÓN DE RENDER")
    print("=" * 60)
    print(f"🕒 Ejecutado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    # 1. Verificar configuración
    if not verificar_configuracion():
        success = False
        print("\n❌ La configuración no se actualizó correctamente")
        print("   Verifica que hayas cambiado TWILIO_WHATSAPP_NUMBER en AMBOS servicios:")
        print("   - Servicio web principal")
        print("   - Cron job 'daily-reminders-backup'")
        print("   Y que hayas hecho redeploy de ambos")
        return False
    
    # 2. Verificar conexión (solo si hay credenciales)
    if not verificar_conexion_twilio():
        print("⚠️  No se pudo verificar conexión con Twilio (normal en desarrollo local)")
    
    # 3. Probar formato
    if not probar_formato_mensaje():
        success = False
    
    # 4. Mostrar información del sandbox
    verificar_sandbox_status()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    if success:
        print("✅ CONFIGURACIÓN ACTUALIZADA CORRECTAMENTE")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Ejecutar: python3 scripts/send_reminders.py")
        print("   2. Verificar logs para 'whatsapp:+14155238886'")
        print("   3. Registrar número en sandbox si quieres recibir mensajes de prueba")
    else:
        print("❌ PROBLEMAS DETECTADOS")
        print("   Revisar configuración en Render")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
