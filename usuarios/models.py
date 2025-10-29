from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import datetime, timezone
from common.models import BaseModel

from usuarios.manager import UserManager

# Jeronimo Rodriguez 10/28/2025 

# Create your models here.
class Usuario(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Modelo base de Usuario del sistema.
    Extiende AbstractBaseUser para autenticación personalizada.
    """
    
    ESTADOS = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
    ]
    
    # Campos básicos
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    email = models.EmailField('Correo electrónico', unique=True)
    username = models.CharField(
        'Nombre de usuario',
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='El nombre de usuario solo puede contener letras, números y @/./+/-/_'
        )]
    )
    password = models.CharField(max_length=255)
    
    # Estado y control
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='activo')
    is_staff = models.BooleanField('Es staff', default=False)
    is_active = models.BooleanField('Está activo', default=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido']
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.username})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"
    

class UsuarioPendiente(BaseModel):
    """
    Modelo que almacena los usuarios que aún no han sido verificados en el sistema.
    """
    email = models.EmailField('Correo electrónico', unique=True)
    password = models.CharField('Contraseña', max_length=255)
    verification_code = models.CharField('Código de verificación', max_length=255)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)

    def es_codigo_valido(self) -> bool:
        """
        Verifica si el código de verificación sigue siendo válido.
        La duración de validez es de 20 minutos desde su creación.
        """
        duracion_validez_segundos = 20 * 60  # 20 minutos
        ahora = datetime.now(timezone.utc)

        diferencia_tiempo = (ahora - self.fecha_creacion).total_seconds()

        return diferencia_tiempo <= duracion_validez_segundos
    
    class Meta:
        db_table = 'usuarios_pendientes'
        verbose_name = 'Usuario Pendiente'
        verbose_name_plural = 'Usuarios Pendientes'

    def __str__(self):
        return f"Pendiente: {self.email}"