"""
Endpoint temporal para crear superuser sin usar shell.
⚠️ IMPORTANTE: Eliminar este endpoint después de crear el superuser en producción.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from usuarios.models import Usuario
import os

User = get_user_model()

class CreateSuperuserView(APIView):
    """
    Endpoint temporal para crear superuser.
    
    Solo funciona si:
    1. No existe ningún superuser en el sistema
    2. O se proporciona una clave secreta (SUPERUSER_CREATION_KEY)
    
    ⚠️ ELIMINAR ESTE ENDPOINT DESPUÉS DE CREAR EL SUPERUSER
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Verificar si ya existe un superuser
        existing_superusers = User.objects.filter(is_superuser=True).count()
        
        # Si ya existe un superuser, verificar clave secreta
        if existing_superusers > 0:
            secret_key = request.data.get('secret_key') or request.query_params.get('secret_key')
            expected_key = os.getenv('SUPERUSER_CREATION_KEY', '')
            
            if not secret_key or secret_key != expected_key:
                return Response(
                    {
                        'error': 'Ya existe un superuser en el sistema. Se requiere SUPERUSER_CREATION_KEY para crear otro.',
                        'hint': 'Configura SUPERUSER_CREATION_KEY en Render Dashboard si necesitas crear más superusers.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Obtener datos del request
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        nombre = request.data.get('nombre', '')
        apellido = request.data.get('apellido', '')
        
        # Validar campos requeridos
        if not username or not email or not password:
            return Response(
                {
                    'error': 'Faltan campos requeridos',
                    'required': ['username', 'email', 'password'],
                    'optional': ['nombre', 'apellido']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el usuario no exista
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': f'El usuario "{username}" ya existe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': f'El email "{email}" ya está registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el superuser
        try:
            superuser = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                nombre=nombre or username,
                apellido=apellido or ''
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Superuser creado exitosamente',
                    'data': {
                        'id': superuser.id,
                        'username': superuser.username,
                        'email': superuser.email,
                        'nombre_completo': superuser.get_full_name(),
                        'is_superuser': superuser.is_superuser,
                        'is_staff': superuser.is_staff
                    },
                    'warning': '⚠️ Recuerda eliminar este endpoint después de crear el superuser en producción'
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'Error al crear superuser',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

