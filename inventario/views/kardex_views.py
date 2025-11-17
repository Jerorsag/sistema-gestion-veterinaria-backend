from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q

from inventario.models import Kardex
from inventario.serializers import KardexSerializer


class KardexViewSet(viewsets.ModelViewSet):

    serializer_class = KardexSerializer
    queryset = Kardex.objects.all().order_by('-fecha')
    permission_classes = [AllowAny]

    def get_queryset(self):

        buscador = self.request.query_params.get("buscador")
        if buscador:
            return Kardex.objects.filter(
                Q(producto__nombre__icontains=buscador) |
                Q(detalle__icontains=buscador)
            ).order_by('-fecha')
        return Kardex.objects.all().order_by('-fecha')

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        # Soft delete (marca como ANULADO y ajusta stock)
        instance.delete()

        # Se recarga desde la base de datos
        instance.refresh_from_db()

        # Se devuelve el Kardex completo
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)