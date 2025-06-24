import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import logging
from typing import Optional, Dict, Any
import socket
from contextlib import contextmanager
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_USE_TLS

logger = logging.getLogger(__name__)

class EmailServiceError(Exception):
    """Base exception class for email service errors."""
    pass

class SMTPConnectionError(EmailServiceError):
    """Raised when there's an error connecting to the SMTP server."""
    pass

class EmailSendError(EmailServiceError):
    """Raised when there's an error sending the email."""
    pass

@contextmanager
def smtp_connection(host: str, port: int, username: str, password: str, use_tls: bool = True, timeout: int = 30):
    """Context manager for handling SMTP connections with proper error handling and timeouts."""
    smtp = None
    try:
        logger.info(f"Iniciando conexión SMTP a {host}:{port}")
        
        # Create a custom SSL context with modern security settings
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Set socket timeout
        socket.setdefaulttimeout(timeout)
        
        if use_tls:
            smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=timeout)
        else:
            smtp = smtplib.SMTP(host, port, timeout=timeout)
            smtp.starttls(context=context)
        
        logger.info("Conexión SMTP establecida, intentando login")
        smtp.login(username, password)
        logger.info("Login SMTP exitoso")
        
        yield smtp
        
    except (socket.timeout, TimeoutError) as e:
        logger.error(f"Timeout al conectar con servidor SMTP: {str(e)}")
        raise SMTPConnectionError(f"Timeout al conectar con servidor SMTP: {str(e)}")
    except ssl.SSLError as e:
        logger.error(f"Error SSL al conectar con servidor SMTP: {str(e)}")
        raise SMTPConnectionError(f"Error SSL al conectar con servidor SMTP: {str(e)}")
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {str(e)}")
        raise EmailSendError(f"Error SMTP: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en el servicio de email: {str(e)}")
        raise EmailServiceError(f"Error inesperado en el servicio de email: {str(e)}")
    finally:
        if smtp:
            try:
                smtp.quit()
                logger.info("Conexión SMTP cerrada correctamente")
            except Exception as e:
                logger.warning(f"Error al cerrar conexión SMTP: {str(e)}")

