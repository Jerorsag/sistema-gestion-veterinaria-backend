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
        descripcion = request.data.get("descripcion", "").strip().title()

        if not descripcion:
            return Response(
                {"mensaje": "La descripción es requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar duplicados
        if Marca.objects.filter(descripcion__iexact=descripcion).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "descripcion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el valor normalizado en el request
        request.data['descripcion'] = descripcion
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instancia = self.get_object()
        nueva_desc = request.data.get("descripcion", "").strip().title()

        if not nueva_desc:
            return Response(
                {"mensaje": "La descripción es requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar duplicados excluyendo la instancia actual
        if Marca.objects.filter(descripcion__iexact=nueva_desc).exclude(pk=instancia.pk).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "descripcion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el valor normalizado en el request
        request.data['descripcion'] = nueva_desc
        return super().update(request, *args, **kwargs)

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
        descripcion = request.data.get("descripcion", "").strip().title()

        if not descripcion:
            return Response(
                {"mensaje": "La descripción es requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar duplicados
        if Categoria.objects.filter(descripcion__iexact=descripcion).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "descripcion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el valor normalizado en el request
        request.data['descripcion'] = descripcion
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instancia = self.get_object()
        nueva_desc = request.data.get("descripcion", "").strip().title()

        if not nueva_desc:
            return Response(
                {"mensaje": "La descripción es requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar duplicados excluyendo la instancia actual
        if Categoria.objects.filter(descripcion__iexact=nueva_desc).exclude(pk=instancia.pk).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "descripcion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el valor normalizado en el request
        request.data['descripcion'] = nueva_desc
        return super().update(request, *args, **kwargs)

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
        # Normalizar campos
        nombre = request.data.get("nombre", "").strip().title()
        codigo_barras = request.data.get("codigo_barras", "").strip() if request.data.get("codigo_barras") else None
        codigo_interno = request.data.get("codigo_interno", "").strip() if request.data.get("codigo_interno") else None

        # Obtener valores numéricos
        stock = request.data.get("stock", 0)
        stock_minimo = request.data.get("stock_minimo", 0)
        precio_compra = request.data.get("precio_compra", 0)
        precio_venta = request.data.get("precio_venta", 0)

        # Convertir a Decimal para comparación segura
        from decimal import Decimal
        try:
            stock = Decimal(str(stock))
            stock_minimo = Decimal(str(stock_minimo))
            precio_compra = Decimal(str(precio_compra))
            precio_venta = Decimal(str(precio_venta))
        except:
            return Response(
                {"mensaje": "Los valores numéricos son inválidos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar nombre requerido
        if not nombre:
            return Response(
                {"mensaje": "El nombre es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar nombre único
        if Producto.objects.filter(nombre__iexact=nombre).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "nombre"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar código de barras único
        if codigo_barras and Producto.objects.filter(codigo_barras__iexact=codigo_barras).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "codigo_barras"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar código interno único
        if codigo_interno and Producto.objects.filter(codigo_interno__iexact=codigo_interno).exists():
            return Response(
                {"mensaje": "duplicado", "campo": "codigo_interno"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Stock mínimo debe ser menor o igual al stock
        if stock_minimo > stock:
            return Response(
                {"mensaje": "El stock mínimo no puede ser mayor al stock actual"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Precio de compra debe ser menor al precio de venta
        if precio_venta > 0 and precio_compra >= precio_venta:
            return Response(
                {"mensaje": "El precio de compra debe ser menor al precio de venta"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar valores normalizados
        request.data['nombre'] = nombre
        if codigo_barras:
            request.data['codigo_barras'] = codigo_barras
        if codigo_interno:
            request.data['codigo_interno'] = codigo_interno

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instancia = self.get_object()

        # Normalizar campos
        nombre = request.data.get("nombre", "").strip().title() if request.data.get("nombre") else None
        codigo_barras = request.data.get("codigo_barras", "").strip() if request.data.get("codigo_barras") else None
        codigo_interno = request.data.get("codigo_interno", "").strip() if request.data.get("codigo_interno") else None

        # Obtener valores numéricos
        stock = request.data.get("stock", instancia.stock)
        stock_minimo = request.data.get("stock_minimo", instancia.stock_minimo)
        precio_compra = request.data.get("precio_compra", instancia.precio_compra)
        precio_venta = request.data.get("precio_venta", instancia.precio_venta)

        # Convertir a Decimal para comparación segura
        from decimal import Decimal
        try:
            stock = Decimal(str(stock))
            stock_minimo = Decimal(str(stock_minimo))
            precio_compra = Decimal(str(precio_compra))
            precio_venta = Decimal(str(precio_venta))
        except:
            return Response(
                {"mensaje": "Los valores numéricos son inválidos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar nombre único
        if nombre:
            if Producto.objects.filter(nombre__iexact=nombre).exclude(pk=instancia.pk).exists():
                return Response(
                    {"mensaje": "duplicado", "campo": "nombre"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.data['nombre'] = nombre

        # Validar código de barras único
        if codigo_barras:
            if Producto.objects.filter(codigo_barras__iexact=codigo_barras).exclude(pk=instancia.pk).exists():
                return Response(
                    {"mensaje": "duplicado", "campo": "codigo_barras"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.data['codigo_barras'] = codigo_barras

        # Validar código interno único
        if codigo_interno:
            if Producto.objects.filter(codigo_interno__iexact=codigo_interno).exclude(pk=instancia.pk).exists():
                return Response(
                    {"mensaje": "duplicado", "campo": "codigo_interno"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.data['codigo_interno'] = codigo_interno

        # Stock mínimo debe ser menor o igual al stock
        if stock_minimo > stock:
            return Response(
                {"mensaje": "El stock mínimo no puede ser mayor al stock actual"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Precio de compra debe ser menor al precio de venta
        if precio_venta > 0 and precio_compra >= precio_venta:
            return Response(
                {"mensaje": "El precio de compra debe ser menor al precio de venta"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Producto.objects.all()
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
                Q(categoria__descripcion__icontains=categoria) | Q(categoria__id__iexact=categoria)
            )

        if marca:
            queryset = queryset.filter(
                Q(marca__descripcion__icontains=marca) | Q(marca__id__iexact=marca)
            )

        return queryset


# ---- KARDEX ----
class KardexViewSet(viewsets.ModelViewSet):
    serializer_class = KardexSerializer
    queryset = Kardex.objects.all().order_by('-fecha')

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
        tipo_original = instance.tipo
        instance.delete()
        return Response(
            {
                "mensaje": f"Movimiento {instance.id} ({tipo_original}) anulado correctamente.",
                "detalle": instance.detalle,
                "tipo": instance.tipo,
            },
            status=status.HTTP_200_OK
        )