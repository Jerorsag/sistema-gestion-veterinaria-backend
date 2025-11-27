
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from inventario.models import Notificacion
from inventario.serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):

    queryset = Notificacion.objects.all().order_by('-fecha')
    serializer_class = NotificacionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):

        qs = Notificacion.objects.all().order_by('-fecha')
        modulo = self.request.query_params.get("modulo")

        if modulo:
            qs = qs.filter(modulo=modulo)

        return qs