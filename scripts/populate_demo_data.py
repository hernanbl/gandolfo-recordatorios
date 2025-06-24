#!/usr/bin/env python
"""
Script para poblar la tabla 'reservas' con datos de muestra para el restaurante de demostración.
Esto crea reservas de ejemplo que permiten visualizar todas las funcionalidades del dashboard.
"""
import sys
import os
import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Configurar path para importar desde el directorio principal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar las dependencias necesarias del sistema
from config import DEMO_RESTAURANT_ID, DEMO_RESTAURANT_NAME
from db.supabase_client import supabase_client

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('demo_data')

# Lista de nombres para generar datos aleatorios
NOMBRES = [
    "Juan Pérez", "María García", "Carlos López", "Ana Martínez", "Luis Rodríguez", 
    "Laura González", "Roberto Sánchez", "Sofía Fernández", "Diego Torres", "Valentina Ramírez",
    "Javier Flores", "Camila Díaz", "Pablo Herrera", "Lucía Castro", "Miguel Ortiz",
    "Isabella Vargas", "Andrés Rojas", "Gabriela Morales", "Alejandro Silva", "Natalia Romero"
]

# Números de teléfono de ejemplo
TELEFONOS = [
    "+549115551234", "+549115552345", "+549115553456", "+549115554567", "+549115555678",
    "+549115556789", "+549115557890", "+549115558901", "+549115559012", "+549115550123",
    "+5491155551234", "+5491155552345", "+5491155553456", "+5491155554567", "+5491155555678",
    "+5491155556789", "+5491155557890", "+5491155558901", "+5491155559012", "+5491155550123"
]

# Emails de ejemplo basados en los nombres
def generar_email(nombre):
    partes = nombre.lower().split(' ')
    return f"{partes[0]}.{partes[1]}@ejemplo.com"

# Estados posibles para las reservas
ESTADOS = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
# Pesos para distribuir los estados (mayoría confirmadas, menos cancelaciones/no shows)
ESTADOS_PESOS = [15, 60, 15, 10]

# Orígenes posibles de las reservas
ORIGENES = ["web", "whatsapp", "teléfono", "presencial"]
ORIGENES_PESOS = [40, 30, 20, 10]  # mayoría vía web y WhatsApp

# ID específico para identificar las reservas creadas por este script de demo
# Esto es crucial si alguna vez necesitamos limpiarlas manualmente de forma segura.
# Sin embargo, este script NO las borrará automáticamente.
DEMO_SCRIPT_MARKER_COMMENT = "Generado por script populate_demo_data.py"

def crear_reserva_aleatoria(fecha_base):
    """
    Crea una reserva con datos aleatorios para una fecha específica
    
    Args:
        fecha_base: fecha base para la reserva (datetime)
        
    Returns:
        dict: datos de la reserva
    """
    # Desviación aleatoria entre -3 y +7 días desde la fecha base
    desviacion_dias = random.randint(-3, 7)
    fecha_reserva = fecha_base + timedelta(days=desviacion_dias)
    
    # No crear reservas para fechas pasadas a más de 60 días o futuras a más de 21 días
    hoy = datetime.now()
    if (hoy - fecha_reserva).days > 60 or (fecha_reserva - hoy).days > 21:
        fecha_reserva = hoy + timedelta(days=random.randint(-3, 7))
    
    # Generar hora aleatoria (franjas típicas de restaurante)
    if random.random() < 0.4:  # 40% para almuerzo
        hora = f"{random.randint(12, 14)}:{random.choice(['00', '15', '30', '45'])}"
    else:  # 60% para cena
        hora = f"{random.randint(19, 22)}:{random.choice(['00', '15', '30', '45'])}"
    
    # Generar cantidad de personas (grupos pequeños más comunes)
    personas_pesos = [0, 25, 30, 20, 15, 5, 3, 2]  # Pesos para 1-8 personas
    personas = random.choices(range(1, 9), weights=personas_pesos)[0]
    
    # Seleccionar nombre y generar email
    nombre = random.choice(NOMBRES)
    email = generar_email(nombre)
    
    # Definir el estado con base en los pesos (más confirmadas que otros estados)
    estado = random.choices(ESTADOS, weights=ESTADOS_PESOS)[0]
    
    # Añadir comentarios al 30% de las reservas
    comentarios_script = DEMO_SCRIPT_MARKER_COMMENT # Marcador por defecto
    if random.random() < 0.3:
        comentarios_opciones = [
            "Mesa cerca de la ventana por favor",
            "Celebramos un cumpleaños",
            "Necesitamos una silla alta para bebé",
            "Preferimos mesa alejada del ruido",
            "Uno de los comensales usa silla de ruedas",
            "Somos celíacos, consultaremos opciones",
            "Es nuestro aniversario",
            "Llegaremos 15min tarde"
        ]
        comentarios_script = f"{random.choice(comentarios_opciones)} ({DEMO_SCRIPT_MARKER_COMMENT})"
    
    # Generar fecha de creación (entre 1 y 10 días antes de la fecha de reserva)
    dias_antes = random.randint(1, 10)
    fecha_creacion = fecha_reserva - timedelta(days=dias_antes)
    
    # Formato ISO para la fecha
    fecha_iso = fecha_reserva.date().isoformat()
    
    # El origen varía según pesos definidos
    origen = random.choices(ORIGENES, weights=ORIGENES_PESOS)[0]
    
    return {
        'id': str(uuid4()),
        'nombre_cliente': nombre,
        'fecha_reserva': fecha_iso,
        'hora_reserva': hora,
        'cantidad_personas': personas,
        'telefono_cliente': random.choice(TELEFONOS),
        'email_cliente': email,
        'comentarios': comentarios_script, # Usamos el comentario con el marcador
        'estado': estado,
        'origen': origen,
        'fecha_creacion': fecha_creacion.isoformat()
    }