def send_email(
    sender_user: str,
    sender_password: str,
    recipient_email: str,
    subject: str,
    template_html: str,
    template_data: Dict[str, Any],
    smtp_config: Dict[str, Any]
) -> bool:
    """
    Send an email using the specified SMTP configuration and templates.
    
    Args:
        sender_user: SMTP username
        sender_password: SMTP password
        recipient_email: Recipient's email address
        subject: Email subject
        template_html: HTML template string
        template_data: Data to format the template with
        smtp_config: SMTP server configuration
        
    Returns:
        bool: True if email was sent successfully
        
    Raises:
        EmailServiceError: If there's any error during the process
    """
    try:
        logger.info(f"Preparando envío de email a {recipient_email}")
        
        # Format the template
        try:
            formatted_html = template_html.format(**template_data)
        except KeyError as e:
            logger.error(f"Error al formatear template: falta la clave {str(e)}")
            raise EmailServiceError(f"Error al formatear template: falta la clave {str(e)}")
        except Exception as e:
            logger.error(f"Error al formatear template: {str(e)}")
            raise EmailServiceError(f"Error al formatear template: {str(e)}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_user
        msg['To'] = recipient_email
        msg['Date'] = formatdate()
        
        html_part = MIMEText(formatted_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email using context manager
        with smtp_connection(
            host=smtp_config['host'],
            port=smtp_config['port'],
            username=sender_user,
            password=sender_password,
            use_tls=smtp_config.get('use_tls', True),
            timeout=smtp_config.get('timeout', 30)
        ) as smtp:
            smtp.send_message(msg)
            logger.info(f"Email enviado exitosamente a {recipient_email}")
            return True
            
    except (SMTPConnectionError, EmailSendError) as e:
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        logger.error(f"Error inesperado al enviar email: {str(e)}")
        raise EmailServiceError(f"Error inesperado al enviar email: {str(e)}")

def _get_nested_value(data_dict, keys, default=None):
    """Helper para obtener valores anidados de forma segura."""
    if not isinstance(data_dict, dict):
        return default
    
    current = data_dict
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current

def enviar_correo_confirmacion(reserva_details, recipient_email, restaurant_config):
    """
    Envía un correo de confirmación de reserva, adaptado al restaurante específico.
    """
    try:
        logger.info(f"Iniciando envío de correo a {recipient_email}")
        logger.info(f"Configuración SMTP: HOST={EMAIL_HOST}, PORT={EMAIL_PORT}, USE_TLS={EMAIL_USE_TLS}")
        
        info_json = _get_nested_value(restaurant_config, ['info_json'], {})
        contact = _get_nested_value(info_json, ['contact'], {})
        restaurant_name = _get_nested_value(restaurant_config, ['nombre'], 'Restaurante')
        restaurant_address_display = contact.get('address', '')
        restaurant_phone_display = contact.get('phone', '')
        restaurant_contact_email_display = contact.get('email', '')
        restaurant_logo_url = restaurant_config.get('logo_url', '')
        
        # Get email sender credentials and log their presence
        email_credentials = _get_nested_value(info_json, ['email_sending'], {})
        sender_user = email_credentials.get('user', EMAIL_USER)
        sender_password = email_credentials.get('password', EMAIL_PASSWORD)
        
        logger.info(f"Credenciales de email - user: {sender_user}, password: {'*' * (len(sender_password) if sender_password else 0)}")

        if not sender_user or not sender_password:
            logger.error("Faltan credenciales de email - user present: %s, password present: %s", 
                        bool(sender_user), bool(sender_password))
            return False
            
        # Log email template configuration
        logger.info(f"Configurando plantilla de email para {restaurant_name}")
        logger.info(f"Datos de la reserva: fecha={reserva_details.get('fecha')}, hora={reserva_details.get('hora')}")

        # HTML template simple y limpio
        html_template = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ 
                        font-family: Arial, Helvetica, sans-serif;
                        margin: 0;
                        padding: 20px;
                        color: #333333;
                        line-height: 1.6;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                    }}
                    h1 {{
                        color: #2C5530;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }}
                    .details {{
                        margin: 20px 0;
                    }}
                    .details ul {{
                        list-style: disc;
                        padding-left: 20px;
                        margin: 10px 0;
                    }}
                    .details li {{
                        margin-bottom: 5px;
                    }}
                    .contact-info {{
                        margin-top: 30px;
                        padding-top: 20px;
                    }}
                    .logo {{
                        margin: 30px 0;
                        text-align: center;
                    }}
                    .logo img {{
                        max-width: 150px;
                        height: auto;
                    }}
                    .signature {{
                        margin-top: 30px;
                        border-top: 1px solid #eee;
                        padding-top: 20px;
                        font-size: 14px;
                        color: #666;
                    }}
                    a {{
                        color: #2C5530;
                        text-decoration: none;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>¡Gracias por tu reserva en {restaurant_name}!</h1>
                    
                    <p>Hemos confirmado tu reserva con los siguientes detalles:</p>
                    
                    <div class="details">
                        <ul>
                            <li><strong>Nombre:</strong> {nombre}</li>
                            <li><strong>Fecha:</strong> {fecha}</li>
                            <li><strong>Hora:</strong> {hora}</li>
                            <li><strong>Personas:</strong> {personas}</li>
                            <li><strong>Teléfono:</strong> {telefono}</li>
                            <li><strong>Email:</strong> {email}</li>
                            {comentarios_html}
                        </ul>
                    </div>
                    
                    <p>Si necesitas modificar o cancelar tu reserva, por favor contáctanos al {restaurant_phone_display}.</p>
                    
                    <p>¡Esperamos recibirte pronto!</p>
                    
                    <div class="logo">
                        {logo_html}
                    </div>
                    
                    <div class="signature">
                        <p><strong>Equipo de {restaurant_name}</strong><br>
                        {restaurant_address_display}<br>
                        Tel: {restaurant_phone_display}<br>
                        Email: {restaurant_contact_email_display}<br>
                        Web: {restaurant_web_display}</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Prepare the template data
        comentarios_html = f'<li><strong>Comentarios:</strong> {reserva_details.get("comentarios")}</li>' if reserva_details.get('comentarios') else ''
        logo_html = f'<img src="{restaurant_logo_url}" alt="{restaurant_name}">' if restaurant_logo_url else f'<h2>{restaurant_name}</h2>'
        
        # Obtener información adicional de la reserva
        telefono = reserva_details.get('telefono', reserva_details.get('phone', ''))
        email = reserva_details.get('email', recipient_email)
        
        template_data = {
            'nombre': reserva_details.get('nombre', ''),
            'fecha': reserva_details.get('fecha', ''),
            'hora': reserva_details.get('hora', ''),
            'personas': reserva_details.get('personas', ''),
            'telefono': telefono,
            'email': email,
            'comentarios_html': comentarios_html,
            'logo_html': logo_html,
            'restaurant_address_display': restaurant_address_display,
            'restaurant_phone_display': restaurant_phone_display,
            'restaurant_contact_email_display': restaurant_contact_email_display,
            'restaurant_name': restaurant_name,
            'restaurant_web_display': restaurant_config.get('website', 'https://vivacom.com.ar/gandolfo')
        }
        
        smtp_config = {
            'host': EMAIL_HOST,
            'port': EMAIL_PORT,
            'use_tls': EMAIL_USE_TLS,
            'timeout': 30
        }
        
        return send_email(
            sender_user=sender_user,
            sender_password=sender_password,
            recipient_email=recipient_email,
            subject=f"Confirmación de Reserva en {restaurant_name}",
            template_html=html_template,
            template_data=template_data,
            smtp_config=smtp_config
        )
        
    except EmailServiceError as e:
        logger.error(f"Error en enviar_correo_confirmacion: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error general en enviar_correo_confirmacion: {str(e)}")
        logger.exception("Traceback completo:")
        return False

