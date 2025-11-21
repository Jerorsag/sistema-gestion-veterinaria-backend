from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.serializers.auth_serializer import RegistroSerializer, UsuarioPerfilSerializer, CustomTokenObtainPairSerializer
from usuarios.serializers.crud_serializer import CambiarPasswordSerializer
from usuarios.serializers.reset_password import (
    ResetPasswordRequestSerializer,
    ResetPasswordConfirmSerializer,
)
from usuarios.modelos.reset_token import ResetPasswordToken
from django.utils import timezone
from datetime import timedelta
from notificaciones.services import enviar_notificacion_generica

# Jeronimo Rodriguez 10/31/2025 
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para la obtención de tokens JWT (Login).

    - Endpoint: POST /api/v1/auth/login/
    - Permite autenticar al usuario y retornar:
        • access token
        • refresh token
        • información básica del usuario autenticado
    - Utiliza el serializer CustomTokenObtainPairSerializer.
    """
    serializer_class = CustomTokenObtainPairSerializer

# Jeronimo Rodriguez 10/30/2025 
class RegistroView(generics.CreateAPIView):
    """
    Vista de API para el auto-registro de nuevos clientes en el sistema.

    Esta vista permite que cualquier usuario (sin autenticación previa)
    se registre como cliente, generando automáticamente su rol correspondiente
    y devolviendo un par de tokens JWT (refresh y access) para autenticación inmediata.
    """
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """
        Procesa la solicitud de registro:
        1. Valida los datos ingresados mediante el serializer.
        2. Crea el usuario con rol 'cliente' y su perfil asociado.
        3. Genera tokens JWT para el nuevo usuario.
        4. Retorna la información básica del usuario y los tokens de autenticación.
        """

        # Validar los datos enviados
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Crear el nuevo usuario
        user = serializer.save()
        
        # Generar tokens JWT para el nuevo usuario
        refresh = RefreshToken.for_user(user)
        
        # Respuesta exitosa con la información del usuario y los tokens
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nombre_completo': user.get_full_name(),
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Usuario registrado exitosamente.'
        }, status=status.HTTP_201_CREATED)
    
    
class PerfilView(generics.RetrieveUpdateAPIView):
    """
    API endpoint que permite a un usuario autenticado visualizar y actualizar su perfil.

    Esta vista hereda de `RetrieveUpdateAPIView`, lo que proporciona automáticamente:
    - **GET**: para recuperar los datos del usuario autenticado.
    - **PUT/PATCH**: para actualizar los datos personales o del perfil asociado.

    El serializer utilizado (`UsuarioPerfilSerializer`) se encarga de representar
    la información completa del usuario, incluyendo:
        - Datos básicos (nombre, email, estado).
        - Roles asignados.
        - Perfiles extendidos (veterinario, practicante o cliente).
    
    Requiere autenticación mediante JWT.
    """
    
    serializer_class = UsuarioPerfilSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Retorna el usuario autenticado."""
        return self.request.user
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password_view(request):
    """
    Endpoint para que el usuario autenticado cambie su contraseña.
    """
    serializer = CambiarPasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        # Cambiar la contraseña
        user = request.user
        user.set_password(serializer.validated_data['password_nueva'])
        user.save()
        
        return Response(
            {'detail': 'Contraseña actualizada correctamente.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Jeronimo Rodriguez 11/01/2025 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Endpoint para cerrar sesión.
    Añade el refresh token a la lista negra (si se implementa).
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'detail': 'Sesión cerrada exitosamente.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Se requiere el refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as _:
        return Response(
            {'detail': 'Token inválido o ya expirado.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_token_view(request):
    """
    Endpoint para verificar si el token es válido.
    Útil para el frontend para validar sesiones.
    """
    return Response({
        'valid': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'nombre_completo': request.user.get_full_name(),
            'roles': [ur.rol.nombre for ur in request.user.usuario_roles.select_related('rol')],
        }
    }, status=status.HTTP_200_OK)


class ResetPasswordRequestView(generics.GenericAPIView):
    serializer_class = ResetPasswordRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(email=email)

        # Crear token
        token_obj = ResetPasswordToken.create_for_user(user, minutes=60)

        # Construir link
        link = f"https://frontend/reset-password/?token={token_obj.token}"

        # Enviar notificación usando el servicio
        context = {
            'usuario_nombre': user.get_full_name(),
            'link': link,
        }
        try:
            enviar_notificacion_generica('RESET_PASSWORD', context, user.email)
        except Exception:
            # No fallar si el envío falla; loguear en producción
            pass

        return Response({'message': 'Si el correo existe, se ha enviado un enlace para restablecer la contraseña.'}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_obj = serializer.validated_data['token_obj']
        password = serializer.validated_data['password']

        user = token_obj.usuario
        user.set_password(password)
        user.save()

        token_obj.usado = True
        token_obj.save()

        return Response({'message': 'Contraseña restablecida correctamente.'}, status=status.HTTP_200_OK)