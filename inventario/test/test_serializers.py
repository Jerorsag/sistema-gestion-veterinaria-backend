from django.test import TestCase
from inventario.models import Marca, Categoria, Producto, Kardex
from inventario.serializers import (
    MarcaSerializer,
    CategoriaSerializer,
    ProductoSerializer,
    KardexSerializer,
)


class SerializerTests(TestCase):

    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Nike")
        self.categoria = Categoria.objects.create(descripcion="Zapatillas")
        self.producto = Producto.objects.create(
            nombre="Air Max",
            descripcion="Zapatillas deportivas",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2,
            codigo_barras="1234567890",
            codigo_interno="P001",
            precio_venta=300000,
            precio_compra=200000,
        )

    def test_marca_serializer(self):
        serializer = MarcaSerializer(self.marca)
        self.assertEqual(serializer.data["descripcion"], "Nike")

    def test_categoria_serializer(self):
        serializer = CategoriaSerializer(self.categoria)
        self.assertEqual(serializer.data["descripcion"], "Zapatillas")

    def test_producto_serializer_read(self):
        serializer = ProductoSerializer(self.producto)
        data = serializer.data
        self.assertEqual(data["nombre"], "Air Max")
        self.assertEqual(data["marca"]["descripcion"], "Nike")
        self.assertEqual(data["categoria"]["descripcion"], "Zapatillas")

    def test_producto_serializer_write(self):
        data = {
            "nombre": "Camiseta",
            "descripcion": "Deportiva",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "stock": 5,
            "stock_minimo": 1,
            "codigo_barras": "9876543210",
            "codigo_interno": "P002",
            "precio_venta": 100000,
            "precio_compra": 50000,
        }
        serializer = ProductoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        producto = serializer.save()
        self.assertEqual(producto.nombre, "Camiseta")

    def test_kardex_serializer_read(self):
        """
        CORREGIDO: El serializer ahora usa 'producto.nombre' en lugar de 'producto.descripcion'
        """
        kardex = Kardex.objects.create(
            producto=self.producto,
            tipo="entrada",
            cantidad=5,
            detalle="Reposición de stock",
        )
        serializer = KardexSerializer(kardex)

        # Verificar que producto_nombre usa el campo 'nombre' del producto
        self.assertEqual(serializer.data["producto_nombre"], "Air Max")
        self.assertEqual(serializer.data["codigo_interno"], "P001")