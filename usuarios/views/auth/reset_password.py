from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from usuarios.serializers.auth import (
    ResetPasswordRequestSerializer,
    ResetPasswordConfirmSerializer,
)
from usuarios.models import ResetPasswordToken
from notificaciones.services import enviar_notificacion_generica

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
