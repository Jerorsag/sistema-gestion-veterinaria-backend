"""
UsuarioPendiente model (módulo separado bajo auth).

Este archivo contiene la clase `UsuarioPendiente` que antes vivía en
`usuarios/models/auth/usuario.py`. La separación mejora modularidad.
"""
from django.db import models
from django.utils import timezone
from common.models import BaseModel


class UsuarioPendiente(BaseModel):
    """
    Modelo que almacena los usuarios que aún no han sido verificados.

    Se utiliza durante el flujo de registro con verificación por email.
    """
    email = models.EmailField('Correo electrónico', unique=True)
    password = models.CharField('Contraseña', max_length=255)
    verification_code = models.CharField('Código de verificación', max_length=255)

    def es_codigo_valido(self) -> bool:
        """
        Verifica si el código de verificación sigue siendo válido (20 minutos).
        """
        from datetime import datetime
        duracion_validez_segundos = 20 * 60  # 20 minutos
        ahora = datetime.now(timezone.utc)
        diferencia_tiempo = (ahora - self.created_at).total_seconds()
        return diferencia_tiempo <= duracion_validez_segundos

    class Meta:
        db_table = 'usuarios_pendientes'
        verbose_name = 'Usuario Pendiente'
        verbose_name_plural = 'Usuarios Pendientes'

    def __str__(self):
        return f"Pendiente: {self.email}"
