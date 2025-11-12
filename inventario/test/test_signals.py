from django.test import TestCase
from inventario.models import Marca, Categoria, Producto, Kardex


class SignalTests(TestCase):

    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Adidas")
        self.categoria = Categoria.objects.create(descripcion="Ropa")
        self.producto = Producto.objects.create(
            nombre="Sudadera",
            descripcion="Sudadera deportiva",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2,
            codigo_barras="111222333",
            codigo_interno="S001",
            precio_venta=200000,
            precio_compra=120000,
        )

    def test_post_save_aumenta_stock_entrada(self):
        """Verifica que un movimiento de tipo entrada aumenta el stock"""
        Kardex.objects.create(
            producto=self.producto,
            tipo="entrada",
            cantidad=5,
            detalle="Reposición",
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)  # 10 + 5

    def test_post_save_reduce_stock_salida(self):
        """Verifica que un movimiento de tipo salida reduce el stock"""
        Kardex.objects.create(
            producto=self.producto,
            tipo="salida",
            cantidad=4,
            detalle="Venta",
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 6)  # 10 - 4

    def test_pre_delete_anula_kardex(self):
        """
        CORREGIDO: Verifica que eliminar un Kardex revierte su efecto y lo marca como anulado.
        El método delete() del modelo hace soft delete (no elimina el registro físicamente).
        """
        kardex = Kardex.objects.create(
            producto=self.producto,
            tipo="entrada",
            cantidad=3,
            detalle="Error en carga",
        )

        # Después de crear: stock = 10 + 3 = 13
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 13)

        # Al eliminar (anular), revierte: stock = 13 - 3 = 10
        kardex.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

        # Verificar que el registro NO se eliminó, solo se marcó como anulado
        kardex.refresh_from_db()
        self.assertIn("ANULADO", kardex.detalle)

        # Verificar que el kardex aún existe en la base de datos
        self.assertTrue(Kardex.objects.filter(id=kardex.id).exists())