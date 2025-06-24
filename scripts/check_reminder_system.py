#!/usr/bin/env python3
"""
Script de verificación del sistema de recordatorios
Se ejecuta diariamente a las 9:00 AM para verificar que todo esté listo
para el envío de recordatorios a las 10:00 AM
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Add the project root to the Python path
app_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, app_dir)

# Cargar variables de entorno
env_file = os.path.join(app_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Configurar zona horaria de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

# Configure logging
log_dir = os.path.join(app_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'system_check.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno estén configuradas"""
    logger.info("🔍 Verificando variables de entorno...")
    
    required_vars = [
        'SUPABASE_URL', 'SUPABASE_KEY', 
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"❌ Variable de entorno faltante: {var}")
        else:
            logger.info(f"✅ {var}: configurado")
    
    if missing_vars:
        logger.error(f"❌ Faltan {len(missing_vars)} variables de entorno críticas")
        return False
    
    logger.info("✅ Todas las variables de entorno están configuradas")
    return True

def verificar_conexion_supabase():
    """Verifica la conexión con Supabase"""
    logger.info("🔍 Verificando conexión con Supabase...")
    
    try:
        from db.supabase_client import supabase_client
        from config import RESERVAS_TABLE
        
        if not supabase_client:
            logger.error("❌ Cliente Supabase no inicializado")
            return False
        
        # Probar consulta simple
        response = supabase_client.table(RESERVAS_TABLE).select('id').limit(1).execute()
        
        if hasattr(response, 'data'):
            logger.info("✅ Conexión con Supabase exitosa")
            return True
        else:
            logger.error("❌ Error en respuesta de Supabase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error conectando con Supabase: {str(e)}")
        return False

def verificar_conexion_twilio():
    """Verifica la conexión con Twilio"""
    logger.info("🔍 Verificando conexión con Twilio...")
    
    try:
        from twilio.rest import Client
        
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        client = Client(twilio_account_sid, twilio_auth_token)
        
        # Obtener información de la cuenta
        account = client.api.accounts(twilio_account_sid).fetch()
        
        if account.status == 'active':
            logger.info("✅ Conexión con Twilio exitosa")
            logger.info(f"   Cuenta: {account.friendly_name}")
            return True
        else:
            logger.error(f"❌ Cuenta Twilio no activa: {account.status}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error conectando con Twilio: {str(e)}")
        return False

def analizar_reservas_manana():
    """Analiza las reservas para mañana que necesitarán recordatorio"""
    logger.info("🔍 Analizando reservas para mañana...")
    
    try:
        from db.supabase_client import supabase_client
        from config import RESERVAS_TABLE, DEFAULT_RESTAURANT_ID
        
        # Calcular fecha de mañana en Argentina
        ahora_argentina = datetime.now(ARGENTINA_TZ)
        manana_argentina = ahora_argentina + timedelta(days=1)
        fecha_manana = manana_argentina.strftime('%Y-%m-%d')
        
        logger.info(f"📅 Fecha actual Argentina: {ahora_argentina.strftime('%d/%m/%Y %H:%M:%S %Z')}")
        logger.info(f"📅 Fecha de mañana: {manana_argentina.strftime('%d/%m/%Y')} ({fecha_manana})")
        
        # Consultar reservas para mañana
        query = supabase_client.table(RESERVAS_TABLE)\
            .select('id,nombre_cliente,telefono,hora,estado,recordatorio_enviado')\
            .eq('fecha', fecha_manana)
        
        # Filtrar por restaurante si está configurado
        if DEFAULT_RESTAURANT_ID:
            query = query.eq('restaurante_id', DEFAULT_RESTAURANT_ID)
        
        response = query.execute()
        
        if not response.data:
            logger.info("ℹ️  No hay reservas para mañana")
            return {
                'total': 0,
                'pendientes_recordatorio': 0,
                'activas': 0,
                'problemas': []
            }
        
        reservas = response.data
        total_reservas = len(reservas)
        
        # Analizar reservas
        pendientes_recordatorio = 0
        activas = 0
        problemas = []
        
        logger.info(f"📊 Total reservas para mañana: {total_reservas}")
        
        for reserva in reservas:
            reserva_id = reserva.get('id')
            nombre = reserva.get('nombre_cliente', 'Sin nombre')
            telefono = reserva.get('telefono', 'Sin teléfono')
            hora = reserva.get('hora', 'Sin hora')
            estado = reserva.get('estado', 'Sin estado').lower()
            recordatorio_enviado = reserva.get('recordatorio_enviado', False)
            
            # Verificar si está activa
            if estado not in ['cancelada', 'no asistió', 'cancelado']:
                activas += 1
                
                # Verificar si necesita recordatorio
                if not recordatorio_enviado:
                    pendientes_recordatorio += 1
                    logger.info(f"   📋 ID {reserva_id}: {nombre} - {hora} - Teléfono: {telefono}")
                    
                    # Verificar problemas potenciales
                    if not telefono or telefono == 'Sin teléfono':
                        problemas.append(f"Reserva {reserva_id} ({nombre}) sin teléfono")
                    
                    if not nombre or nombre == 'Sin nombre':
                        problemas.append(f"Reserva {reserva_id} sin nombre")
                        
                else:
                    logger.info(f"   ✅ ID {reserva_id}: {nombre} - Ya tiene recordatorio enviado")
            else:
                logger.info(f"   ⏭️  ID {reserva_id}: {nombre} - Estado: {estado} (omitida)")
        
        # Resumen
        logger.info(f"\n📊 RESUMEN:")
        logger.info(f"   Total reservas: {total_reservas}")
        logger.info(f"   Reservas activas: {activas}")
        logger.info(f"   Pendientes de recordatorio: {pendientes_recordatorio}")
        
        if problemas:
            logger.warning(f"   ⚠️  Problemas detectados: {len(problemas)}")
            for problema in problemas:
                logger.warning(f"      - {problema}")
        else:
            logger.info(f"   ✅ No se detectaron problemas")
        
        return {
            'total': total_reservas,
            'pendientes_recordatorio': pendientes_recordatorio,
            'activas': activas,
            'problemas': problemas
        }
        
    except Exception as e:
        logger.error(f"❌ Error analizando reservas: {str(e)}")
        return {
            'total': 0,
            'pendientes_recordatorio': 0,
            'activas': 0,
            'problemas': [f"Error de sistema: {str(e)}"]
        }

