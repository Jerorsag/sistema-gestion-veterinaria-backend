from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from usuarios.serializers.auth_serializer import RegistroSerializer, UsuarioPerfilSerializer, CustomTokenObtainPairSerializer

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
    except Exception as e:
        return Response(
            {'detail': 'Token inválido o ya expirado.'},
            status=status.HTTP_400_BAD_REQUEST
        )