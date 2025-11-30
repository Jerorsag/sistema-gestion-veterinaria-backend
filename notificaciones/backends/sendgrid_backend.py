"""
Backend personalizado de Django para usar SendGrid API REST en lugar de SMTP.
Soluciona problemas de timeout y bloqueo de conexiones SMTP en Render.
"""
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
import logging
import os

logger = logging.getLogger(__name__)

class SendGridBackend(BaseEmailBackend):
    """
    Backend de email usando SendGrid API REST.
    Más confiable que SMTP y no bloqueado por Render.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        
        # Intentar obtener el API Key de múltiples fuentes
        self.api_key = (
            getattr(settings, 'SENDGRID_API_KEY', None) or 
            getattr(settings, 'EMAIL_HOST_PASSWORD', None) or
            os.getenv('SENDGRID_API_KEY') or
            os.getenv('EMAIL_HOST_PASSWORD')
        )
        
        # Limpiar el API Key (eliminar espacios)
        if self.api_key:
            self.api_key = self.api_key.strip()
        
        # Log para debugging (sin mostrar el API Key completo)
        if self.api_key:
            api_key_preview = self.api_key[:10] + "..." + self.api_key[-5:] if len(self.api_key) > 15 else "***"
            logger.info(f"📧 SendGrid API Key configurado: {api_key_preview}")
            logger.info(f"📧 Longitud del API Key: {len(self.api_key)} caracteres")
            logger.info(f"📧 API Key empieza con: {self.api_key[:3] if len(self.api_key) >= 3 else 'N/A'}")
        else:
            logger.error("❌ SENDGRID_API_KEY no está configurado")
        
        if not self.api_key:
            raise ValueError(
                'SENDGRID_API_KEY o EMAIL_HOST_PASSWORD debe estar configurado '
                'para usar SendGridBackend. Verifica las variables de entorno en Render.'
            )
        
        # Verificar que el API Key tenga el formato correcto (debe empezar con SG.)
        if not self.api_key.startswith('SG.'):
            logger.warning(f"⚠️ El API Key no parece tener el formato correcto (debe empezar con 'SG.')")
            logger.warning(f"⚠️ Primeros caracteres: {self.api_key[:10]}")
        
        self.client = SendGridAPIClient(self.api_key)
    
    def send_messages(self, email_messages):
        """
        Envía uno o más mensajes de email usando SendGrid API.
        """
        if not email_messages:
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                # Extraer información del mensaje
                from_email_raw = message.from_email
                to_emails = message.to
                subject = message.subject
                
                # Parsear from_email si viene en formato "Nombre <email@example.com>"
                if '<' in from_email_raw and '>' in from_email_raw:
                    # Formato: "Nombre <email@example.com>"
                    import re
                    match = re.match(r'(.+?)\s*<(.+?)>', from_email_raw)
                    if match:
                        from_name = match.group(1).strip()
                        from_email = match.group(2).strip()
                        from_email_obj = Email(from_email, from_name)
                    else:
                        from_email_obj = from_email_raw
                else:
                    # Solo email
                    from_email_obj = from_email_raw
                
                # Obtener el contenido HTML o texto
                if hasattr(message, 'alternatives') and message.alternatives:
                    # Si hay HTML, usar el HTML
                    html_content = message.alternatives[0][0]
                    text_content = message.body
                else:
                    # Solo texto
                    text_content = message.body
                    html_content = None
                
                # Crear el objeto Mail de SendGrid
                mail = Mail(
                    from_email=from_email_obj,
                    to_emails=to_emails,
                    subject=subject,
                    plain_text_content=text_content,
                    html_content=html_content
                )
                
                # Enviar el email
                response = self.client.send(mail)
                
                # Verificar respuesta
                if response.status_code in [200, 201, 202]:
                    num_sent += 1
                    logger.info(f"✅ Email enviado exitosamente a {to_emails} via SendGrid API")
                else:
                    error_msg = f"❌ Error enviando email: Status {response.status_code}, Body: {response.body}"
                    logger.error(error_msg)
                    if not self.fail_silently:
                        raise Exception(error_msg)
                        
            except Exception as e:
                error_msg = f"❌ Error enviando email via SendGrid API: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # Si es error 401, dar información más específica
                if '401' in str(e) or 'Unauthorized' in str(e):
                    api_key_preview = self.api_key[:10] + "..." + self.api_key[-5:] if len(self.api_key) > 15 else "***"
                    logger.error(f"❌ Error 401: El API Key puede ser incorrecto o no tener permisos")
                    logger.error(f"❌ API Key usado: {api_key_preview}")
                    logger.error(f"❌ Verifica que SENDGRID_API_KEY en Render Dashboard sea correcto")
                    logger.error(f"❌ Verifica que el API Key tenga permisos 'Mail Send' en SendGrid")
                
                if not self.fail_silently:
                    raise
        
        return num_sent

