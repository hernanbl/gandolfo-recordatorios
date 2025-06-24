#!/usr/bin/env python3
"""
Script de diagnóstico completo para el sistema de recordatorios.
Verifica configuración, conexiones y posibles problemas.
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_environment_variables():
    """Verificar variables de entorno requeridas"""
    print("🔧 VERIFICANDO VARIABLES DE ENTORNO")
    print("=" * 50)
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'TWILIO_WHATSAPP_NUMBER':
                print(f"✅ {var}: {value}")
            else:
                print(f"✅ {var}: {'*' * min(10, len(value))}...")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_supabase_connection():
    """Verificar conexión con Supabase"""
    print("\n🗄️  VERIFICANDO CONEXIÓN CON SUPABASE")
    print("=" * 50)
    
    try:
        from db.supabase_client import supabase_client
        
        # Probar conexión básica
        response = supabase_client.table('restaurantes').select('id, nombre').limit(1).execute()
        
        if hasattr(response, 'data') and response.data is not None:
            print("✅ Conexión con Supabase exitosa")
            return True
        else:
            print("❌ Conexión con Supabase falló - no se obtuvieron datos")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando con Supabase: {str(e)}")
        return False

def check_twilio_configuration():
    """Verificar configuración de Twilio"""
    print("\n📱 VERIFICANDO CONFIGURACIÓN DE TWILIO")
    print("=" * 50)
    
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
            print("❌ Faltan credenciales de Twilio")
            return False
        
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Verificar cuenta
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Cuenta Twilio: {account.friendly_name} (Status: {account.status})")
        
        # Listar números disponibles
        numbers = client.incoming_phone_numbers.list()
        if numbers:
            print(f"📞 Números disponibles en la cuenta:")
            for number in numbers:
                print(f"   - {number.phone_number} (SMS: {number.capabilities['sms']}, Voice: {number.capabilities['voice']})")
        else:
            print("⚠️  No hay números disponibles en la cuenta")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Twilio: {str(e)}")
        return False

def check_reservations_for_tomorrow():
    """Verificar reservas para mañana"""
    print("\n📅 VERIFICANDO RESERVAS PARA MAÑANA")
    print("=" * 50)
    
    try:
        from db.supabase_client import supabase_client
        from config import RESERVAS_TABLE
        
        # Calcular fecha de mañana
        argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(argentina_tz)
        tomorrow = (now + timedelta(days=1)).date()
        
        print(f"🕒 Fecha actual (Argentina): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 Buscando reservas para: {tomorrow}")
        
        # Buscar reservas para mañana sin recordatorio enviado
        response = supabase_client.table(RESERVAS_TABLE)\
            .select('id, nombre_cliente, telefono, fecha, hora, restaurante_id, recordatorio_enviado')\
            .eq('fecha', str(tomorrow))\
            .execute()
        
        if hasattr(response, 'data') and response.data:
            total_reservas = len(response.data)
            reservas_sin_recordatorio = [r for r in response.data if not r.get('recordatorio_enviado', False)]
            
            print(f"📊 Total reservas para mañana: {total_reservas}")
            print(f"📊 Reservas sin recordatorio: {len(reservas_sin_recordatorio)}")
            
            if reservas_sin_recordatorio:
                print(f"📋 Reservas que necesitan recordatorio:")
                for reserva in reservas_sin_recordatorio:
                    print(f"   - {reserva['nombre_cliente']} | {reserva['telefono']} | {reserva['hora']} | Restaurante: {reserva.get('restaurante_id', 'N/A')}")
            
            return len(reservas_sin_recordatorio) > 0
        else:
            print("ℹ️  No hay reservas para mañana")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando reservas: {str(e)}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA DE RECORDATORIOS")
    print("=" * 60)
    print(f"🕒 Ejecutado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_ok = True
    
    # Verificar variables de entorno
    env_ok, missing_vars = check_environment_variables()
    if not env_ok:
        print(f"\n❌ Variables faltantes: {', '.join(missing_vars)}")
        all_ok = False
    
    # Verificar Supabase
    supabase_ok = check_supabase_connection()
    if not supabase_ok:
        all_ok = False
    
    # Verificar Twilio
    twilio_ok = check_twilio_configuration()
    if not twilio_ok:
        all_ok = False
    
    # Verificar reservas
    reservations_found = check_reservations_for_tomorrow()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    status = "✅ SISTEMA OK" if all_ok else "❌ PROBLEMAS DETECTADOS"
    print(f"Estado general: {status}")
    print(f"Variables de entorno: {'✅' if env_ok else '❌'}")
    print(f"Conexión Supabase: {'✅' if supabase_ok else '❌'}")
    print(f"Configuración Twilio: {'✅' if twilio_ok else '❌'}")
    print(f"Reservas para procesar: {'✅' if reservations_found else 'ℹ️  Ninguna'}")
    
    if not all_ok:
        print("\n🔧 ACCIONES RECOMENDADAS:")
        if not env_ok:
            print("   1. Configurar variables de entorno faltantes en Render")
        if not supabase_ok:
            print("   2. Verificar credenciales y conexión con Supabase")
        if not twilio_ok:
            print("   3. Verificar configuración de Twilio y números de WhatsApp")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
