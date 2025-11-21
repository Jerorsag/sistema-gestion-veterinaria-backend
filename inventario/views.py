from rest_framework import status, viewsets
from rest_framework.response import Response
from .models import Marca, Categoria, Producto, Kardex
from .serializers import MarcaSerializer, CategoriaSerializer, ProductoSerializer, KardexSerializer
from django.db.models import Q

# ---- MARCA ----
class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer

    def create(self, request, *args, **kwargs):
        descripcion = request.data.get("descripcion")
        if Marca.objects.filter(descripcion__iexact=descripcion).exists():
            return Response({"mensaje": "duplicado"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        buscador = self.request.query_params.get("buscador")
        if buscador:
            return Marca.objects.filter(Q(descripcion__icontains=buscador))
        return Marca.objects.all()


# ---- CATEGORIA ----
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def create(self, request, *args, **kwargs):
        descripcion = request.data.get("descripcion")
        if Categoria.objects.filter(descripcion__iexact=descripcion).exists():
            return Response({"mensaje": "duplicado"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        buscador = self.request.query_params.get("buscador")
        if buscador:
            return Categoria.objects.filter(Q(descripcion__icontains=buscador))
        return Categoria.objects.all()


# ---- PRODUCTO ----
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def create(self, request, *args, **kwargs):
        descripcion = request.data.get("descripcion")
        if Producto.objects.filter(descripcion__iexact=descripcion).exists():
            return Response({"mensaje": "duplicado"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Producto.objects.all()
        buscador = self.request.query_params.get("buscador")
        categoria = self.request.query_params.get("categoria")
        marca = self.request.query_params.get("marca")

        if buscador:
            queryset = queryset.filter(Q(descripcion__icontains=buscador))

        if categoria:
            # Buscar por nombre o ID
            queryset = queryset.filter(
                Q(categoria__descripcion__icontains=categoria) | Q(categoria__id__iexact=categoria)
            )

        if marca:
            queryset = queryset.filter(
                Q(marca__descripcion__icontains=marca) | Q(marca__id__iexact=marca)
            )

        return queryset

class KardexViewSet(viewsets.ModelViewSet):
    serializer_class = KardexSerializer
    queryset = Kardex.objects.all().order_by('-fecha')

    def get_queryset(self):
        buscador = self.request.query_params.get("buscador")
        if buscador:
            return Kardex.objects.filter(Q(producto__descripcion__icontains=buscador))
        return Kardex.objects.all().order_by('-fecha')

    def destroy(self, request, *args, **kwargs):
        #Cuando el usuario (desde Postman, API o frontend) hace DELETE, no se elimina físicamente el registro: se anula y se revierte el stock.

        instance = self.get_object()

        # Guardamos una referencia antes de modificar el tipo
        tipo_original = instance.tipo

        # Llamamos al delete() del modelo (que realiza la anulación lógica)
        instance.delete()

        # Retornamos respuesta personalizada
        return Response(
            {
                "mensaje": f"Movimiento {instance.id} ({tipo_original}) anulado correctamente.",
                "detalle": instance.detalle,
                "tipo": instance.tipo,
            },
            status=status.HTTP_200_OK
        )