"""
Token serializers - Autenticación JWT personalizada.
"""
from rest_framework import serializers
from django.utils import timezone
from usuarios.models import Usuario
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
        
        # Verificar estado del usuario ANTES de intentar autenticar
        # Esto permite devolver mensajes de error apropiados
        # Verificar primero el estado personalizado para mensajes más específicos
        if user.estado != 'activo':
            estado_display = user.get_estado_display() if hasattr(user, 'get_estado_display') else user.estado
            raise serializers.ValidationError(
                f'Esta cuenta está en estado: {estado_display}.'
            )
        
        # Verificar is_active después del estado personalizado
        # (aunque normalmente si estado != 'activo', is_active también será False)
        if not user.is_active:
            raise serializers.ValidationError(
                'Esta cuenta está inactiva. Contacte al administrador.'
            )
        
        # Intentar autenticación normal
        try:
            data = super().validate(attrs)
        except (serializers.ValidationError, AuthenticationFailed):
            mensaje = user.registrar_intento_fallido()
            raise serializers.ValidationError(mensaje)

        # Si la autenticación fue exitosa, reiniciar los intentos fallidos
        user.resetear_intentos()
        
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
