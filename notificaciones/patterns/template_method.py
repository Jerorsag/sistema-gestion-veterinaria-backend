from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from abc import ABC, abstractmethod
import threading  # Agregar para envío asíncrono
import os

class BaseNotification(ABC):
    """
    Clase Base Abstracta (El "Molde").
    Implementa el Patrón Template Method.
    Define el esqueleto del algoritmo ("cómo") para enviar una notificación.
    Su única responsabilidad es definir el algoritmo de envío.
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
        """Método privado que envía el correo de forma síncrona."""
        try:
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL,
                [self.to_email],
                html_message=message_body,
                fail_silently=False,
            )
            print(f"✅ Correo '{subject}' enviado exitosamente a {self.to_email}")
        except Exception as e:
            # Log del error para debugging en producción
            print(f"❌ Error al enviar correo '{subject}' a {self.to_email}: {e}")
            # Re-lanzar la excepción para que se pueda manejar si es necesario
            raise

    def send(self):
        """
        El "Template Method": El algoritmo principal e invariable.
        Construye y envía el email de forma asíncrona.
        
        Nota: El envío se hace en un thread separado para no bloquear
        el worker de Gunicorn. El thread es daemon=True para que no
        impida que el proceso termine, pero en la práctica el envío
        de correo es rápido (< 10 segundos) y no debería ser un problema.
        
        Se puede desactivar el modo asíncrono con la variable de entorno
        USE_ASYNC_EMAIL=False para debugging o en caso de problemas.
        """
        subject = self.get_subject()
        message_body = self.build_message_body()
        
        # Opción de fallback: permitir modo síncrono con variable de entorno
        use_async = os.getenv('USE_ASYNC_EMAIL', 'True').lower() == 'true'
        
        if use_async:
            print(f"📧 Iniciando envío asíncrono de correo '{subject}' a {self.to_email}...")
            
            # Enviar en un thread separado para no bloquear el worker
            # daemon=True permite que el proceso termine sin esperar al thread
            # Esto es seguro porque el envío de correo normalmente toma < 10 segundos
            thread = threading.Thread(
                target=self._send_email_sync,
                args=(subject, message_body),
                daemon=True,
                name=f"EmailThread-{subject[:20]}"  # Nombre descriptivo para debugging
            )
            thread.start()
            
            # No esperamos a que termine (non-blocking)
            # El thread se ejecutará en segundo plano
        else:
            # Modo síncrono (fallback para debugging)
            print(f"📧 Enviando correo de forma síncrona '{subject}' a {self.to_email}...")
            self._send_email_sync(subject, message_body)