# This file makes the 'twilio' directory a Python package
# It allows importing modules from this directory
from services.twilio.messaging import send_whatsapp_message

from services.twilio.utils import es_consulta_relevante, get_or_create_session
from services.twilio.reminder_handler import handle_reminder_response

# Export the main functions
__all__ = [
    'send_whatsapp_message',
    'handle_whatsapp_message',
    'es_consulta_relevante',
    'get_or_create_session',
    'handle_reminder_response'
]