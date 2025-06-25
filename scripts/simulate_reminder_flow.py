#!/usr/bin/env python3
"""
Script para simular el flujo completo de recordatorios de WhatsApp
Permite probar la funcionalidad sin esperar al cron programado
"""

import sys
import os
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.supabase_client import supabase_client
from services.twilio.messaging import send_whatsapp_message
from utils.session_manager import save_session
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Volumes/AUDIO/gandolfo-recordatorios/logs/simulate_reminder.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class ReminderSimulator:
    def __init__(self):
        self.supabase = supabase_client
    
    def create_test_reservation(self, test_phone="+5491123456789", hours_ahead=25):
        """
        Crea una reserva de prueba para simular recordatorio
        """
        try:
            # Crear fecha de mañana 
            tomorrow = date.today() + timedelta(days=1)
            
            # Datos de reserva de prueba
            reserva_data = {
                'restaurante_id': 'e0f20795-d325-4af1-8603-1c52050048db',  # Gandolfo restó
                'fecha': tomorrow.isoformat(),
                'hora': '20:00',
                'personas': 2,
                'nombre_cliente': 'Test Recordatorio Usuario',
                'telefono': test_phone,
                'email': 'test@ejemplo.com',
                'estado': 'Confirmada',
                'origen': 'test_reminder_simulation',
                'comentarios': f'Reserva de prueba para simular recordatorio - {datetime.now()}'
            }
            
            logger.info(f"🧪 CREANDO RESERVA DE PRUEBA: {reserva_data}")
            
            # Insertar en la base de datos
            result = self.supabase.table("reservas_prod").insert(reserva_data).execute()
            
            if result.data and len(result.data) > 0:
                reservation_id = result.data[0]['id']
                logger.info(f"✅ RESERVA DE PRUEBA CREADA: ID {reservation_id}")
                return reservation_id, reserva_data
            else:
                logger.error("❌ Error: No se pudo crear la reserva de prueba")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ ERROR creando reserva de prueba: {str(e)}")
            return None, None
    
    def simulate_reminder_sending(self, reservation_id, phone_number, reserva_data):
        """
        Simula el envío de recordatorio y configura la sesión correctamente
        """
        try:
            logger.info(f"📱 SIMULANDO ENVÍO DE RECORDATORIO para reserva {reservation_id}")
            
            # Obtener configuración del restaurante desde la base de datos
            restaurant_result = self.supabase.table("restaurantes").select("*").eq('id', reserva_data['restaurante_id']).execute()
            if not restaurant_result.data:
                logger.error(f"❌ No se encontró el restaurante {reserva_data['restaurante_id']}")
                return False
            
            restaurant_data = restaurant_result.data[0]
            restaurant_name = restaurant_data.get('nombre', 'el restaurante')
            
            # Formatear fecha en español para el mensaje
            fecha_obj = datetime.strptime(reserva_data['fecha'], "%Y-%m-%d").date()
            
            # Mapeo de días en español (igual que en reservation_handler.py)
            DIAS_SEMANA = {
                'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
                'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
            }
            
            MESES = {
                'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
                'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
                'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
            }
            
            # Formatear fecha en español
            dia_semana_en = fecha_obj.strftime("%A")
            mes_en = fecha_obj.strftime("%B")
            dia = fecha_obj.strftime("%d")
            año = fecha_obj.strftime("%Y")
            
            dia_semana_es = DIAS_SEMANA.get(dia_semana_en, dia_semana_en.lower())
            mes_es = MESES.get(mes_en, mes_en.lower())
            fecha_formateada = f"{dia_semana_es} {dia} de {mes_es} de {año}"
            
            # 🔥 CRÍTICO: Configurar sesión EXACTAMENTE como lo hace el sistema real
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
            
            # Guardar sesión con los datos de recordatorio
            save_session(phone_number, session_data, reserva_data['restaurante_id'])
            
            logger.info(f"💾 SESIÓN CONFIGURADA: {session_data}")
            
            # Crear mensaje de recordatorio (igual que en recordatorio_service.py)
            primer_nombre = reserva_data['nombre_cliente'].split()[0]
            
            mensaje = f"🔔 **Recordatorio de Reserva**\n\n"
            mensaje += f"Hola {primer_nombre}! 👋\n\n"
            mensaje += f"Te recordamos tu reserva en {restaurant_name}:\n\n"
            mensaje += f"📅 **{fecha_formateada}**\n"
            mensaje += f"🕗 **{reserva_data['hora']}**\n" 
            mensaje += f"👥 **{reserva_data['personas']} persona{'s' if reserva_data['personas'] > 1 else ''}**\n\n"
            mensaje += "Por favor confirma tu asistencia:\n\n"
            mensaje += "✅ Responde **1** para CONFIRMAR\n"
            mensaje += "❌ Responde **2** para CANCELAR\n\n"
            mensaje += "¡Esperamos verte pronto! 😊"
            
            # Enviar mensaje de recordatorio
            logger.info(f"📤 ENVIANDO RECORDATORIO: {mensaje}")
            success = send_whatsapp_message(phone_number, mensaje, restaurant_data)
            
            if success:
                logger.info(f"✅ RECORDATORIO ENVIADO EXITOSAMENTE")
                logger.info(f"🎯 LISTO PARA PRUEBA: Envía '1' o '2' desde {phone_number} para probar")
                return True
            else:
                logger.error(f"❌ ERROR enviando recordatorio")
                return False
                
        except Exception as e:
            logger.error(f"❌ ERROR simulando recordatorio: {str(e)}")
            return False
    
    def test_manual_response(self, phone_number, response_message):
        """
        Simula una respuesta manual para probar el webhook
        """
        try:
            logger.info(f"🧪 SIMULANDO RESPUESTA MANUAL: {phone_number} -> '{response_message}'")
            
            # Hacer una petición POST simulada al webhook
            import requests
            
            webhook_url = "https://your-app.render.com/webhook/whatsapp"  # Cambiar por tu URL real
            
            # Simular el payload que Twilio envía
            webhook_data = {
                'From': phone_number,
                'Body': response_message,
                'MessageSid': f'test_sid_{datetime.now().timestamp()}',
                'AccountSid': 'test_account_sid'
            }
            
            logger.info(f"📤 ENVIANDO AL WEBHOOK: {webhook_data}")
            
            # Hacer la petición (opcional, para apps en producción)
            # response = requests.post(webhook_url, data=webhook_data)
            # logger.info(f"📥 RESPUESTA WEBHOOK: {response.status_code} - {response.text}")
            
            logger.info("🎯 RESPUESTA SIMULADA ENVIADA - Revisa los logs del webhook")
            
        except Exception as e:
            logger.error(f"❌ ERROR simulando respuesta: {str(e)}")
    
    def cleanup_test_reservation(self, reservation_id):
        """
        Limpia la reserva de prueba después del test
        """
        try:
            if reservation_id:
                logger.info(f"🧹 LIMPIANDO RESERVA DE PRUEBA: {reservation_id}")
                result = self.supabase.table("reservas_prod").delete().eq('id', reservation_id).execute()
                if result.data:
                    logger.info(f"✅ RESERVA DE PRUEBA ELIMINADA")
                else:
                    logger.warning(f"⚠️ No se pudo eliminar la reserva de prueba")
        except Exception as e:
            logger.error(f"❌ ERROR limpiando reserva: {str(e)}")

