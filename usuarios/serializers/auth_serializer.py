from rest_framework import serializers
from django.utils import timezone
from usuarios.models import Usuario, Rol, UsuarioRol, Cliente
from usuarios.serializers.user_serializer import ClienteSerializer, VeterinarioSerializer, PracticanteSerializer 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

# Jeronimo Rodriguez 10/31/2025 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para la autenticación JWT.

    Este serializer amplía el comportamiento de `TokenObtainPairSerializer` 
    de SimpleJWT para incluir validaciones de seguridad adicionales y 
    proporcionar información personalizada del usuario dentro del token.
    
    - Extiende la funcionalidad del TokenObtainPairSerializer base de SimpleJWT.
    - Valida que el usuario esté activo y en estado 'activo' dentro del sistema.
    - Implementa control de seguridad ante múltiples intentos fallidos.
    - Incluye información adicional del usuario dentro del token (claims)
      y en la respuesta del login.
    """
    
    def validate(self, attrs):
        """
        Valida las credenciales del usuario y genera los tokens JWT.

        Flujo del proceso:
        1. Verifica si el usuario existe.
        2. Comprueba si está bloqueado temporalmente.
        3. Intenta autenticar; si falla, incrementa los intentos y genera un mensaje dinámico.
        4. Si la autenticación es exitosa, reinicia el contador de intentos.
        5. Retorna los tokens (access y refresh) y los datos del usuario autenticado.

        Args:
            attrs (dict): Diccionario con las credenciales del usuario (`username`, `password`).

        Raises:
            serializers.ValidationError: Si el usuario está bloqueado o las credenciales son incorrectas.

        Returns:
            dict: Par de tokens JWT (`access`, `refresh`) junto con la información del usuario.
        """
        
        username = attrs.get("username")

        # Buscar usuario para controlar intentos fallidos
        try:
            user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario o contraseña incorrectos.")
        
        # Verificar si el usuario está temporalmente bloqueado
        if user.esta_bloqueado():
            minutos_restantes = int((user.bloqueado_hasta - timezone.now()).total_seconds() // 60)
            raise serializers.ValidationError(
                f"Cuenta bloqueada temporalmente. Intente nuevamente en {minutos_restantes} minutos."
            )
        
        # Intentar autenticación normal
        try:
            data = super().validate(attrs)
        except (serializers.ValidationError, AuthenticationFailed):
            mensaje = user.registrar_intento_fallido()
            raise serializers.ValidationError(mensaje)

        # Si la autenticación fue exitosa, reiniciar los intentos fallidos
        user.resetear_intentos()
        
        # Verificar si la cuenta está desactivada a nivel Django
        if not self.user.is_active:
            raise serializers.ValidationError(
                'Esta cuenta está inactiva. Contacte al administrador.'
            )
        
        # Verificar si el estado del usuario en el modelo no es "activo"
        if self.user.estado != 'activo':
            raise serializers.ValidationError(
                f'Esta cuenta está en estado: {self.user.get_estado_display()}.'
            )
        
        # Agregar información adicional del usuario a la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'nombre_completo': self.user.get_full_name(),
            'roles': [ur.rol.nombre for ur in self.user.usuario_roles.select_related('rol')],
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        """
        Sobrescribe la generación del token JWT para añadir 'claims' personalizados.
        Estos datos pueden ser leídos directamente desde el payload del token.
        """
        token = super().get_token(user)
        
        # Claims personalizados del usuario
        token['username'] = user.username
        token['email'] = user.email
        token['nombre'] = user.nombre
        token['apellido'] = user.apellido
        token['roles'] = [ur.rol.nombre for ur in user.usuario_roles.select_related('rol')]
        
        return token
    

# Jeronimo Rodriguez 10/30/2025 
class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para auto-registro de clientes (público).
    Maneja:
    - Validación básica de contraseñas (coincidencia).
    - Creación del objeto Usuario usando el manager personalizado.
    - Asignación del rol 'cliente' y creación del perfil Cliente asociado.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    # Campos opcionales del perfil de cliente (no forman parte del modelo Usuario)
    telefono = serializers.CharField(required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'nombre', 'apellido', 'telefono', 'direccion'
        ]
    
    def validate(self, attrs):

        """Validaciones de entrada antes de crear el usuario.

        Actualmente verifica que `password` y `password_confirm` coincidan.
        Levanta ValidationError con un mensaje claro en caso de discrepancia.
        """

        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def create(self, validated_data):
        """Crea un Usuario con rol 'cliente' y su perfil Cliente.

        Flujo:
        1. Extrae y elimina campos de perfil (teléfono, dirección) y password_confirm.
        2. Crea el Usuario usando `create_user` del manager (asegura hashing).
        3. Asigna (o crea si no existe) el Rol 'cliente' y la relación UsuarioRol.
        4. Crea el perfil Cliente vinculado al usuario.

        Retorna el objeto Usuario creado.
        """
        
        # Extraer datos de perfil que no pertenecen al modelo Usuario
        telefono = validated_data.pop('telefono', '')
        direccion = validated_data.pop('direccion', '')
        # Quitar campo auxiliar de confirmación de contraseña
        validated_data.pop('password_confirm')
        
        # Crear usuario (manager debe encargarse del hashing de la contraseña)
        password = validated_data.pop('password')
        usuario = Usuario.objects.create_user(password=password, **validated_data)
        
        # Asignar rol de cliente (se crea si no existe)
        rol_cliente, _ = Rol.objects.get_or_create(nombre='cliente')
        UsuarioRol.objects.create(usuario=usuario, rol=rol_cliente)
        
        # Crear perfil de cliente con los datos opcionales
        Cliente.objects.create(
            usuario=usuario,
            telefono=telefono,
            direccion=direccion
        )
        
        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para ver/editar el perfil del usuario autenticado.

    Este serializer centraliza la información del usuario que ha iniciado sesión,
    incluyendo sus datos básicos, roles asignados y perfiles asociados
    (Veterinario, Practicante o Cliente).

    Características:
    - Combina datos del modelo Usuario con datos relacionados en modelos de perfil.
    - Usa SerializerMethodField para calcular campos dinámicos.
    - Solo permite edición de campos limitados (controlado por `read_only_fields`).
    """
    
    # Campos dinámicos obtenidos mediante métodos personalizados
    roles = serializers.SerializerMethodField()
    perfil_veterinario = serializers.SerializerMethodField()
    perfil_practicante = serializers.SerializerMethodField()
    perfil_cliente = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'nombre', 'apellido',
            'estado', 'roles', 'created_at',
            'perfil_veterinario', 'perfil_practicante', 'perfil_cliente'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'estado']

    """ 
    --------------------------------------------
    MÉTODOS PERSONALIZADOS
    --------------------------------------------
    """
    
    def get_roles(self, obj):
        """Obtiene los roles del usuario."""
        return [ur.rol.get_nombre_display() for ur in obj.usuario_roles.select_related('rol')]
    
    def get_perfil_veterinario(self, obj):
        """Retorna el perfil de veterinario si existe."""
        if hasattr(obj, 'perfil_veterinario'):
            return VeterinarioSerializer(obj.perfil_veterinario).data
        return None
    
    def get_perfil_practicante(self, obj):
        """Retorna el perfil de practicante si existe."""
        if hasattr(obj, 'perfil_practicante'):
            return PracticanteSerializer(obj.perfil_practicante).data
        return None
    
    def get_perfil_cliente(self, obj):
        """Retorna el perfil de cliente si existe."""
        if hasattr(obj, 'perfil_cliente'):
            return ClienteSerializer(obj.perfil_cliente).data
        return None