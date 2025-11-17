from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

from common.models import BaseModel


class ResetPasswordToken(BaseModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    usado = models.BooleanField(default=False)

    class Meta:
        db_table = 'reset_password_tokens'
        verbose_name = 'Reset Password Token'
        verbose_name_plural = 'Reset Password Tokens'

    def __str__(self):
        return f"ResetToken({self.usuario}, used={self.usado})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)

    @classmethod
    def create_for_user(cls, usuario, minutes: int = 60):
        token = cls.generate_token()
        expires = timezone.now() + timedelta(minutes=minutes)
        return cls.objects.create(usuario=usuario, token=token, expires_at=expires)
