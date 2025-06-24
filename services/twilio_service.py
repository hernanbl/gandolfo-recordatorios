"""
Servicio de Twilio para envío de mensajes de WhatsApp
Este archivo es un wrapper para los módulos refactorizados
"""

# Import all the necessary functions from the refactored modules
from services.twilio.messaging import send_whatsapp_message
from services.twilio.reservations import (
    handle_reservation_confirmation,
    send_reservation_reminder,
    check_upcoming_reservations
)

# Re-export all the functions
__all__ = [
    'send_whatsapp_message',
    'handle_reservation_confirmation',
    'send_reservation_reminder',
    'check_upcoming_reservations'
]