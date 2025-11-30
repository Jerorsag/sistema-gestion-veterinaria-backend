from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from usuarios.serializers.auth import CustomTokenObtainPairSerializer
import logging

logger = logging.getLogger(__name__)

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
    
    def post(self, request, *args, **kwargs):
        """
        Sobrescribir post para asegurar que siempre devuelva JSON.
        """
        try:
            # Log del request para debugging
            logger.info(f"Login request recibido - Content-Type: {request.content_type}")
            logger.info(f"Login request data: {request.data if hasattr(request, 'data') else 'No data'}")
            
            # Llamar al método padre
            response = super().post(request, *args, **kwargs)
            
            # Asegurar que la respuesta sea JSON
            if not isinstance(response.data, dict):
                response.data = {'detail': str(response.data)}
            
            return response
            
        except Exception as e:
            # Capturar cualquier excepción y devolver JSON
            logger.error(f"Error en login: {type(e).__name__}: {str(e)}")
            return Response(
                {
                    'detail': str(e) if str(e) else 'Error al procesar la solicitud de login',
                    'error_type': type(e).__name__
                },
                status=status.HTTP_400_BAD_REQUEST
            )
