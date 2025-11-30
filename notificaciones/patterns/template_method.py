from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from abc import ABC, abstractmethod
import threading
import os

class BaseNotification(ABC):
    """
    Clase Base Abstracta (El "Molde").
    Implementa el Patrón Template Method.
    Define el esqueleto del algoritmo ("cómo") para enviar una notificación.
    Su única responsabilidad es definir el algoritmo de envío.
    
    Optimizado para:
    - Emails críticos: Envío síncrono garantizado (verificación de cuenta)
    - Emails no críticos: Envío asíncrono para no bloquear requests
    """
    
    def __init__(self, context_data: dict, to_email: str):
        self.context_data = context_data
        self.to_email = to_email

    @abstractmethod
    def get_subject(self) -> str:
        """Método abstracto: Las subclases DEBEN definir el asunto que tendra el correo"""
        pass

    @abstractmethod
    def get_template_name(self) -> str:
        """Método abstracto: Las subclases DEBEN definir plantilla html que usara el correo."""
        pass

    def build_message_body(self) -> str:
        """Construye el cuerpo del mensaje HTML desde una plantilla."""
        template_name = self.get_template_name()
        return render_to_string(template_name, self.context_data)

    def _send_email_sync(self, subject: str, message_body: str):
        """
        Método privado que envía el correo de forma síncrona.
        Optimizado con timeouts cortos para SendGrid.
        """
        try:
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL,
                [self.to_email],
                html_message=message_body,
                fail_silently=False,
            )
            print(f"✅ Correo '{subject}' enviado a {self.to_email}")
        except Exception as e:
            error_msg = f"❌ Error enviando '{subject}' a {self.to_email}: {e}"
            print(error_msg)
            raise

    def send(self, require_success: bool = False):
        """
        El "Template Method": El algoritmo principal e invariable.
        Construye y envía el email de forma optimizada.
        
        Args:
            require_success: Si es True, envía síncrono (garantizado para emails críticos).
                           Si es False, envía asíncrono (no bloquea para emails no críticos).
        
        Estrategia:
        - Emails críticos (verificación): Síncrono para garantizar envío
        - Emails no críticos (notificaciones): Asíncrono para mejor performance
        """
        subject = self.get_subject()
        message_body = self.build_message_body()
        
        # Para emails críticos (verificación de cuenta), usar modo síncrono
        # Esto garantiza que el email se envíe antes de responder al usuario
        if require_success:
            self._send_email_sync(subject, message_body)
            return
        
        # Para emails no críticos, usar modo asíncrono (no bloquea la respuesta)
        use_async = os.getenv('USE_ASYNC_EMAIL', 'True').lower() == 'true'
        
        if use_async:
            thread = threading.Thread(
                target=self._send_email_sync,
                args=(subject, message_body),
                daemon=True,
                name=f"Email-{subject[:15]}"
            )
            thread.start()
        else:
            # Modo síncrono (solo para debugging)
            self._send_email_sync(subject, message_body)