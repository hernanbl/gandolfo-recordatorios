#!/usr/bin/env python3
"""
Script de prueba para el sistema de recordatorios
Permite crear reservas de prueba y probar el envío de recordatorios
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import pytz

# Add the project root to the Python path
app_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, app_dir)

from dotenv import load_dotenv

# Cargar variables de entorno
env_file = os.path.join(app_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zona horaria Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

try:
    from db.supabase_client import supabase_client
    from config import RESERVAS_TABLE, DEFAULT_RESTAURANT_ID
    from services.recordatorio_service import enviar_recordatorios_reservas
except ImportError as e:
    logger.error(f"Error importando módulos: {str(e)}")
    sys.exit(1)

def verificar_configuracion():
    """Verifica que la configuración esté correcta"""
    print("=== VERIFICACIÓN DE CONFIGURACIÓN ===")
    
    # Variables de entorno requeridas
    required_vars = [
        'SUPABASE_URL', 'SUPABASE_KEY', 
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER'
    ]
    
    print("1. Variables de entorno:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: configurado")
        else:
            print(f"   ❌ {var}: NO configurado")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Faltan variables: {', '.join(missing_vars)}")
        return False
    
    # Conexión a Supabase
    print("\n2. Conexión a Supabase:")
    try:
        if supabase_client:
            print("   ✅ Cliente Supabase inicializado")
            
            # Probar consulta simple
            response = supabase_client.table(RESERVAS_TABLE).select('id').limit(1).execute()
            if hasattr(response, 'data'):
                print("   ✅ Consulta a tabla de reservas exitosa")
            else:
                print("   ❌ Error en consulta a tabla de reservas")
                return False
        else:
            print("   ❌ Cliente Supabase no inicializado")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando a Supabase: {str(e)}")
        return False
    
    print("\n✅ Configuración correcta")
    return True

def mostrar_reservas_proximas():
    """Muestra las reservas próximas en la base de datos"""
    print("\n=== RESERVAS PRÓXIMAS ===")
    
    # Fechas en zona horaria Argentina
    ahora_argentina = datetime.now(ARGENTINA_TZ)
    manana_argentina = ahora_argentina + timedelta(days=1)
    pasado_manana = ahora_argentina + timedelta(days=2)
    
    fechas_consulta = [
        (ahora_argentina, "Hoy"),
        (manana_argentina, "Mañana"),
        (pasado_manana, "Pasado mañana")
    ]
    
    for fecha_obj, etiqueta in fechas_consulta:
        fecha_db = fecha_obj.strftime('%Y-%m-%d')
        fecha_display = fecha_obj.strftime('%d/%m/%Y')
        
        try:
            response = supabase_client.table(RESERVAS_TABLE)\
                .select('id,nombre,telefono,hora,estado,recordatorio_enviado')\
                .eq('fecha', fecha_db)\
                .order('hora')\
                .execute()
            
            if response.data:
                print(f"\n📅 {etiqueta} ({fecha_display}):")
                for reserva in response.data:
                    recordatorio_status = "✅" if reserva.get('recordatorio_enviado') else "⏳"
                    print(f"   {recordatorio_status} ID: {reserva['id']} | {reserva.get('nombre')} | {reserva.get('hora')} | Estado: {reserva.get('estado')}")
            else:
                print(f"\n📅 {etiqueta} ({fecha_display}): Sin reservas")
                
        except Exception as e:
            print(f"\n❌ Error consultando {etiqueta}: {str(e)}")

def crear_reserva_prueba():
    """Crea una reserva de prueba para mañana"""
    print("\n=== CREAR RESERVA DE PRUEBA ===")
    
    # Pedir datos al usuario
    nombre = input("Nombre del cliente (default: Test Recordatorio): ").strip()
    if not nombre:
        nombre = "Test Recordatorio"
    
    telefono = input("Teléfono (default: 1166686255): ").strip()
    if not telefono:
        telefono = "1166686255"
    
    hora = input("Hora (default: 20:00): ").strip()
    if not hora:
        hora = "20:00"
    
    personas = input("Cantidad de personas (default: 2): ").strip()
    if not personas:
        personas = "2"
    
    # Fecha para mañana
    manana_argentina = datetime.now(ARGENTINA_TZ) + timedelta(days=1)
    fecha_db = manana_argentina.strftime('%Y-%m-%d')
    fecha_display = manana_argentina.strftime('%d/%m/%Y')
    
    # Datos de la reserva
    reserva_data = {
        'nombre': nombre,
        'fecha': fecha_db,
        'hora': hora,
        'personas': int(personas),
        'telefono': telefono,
        'email': 'test@example.com',
        'comentarios': 'Reserva de prueba para sistema de recordatorios',
        'estado': 'Confirmada',
        'origen': 'test_recordatorio',
        'recordatorio_enviado': False
    }
    
    # Agregar restaurant_id si está configurado
    if DEFAULT_RESTAURANT_ID:
        reserva_data['restaurante_id'] = DEFAULT_RESTAURANT_ID
    
    print(f"\nCreando reserva de prueba:")
    print(f"   👤 Cliente: {nombre}")
    print(f"   📅 Fecha: {fecha_display}")
    print(f"   🕒 Hora: {hora}")
    print(f"   👥 Personas: {personas}")
    print(f"   📞 Teléfono: {telefono}")
    
    try:
        response = supabase_client.table(RESERVAS_TABLE).insert(reserva_data).execute()
        
        if response.data:
            reserva_id = response.data[0]['id']
            print(f"\n✅ Reserva de prueba creada exitosamente!")
            print(f"   🆔 ID: {reserva_id}")
            return reserva_id
        else:
            print(f"\n❌ Error creando reserva de prueba")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def probar_recordatorios():
    """Prueba el sistema de recordatorios"""
    print("\n=== PROBAR SISTEMA DE RECORDATORIOS ===")
    
    try:
        # Establecer modo de prueba
        os.environ['TEST_MODE'] = 'true'
        
        print("🧪 Ejecutando recordatorios en modo de prueba...")
        resultado = enviar_recordatorios_reservas()
        
        print(f"\n📋 Resultado: {resultado}")
        
        if resultado.get('success'):
            reservas_encontradas = resultado.get('reservas_encontradas', 0)
            mensajes_enviados = resultado.get('mensajes_enviados', 0)
            mensajes_fallidos = resultado.get('mensajes_fallidos', 0)
            
            print(f"\n✅ Proceso completado:")
            print(f"   📊 Reservas encontradas: {reservas_encontradas}")
            print(f"   ✅ Mensajes enviados: {mensajes_enviados}")
            print(f"   ❌ Mensajes fallidos: {mensajes_fallidos}")
            
            if resultado.get('errores'):
                print(f"   ⚠️  Errores:")
                for error in resultado['errores']:
                    print(f"      - {error}")
        else:
            print(f"❌ Error en el proceso: {resultado.get('error')}")
            
    except Exception as e:
        print(f"❌ Error probando recordatorios: {str(e)}")
    finally:
        # Limpiar modo de prueba
        if 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']

def eliminar_reserva_prueba():
    """Elimina reservas de prueba"""
    print("\n=== ELIMINAR RESERVAS DE PRUEBA ===")
    
    try:
        # Buscar reservas de prueba
        response = supabase_client.table(RESERVAS_TABLE)\
            .select('id,nombre,fecha,hora')\
            .eq('origen', 'test_recordatorio')\
            .execute()
        
        if not response.data:
            print("ℹ️  No se encontraron reservas de prueba")
            return
        
        print(f"📋 Encontradas {len(response.data)} reservas de prueba:")
        for reserva in response.data:
            print(f"   🆔 {reserva['id']} - {reserva['nombre']} - {reserva['fecha']} {reserva['hora']}")
        
        confirmar = input("\n¿Eliminar todas las reservas de prueba? (s/N): ").strip().lower()
        if confirmar == 's':
            delete_response = supabase_client.table(RESERVAS_TABLE)\
                .delete()\
                .eq('origen', 'test_recordatorio')\
                .execute()
            
            print(f"✅ Reservas de prueba eliminadas")
        else:
            print("ℹ️  Operación cancelada")
            
    except Exception as e:
        print(f"❌ Error eliminando reservas de prueba: {str(e)}")

def main():
    """Menú principal"""
    print("🤖 SISTEMA DE PRUEBA DE RECORDATORIOS")
    print("=====================================")
    
    while True:
        print("\nSelecciona una opción:")
        print("1. Verificar configuración")
        print("2. Mostrar reservas próximas")
        print("3. Crear reserva de prueba para mañana")
        print("4. Probar sistema de recordatorios")
        print("5. Eliminar reservas de prueba")
        print("6. Prueba completa (crear reserva + probar recordatorio)")
        print("0. Salir")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == '1':
            verificar_configuracion()
        elif opcion == '2':
            mostrar_reservas_proximas()
        elif opcion == '3':
            crear_reserva_prueba()
        elif opcion == '4':
            probar_recordatorios()
        elif opcion == '5':
            eliminar_reserva_prueba()
        elif opcion == '6':
            print("\n🚀 EJECUTANDO PRUEBA COMPLETA")
            if verificar_configuracion():
                reserva_id = crear_reserva_prueba()
                if reserva_id:
                    input("\nPresiona Enter para probar el envío de recordatorios...")
                    probar_recordatorios()
        elif opcion == '0':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