def main():
    print("🧪 SIMULADOR DE RECORDATORIOS DE WHATSAPP")
    print("="*50)
    
    simulator = ReminderSimulator()
    
    # Solicitar número de teléfono
    test_phone = input("📱 Ingresa el número de WhatsApp para la prueba (ej: +5491123456789): ").strip()
    if not test_phone:
        test_phone = "+5491123456789"  # Número por defecto
    
    print(f"\n🚀 Iniciando simulación con {test_phone}")
    
    # Paso 1: Crear reserva de prueba
    print("\n📋 PASO 1: Creando reserva de prueba...")
    reservation_id, reserva_data = simulator.create_test_reservation(test_phone)
    
    if not reservation_id:
        print("❌ No se pudo crear la reserva de prueba")
        return
    
    print(f"✅ Reserva de prueba creada: ID {reservation_id}")
    
    # Paso 2: Simular envío de recordatorio
    print("\n📱 PASO 2: Simulando envío de recordatorio...")
    success = simulator.simulate_reminder_sending(reservation_id, test_phone, reserva_data)
    
    if not success:
        print("❌ No se pudo simular el recordatorio")
        simulator.cleanup_test_reservation(reservation_id)
        return
    
    print("✅ Recordatorio simulado enviado")
    
    # Paso 3: Instrucciones para el usuario
    print("\n🎯 PASO 3: PRUEBA INTERACTIVA")
    print("-" * 30)
    print(f"1. Envía un mensaje desde {test_phone} con '1' para confirmar")
    print(f"2. O envía '2' para cancelar")
    print("3. Observa los logs del webhook para ver si se detecta correctamente")
    print("4. Verifica si se actualiza el estado de la reserva en la base de datos")
    
    # Opción para simulación automática
    print("\n🤖 OPCIÓN AUTOMÁTICA:")
    auto_test = input("¿Quieres simular automáticamente una respuesta? (y/n): ").strip().lower()
    
    if auto_test == 'y':
        response = input("Ingresa la respuesta a simular (1 o 2): ").strip()
        simulator.test_manual_response(test_phone, response)
    
    # Preguntar si limpiar
    print("\n🧹 LIMPIEZA:")
    cleanup = input("¿Quieres eliminar la reserva de prueba? (y/n): ").strip().lower()
    
    if cleanup == 'y':
        simulator.cleanup_test_reservation(reservation_id)
    else:
        print(f"📌 Reserva de prueba conservada: ID {reservation_id}")
    
    print("\n✅ Simulación completada!")
    print("🔍 Revisa los logs en /logs/simulate_reminder.log para más detalles")

if __name__ == "__main__":
    main()