def poblar_datos_demo():
    """
    Crea y AÑADE reservas de ejemplo para el restaurante de demostración.
    NO BORRA NINGUNA RESERVA EXISTENTE.
    """
    try:
        # Verificar conexión a Supabase
        if not supabase_client:
            logger.error("No se pudo conectar a Supabase. Verifique las credenciales.")
            return False
        
        logger.info(f"Creando datos de muestra para el restaurante de demostración: {DEMO_RESTAURANT_NAME} ({DEMO_RESTAURANT_ID})")
        
        # Fecha base (hoy)
        hoy = datetime.now()
        
        # Generar reservas para los últimos 3 meses (distribución no uniforme)
        reservas_a_crear = []
        
        # Distribución por mes (más reservas para el mes actual)
        meses = [2, 1, 0]  # Hace 2 meses, hace 1 mes, mes actual
        reservas_por_mes = [10, 15, 20]  # Cantidad reducida para no sobrecargar en cada ejecución
        
        for i, mes in enumerate(meses):
            fecha_base = hoy - timedelta(days=30 * mes)
            cantidad = reservas_por_mes[i]
            
            logger.info(f"Generando {cantidad} reservas para el mes {'actual' if mes == 0 else f'(hace {mes} meses)'}")
            
            for _ in range(cantidad):
                reserva = crear_reserva_aleatoria(fecha_base)
                reservas_a_crear.append(reserva)
        
        # YA NO SE ELIMINAN RESERVAS EXISTENTES
        logger.info("Este script NO elimina reservas existentes. Solo añade nuevas reservas de demostración.")
        
        # Insertar las nuevas reservas
        logger.info(f"Insertando {len(reservas_a_crear)} nuevas reservas de muestra en la base de datos...")
        
        # Insertar en lotes para evitar problemas con la API
        BATCH_SIZE = 20
        for i in range(0, len(reservas_a_crear), BATCH_SIZE):
            batch = reservas_a_crear[i:i+BATCH_SIZE]
            response = supabase_client.table('reservas').insert(batch).execute()
            logger.info(f"Lote insertado: {i//BATCH_SIZE + 1}/{(len(reservas_a_crear) + BATCH_SIZE - 1) // BATCH_SIZE}")
        
        logger.info(f"¡Datos de demostración creados con éxito! ({len(reservas_a_crear)} reservas)")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear datos de demostración: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Iniciando script para poblar datos de demostración...")
    resultado = poblar_datos_demo()
    if resultado:
        logger.info("Proceso completado con éxito.")
    else:
        logger.info("El proceso encontró errores. Revise los logs para más detalles.")
        sys.exit(1)
