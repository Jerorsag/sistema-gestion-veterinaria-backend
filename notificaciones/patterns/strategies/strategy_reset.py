from ..template_method import BaseNotification


class ResetPasswordEmail(BaseNotification):
    def get_subject(self) -> str:
        return "Restablece tu contraseña"

    def get_template_name(self) -> str:
        return "emails/reset_password.html"
