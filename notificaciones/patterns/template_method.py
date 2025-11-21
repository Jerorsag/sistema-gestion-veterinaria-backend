from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from abc import ABC, abstractmethod

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

    def send(self):
        """
        El "Template Method": El algoritmo principal e invariable.
        Construye y envía el email.
        """
        subject = self.get_subject()
        message_body = self.build_message_body()

        print(f"Intentando enviar correo '{subject}' a {self.to_email}...")
        
        try:
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL,
                [self.to_email],
                html_message=message_body,
                fail_silently=False,
            )
            print(f"Correo '{subject}' enviado exitosamente a {self.to_email}")
        except Exception as e:
            print(f"Error al enviar correo: {e}")