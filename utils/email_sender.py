import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configuración de email - debería estar en variables de entorno en producción
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'info@gandolforesto.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'info@gandolforesto.com')
RESTAURANT_NAME = os.environ.get('RESTAURANT_NAME', 'Gandolfo Restó')
RESTAURANT_PHONE = os.environ.get('RESTAURANT_PHONE', '116-6668-6255')
RESTAURANT_ADDRESS = os.environ.get('RESTAURANT_ADDRESS', 'Islandia 2397, Ingeniero Maschwitz')

# This should be importing and using the enviar_correo_confirmacion function
from services.email_service import enviar_correo_confirmacion

def send_reservation_email(reserva):
    """
    Wrapper function to send reservation confirmation email
    """
    # If reserva is an object, convert it to a dictionary
    if hasattr(reserva, 'to_dict'):
        reserva_dict = reserva.to_dict()
    else:
        reserva_dict = reserva
        
    # Call the actual email sending function
    return enviar_correo_confirmacion(reserva_dict)
    """Envía un email de confirmación de reserva al cliente"""
    if not SMTP_PASSWORD:
        logger.warning("SMTP_PASSWORD no configurado. No se enviará el email de confirmación.")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = f"{RESTAURANT_NAME} <{SENDER_EMAIL}>"
        msg['To'] = reserva.email
        msg['Subject'] = f"Confirmación de Reserva - {RESTAURANT_NAME}"
        
        # Formatear fecha para mostrar
        fecha_obj = datetime.strptime(reserva.fecha, '%Y-%m-%d')
        fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        
        # Cuerpo del mensaje
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #5c652a; text-align: center;">¡Tu reserva ha sido confirmada!</h2>
                
                <p>Hola <strong>{reserva.nombre}</strong>,</p>
                
                <p>Gracias por elegir {RESTAURANT_NAME}. Hemos registrado tu reserva con los siguientes detalles:</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Fecha:</strong> {fecha_formateada}</p>
                    <p><strong>Hora:</strong> {reserva.hora} hs</p>
                    <p><strong>Personas:</strong> {reserva.personas}</p>
                    <p><strong>Número de contacto:</strong> {reserva.telefono}</p>
                </div>
                
                <p>Si necesitas modificar o cancelar tu reserva, por favor contáctanos al {RESTAURANT_PHONE}.</p>
                
                <p>Dirección: {RESTAURANT_ADDRESS}</p>
                
                <p style="text-align: center; margin-top: 30px;">¡Esperamos recibirte pronto!</p>
                
                <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; font-size: 12px;">
                    <p>Este es un mensaje automático, por favor no respondas a este correo.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Conectar al servidor SMTP y enviar
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email de confirmación enviado a {reserva.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar email de confirmación: {str(e)}")
        return False