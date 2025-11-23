from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q

from inventario.models import Producto
from inventario.serializers import ProductoSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(activo=True)
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Producto.objects.filter(activo=True)

        buscador = self.request.query_params.get("buscador")
        categoria = self.request.query_params.get("categoria")
        marca = self.request.query_params.get("marca")

        if buscador:
            queryset = queryset.filter(
                Q(nombre__icontains=buscador) |
                Q(descripcion__icontains=buscador) |
                Q(codigo_barras__icontains=buscador) |
                Q(codigo_interno__icontains=buscador)
            )

        if categoria:
            queryset = queryset.filter(
                Q(categoria__descripcion__icontains=categoria) |
                Q(categoria__id__iexact=categoria)
            )

        if marca:
            queryset = queryset.filter(
                Q(marca__descripcion__icontains=marca) |
                Q(marca__id__iexact=marca)
            )

        return queryset

#para desactivar un producto en lugar de eliminar
    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()

        if not producto.activo:
            return Response(
                {"detalle": "Este producto ya está desactivado y no puede eliminarse."},
                status=status.HTTP_400_BAD_REQUEST
            )

        producto.activo = False
        producto.save()

        return Response(
            {"detalle": "Producto desactivado correctamente. Los movimientos del kardex se mantienen intactos."},
            status=status.HTTP_200_OK
        )
