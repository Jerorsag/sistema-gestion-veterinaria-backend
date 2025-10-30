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

    def es_codigo_valido(self) -> bool:
        """
        Verifica si el código de verificación sigue siendo válido.
        La duración de validez es de 20 minutos desde su creación.
        """
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
    
    
# Jeronimo Rodriguez 10/30/2025
# Creacion de Modelos-Tablas Rol-UsuarioRol   
class Rol(models.Model):
    """Modelo de roles del sistema."""
    
    ROLES_DISPONIBLES = [
        ('administrador', 'Administrador'),
        ('veterinario', 'Veterinario'),
        ('practicante', 'Practicante'),
        ('recepcionista', 'Recepcionista'),
        ('cliente', 'Cliente'),
    ]
    
    nombre = models.CharField(
        'Nombre del rol',
        max_length=50,
        choices=ROLES_DISPONIBLES,
        unique=True
    )
    descripcion = models.TextField('Descripción', blank=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.get_nombre_display()
    

class UsuarioRol(models.Model):
    """Tabla intermedia para la relación muchos a muchos entre Usuario y Rol."""
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='usuario_roles'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='rol_usuarios'
    )
    
    class Meta:
        db_table = 'usuario_roles'
        verbose_name = 'Usuario-Rol'
        verbose_name_plural = 'Usuarios-Roles'
        unique_together = ['usuario', 'rol']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.rol.nombre}"
    
# Jeronimo Rodriguez 10/30/2025
# Creacion de Modelo Veterinario
class Veterinario(models.Model):
    """Perfil extendido para usuarios veterinarios."""
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='perfil_veterinario'
    )
    licencia = models.CharField('Número de licencia', max_length=50, unique=True)
    especialidad = models.CharField('Especialidad', max_length=100, blank=True)
    horario = models.TextField('Horario de atención', blank=True)
    
    class Meta:
        db_table = 'veterinarios'
        verbose_name = 'Veterinario'
        verbose_name_plural = 'Veterinarios'
    
    def __str__(self):
        return f"Dr(a). {self.usuario.get_full_name()}"


class Practicante(models.Model):
    """Perfil extendido para usuarios practicantes."""
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='perfil_practicante'
    )
    tutor_veterinario = models.ForeignKey(
        Veterinario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='practicantes'
    )
    universidad = models.CharField('Universidad', max_length=200, blank=True)
    periodo_practica = models.CharField('Período de práctica', max_length=100, blank=True)
    
    class Meta:
        db_table = 'practicantes'
        verbose_name = 'Practicante'
        verbose_name_plural = 'Practicantes'
    
    def __str__(self):
        return f"Practicante {self.usuario.get_full_name()}"
    
class Cliente(models.Model):
    """Perfil extendido para usuarios clientes (propietarios de mascotas)."""
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='perfil_cliente'
    )
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    direccion = models.TextField('Dirección', blank=True)
    
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return self.usuario.get_full_name()