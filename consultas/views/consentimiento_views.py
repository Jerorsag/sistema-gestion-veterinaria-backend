# consultas/views/consentimiento_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny  # ¡Público!
from rest_framework import status
from django.utils import timezone
from consultas.models import Consulta


class ConfirmarConsentimientoView(APIView):
    """
    Endpoint público para que un cliente confirme un consentimiento
    haciendo clic en el enlace del correo.

    Espera un método POST con un JSON: {"token": "..."}
    """
    permission_classes = [AllowAny]  # No requiere login

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')

        if not token:
            return Response(
                {"error": "Token no proporcionado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Buscar la consulta por el token de texto
            consulta = Consulta.objects.get(consentimiento_token=token)

            # 2. Marcar como confirmada (solo la primera vez)
            if not consulta.consentimiento_otorgado:
                consulta.consentimiento_otorgado = True
                consulta.consentimiento_fecha = timezone.now()
                consulta.save(update_fields=['consentimiento_otorgado', 'consentimiento_fecha'])

            return Response(
                {"message": "Consentimiento confirmado exitosamente."},
                status=status.HTTP_200_OK
            )

        except Consulta.DoesNotExist:
            return Response(
                {"error": "Enlace de consentimiento inválido o expirado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )