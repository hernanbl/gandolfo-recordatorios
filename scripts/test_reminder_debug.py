#!/usr/bin/env python3
"""
Script de prueba para envío de recordatorios con debugging extendido.
Útil para diagnosticar problemas en producción.
"""

import sys
import os
from datetime import datetime, timedelta
import pytz
import logging

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_single_reminder():
    """Probar envío de un recordatorio simple"""
    logger.info("🧪 PRUEBA DE ENVÍO DE RECORDATORIO ÚNICO")
    logger.info("=" * 50)
    
    try:
        # Importar dependencias
        from db.supabase_client import supabase_client
        from config import RESERVAS_TABLE, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
        
        # Verificar configuración
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
            logger.error("❌ Faltan credenciales de Twilio")
            return False
        
        logger.info(f"📱 Usando número Twilio: {TWILIO_WHATSAPP_NUMBER}")
        
        # Buscar una reserva para mañana
        argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')
        tomorrow = (datetime.now(argentina_tz) + timedelta(days=1)).date()
        
        response = supabase_client.table(RESERVAS_TABLE)\
            .select('*')\
            .eq('fecha', str(tomorrow))\
            .eq('recordatorio_enviado', False)\
            .limit(1)\
            .execute()
        
        if not hasattr(response, 'data') or not response.data:
            logger.info("ℹ️  No hay reservas disponibles para prueba")
            return False
        
        reserva = response.data[0]
        logger.info(f"📋 Probando con reserva: {reserva['id']}")
        logger.info(f"👤 Cliente: {reserva.get('nombre_cliente', 'N/A')}")
        logger.info(f"📞 Teléfono: {reserva.get('telefono', 'N/A')}")
        
        # Intentar envío simple con Twilio directo
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Preparar números
        phone_clean = reserva['telefono'].replace('+', '').replace(' ', '').replace('-', '')
        if not phone_clean.startswith('549'):
            if phone_clean.startswith('54'):
                phone_clean = f"9{phone_clean[2:]}"
            else:
                phone_clean = f"549{phone_clean}"
        
        to_number = f"whatsapp:+{phone_clean}"
        from_number = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}" if not TWILIO_WHATSAPP_NUMBER.startswith('whatsapp:') else TWILIO_WHATSAPP_NUMBER
        
        logger.info(f"📤 Enviando desde: {from_number}")
        logger.info(f"📥 Enviando hacia: {to_number}")
        
        # Mensaje simple de prueba
        mensaje = f"""🧪 PRUEBA DE RECORDATORIO
        
Hola {reserva.get('nombre_cliente', 'Cliente')}!

Esta es una prueba del sistema de recordatorios.

Fecha: {tomorrow}
Hora: {reserva['hora']}
        
Este es un mensaje de prueba."""
        
        # Enviar mensaje
        try:
            message = client.messages.create(
                body=mensaje,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"✅ Mensaje enviado exitosamente!")
            logger.info(f"📱 SID: {message.sid}")
            logger.info(f"🔍 Status: {message.status}")
            
            return True
            
        except Exception as send_error:
            logger.error(f"❌ Error enviando mensaje: {str(send_error)}")
            
            # Diagnosticar el error específico
            if "Channel with the specified From address" in str(send_error):
                logger.error("🚨 PROBLEMA: El número WhatsApp no está configurado correctamente en Twilio")
                logger.error(f"   Número usado: {from_number}")
                logger.error("   Soluciones:")
                logger.error("   1. Verifica que el número esté habilitado para WhatsApp en Twilio Console")
                logger.error("   2. Verifica que TWILIO_WHATSAPP_NUMBER tenga el formato correcto")
                logger.error("   3. Verifica que tengas una cuenta WhatsApp Business aprobada")
                
                # Listar números disponibles
                try:
                    numbers = client.incoming_phone_numbers.list()
                    if numbers:
                        logger.info("📞 Números disponibles en tu cuenta Twilio:")
                        for num in numbers:
                            logger.info(f"   - {num.phone_number}")
                    else:
                        logger.error("❌ No hay números disponibles en la cuenta")
                except:
                    logger.error("❌ No se pudieron listar los números disponibles")
                    
            return False
            
    except Exception as e:
        logger.error(f"❌ Error general: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Función principal"""
    logger.info("🔍 PRUEBA DE DIAGNÓSTICO DE RECORDATORIOS")
    logger.info("=" * 60)
    
    success = test_single_reminder()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ PRUEBA EXITOSA - El sistema está funcionando")
    else:
        logger.info("❌ PRUEBA FALLIDA - Revisar logs para detalles")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
