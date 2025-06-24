"""
Paquete de servicios para gestión de reservas
"""

# Importar las funciones principales para que estén disponibles directamente desde el paquete
from .core import registrar_reserva, registrar_reserva_whatsapp
from .validacion import validar_reserva, validar_paso_reserva
from .db import (
    obtener_reservas, obtener_reservas_proximas, actualizar_reserva,
    buscar_reserva_por_telefono, actualizar_estado_reserva, marcar_recordatorio_enviado
)

# Exportar todas las funciones para mantener compatibilidad con el código existente
__all__ = [
    'registrar_reserva', 'registrar_reserva_whatsapp',
    'validar_reserva', 'validar_paso_reserva',
    'obtener_reservas', 'obtener_reservas_proximas', 'actualizar_reserva',
    'buscar_reserva_por_telefono', 'actualizar_estado_reserva', 'marcar_recordatorio_enviado'
]