def generar_reporte_estado():
    """Genera un reporte del estado del sistema"""
    logger.info("📋 Generando reporte de estado del sistema...")
    
    ahora_argentina = datetime.now(ARGENTINA_TZ)
    
    reporte = {
        'timestamp': ahora_argentina.isoformat(),
        'fecha_check': ahora_argentina.strftime('%d/%m/%Y %H:%M:%S %Z'),
        'variables_entorno_ok': False,
        'supabase_ok': False,
        'twilio_ok': False,
        'reservas_info': {},
        'alertas': [],
        'estado_general': 'ERROR'
    }
    
    # Verificaciones
    reporte['variables_entorno_ok'] = verificar_variables_entorno()
    reporte['supabase_ok'] = verificar_conexion_supabase()
    reporte['twilio_ok'] = verificar_conexion_twilio()
    reporte['reservas_info'] = analizar_reservas_manana()
    
    # Generar alertas
    if not reporte['variables_entorno_ok']:
        reporte['alertas'].append("Variables de entorno faltantes")
    
    if not reporte['supabase_ok']:
        reporte['alertas'].append("Error de conexión con Supabase")
    
    if not reporte['twilio_ok']:
        reporte['alertas'].append("Error de conexión con Twilio")
    
    if reporte['reservas_info'].get('problemas'):
        reporte['alertas'].extend(reporte['reservas_info']['problemas'])
    
    # Determinar estado general
    if all([reporte['variables_entorno_ok'], reporte['supabase_ok'], reporte['twilio_ok']]):
        if not reporte['alertas']:
            reporte['estado_general'] = 'OK'
        else:
            reporte['estado_general'] = 'WARNING'
    else:
        reporte['estado_general'] = 'ERROR'
    
    return reporte

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("🔍 VERIFICACIÓN DIARIA DEL SISTEMA DE RECORDATORIOS")
    logger.info("=" * 60)
    
    ahora_argentina = datetime.now(ARGENTINA_TZ)
    logger.info(f"📅 Fecha y hora: {ahora_argentina.strftime('%d/%m/%Y %H:%M:%S %Z')}")
    
    # Generar reporte completo
    reporte = generar_reporte_estado()
    
    # Mostrar resumen final
    logger.info("\n" + "=" * 40)
    logger.info("📋 RESUMEN FINAL")
    logger.info("=" * 40)
    logger.info(f"🎯 Estado general: {reporte['estado_general']}")
    logger.info(f"📊 Reservas para mañana: {reporte['reservas_info'].get('pendientes_recordatorio', 0)}")
    
    if reporte['alertas']:
        logger.warning(f"⚠️  Alertas encontradas ({len(reporte['alertas'])}):")
        for alerta in reporte['alertas']:
            logger.warning(f"   - {alerta}")
    else:
        logger.info("✅ Sistema listo para envío de recordatorios")
    
    # Guardar reporte en archivo
    try:
        import json
        reporte_file = os.path.join(log_dir, f"system_check_{ahora_argentina.strftime('%Y%m%d')}.json")
        with open(reporte_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 Reporte guardado en: {reporte_file}")
    except Exception as e:
        logger.warning(f"⚠️  No se pudo guardar reporte: {str(e)}")
    
    # Determinar código de salida
    if reporte['estado_general'] == 'ERROR':
        logger.error("❌ Sistema no está listo - Se requiere intervención")
        sys.exit(1)
    elif reporte['estado_general'] == 'WARNING':
        logger.warning("⚠️  Sistema funcional pero con alertas")
        sys.exit(0)  # No fallar el cron por warnings
    else:
        logger.info("✅ Sistema completamente operativo")
        sys.exit(0)

if __name__ == "__main__":
    main()
