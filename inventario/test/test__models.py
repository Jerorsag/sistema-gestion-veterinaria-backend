from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import Marca, Categoria, Producto, Kardex
from decimal import Decimal


#
class MarcaModelTest(TestCase):

    def test_creacion_marca_normaliza_descripcion(self):
        marca = Marca.objects.create(descripcion="  nike  ")
        self.assertEqual(marca.descripcion, "Nike")

    def test_marca_descripcion_duplicada(self):
        Marca.objects.create(descripcion="Adidas")
        marca_duplicada = Marca(descripcion="adidas")
        with self.assertRaises(ValidationError):
            marca_duplicada.clean()



class CategoriaModelTest(TestCase):

    def test_creacion_categoria_normaliza_descripcion(self):
        categoria = Categoria.objects.create(descripcion="  ropa deportiva  ")
        self.assertEqual(categoria.descripcion, "Ropa Deportiva")

    def test_categoria_descripcion_duplicada(self):
        Categoria.objects.create(descripcion="Calzado")
        categoria_duplicada = Categoria(descripcion="CALZADO")
        with self.assertRaises(ValidationError):
            categoria_duplicada.clean()


class ProductoModelTest(TestCase):

    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Puma")
        self.categoria = Categoria.objects.create(descripcion="Accesorios")

    def test_creacion_producto_normaliza_nombre(self):
        producto = Producto.objects.create(
            nombre="  gorra negra ",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2
        )
        self.assertEqual(producto.nombre, "Gorra Negra")

    def test_error_stock_minimo_mayor_stock(self):
        producto = Producto(
            nombre="Bolso",
            marca=self.marca,
            categoria=self.categoria,
            stock=2,
            stock_minimo=5
        )
        with self.assertRaises(ValidationError):
            producto.clean()

    def test_error_precio_compra_mayor_o_igual_precio_venta(self):
        producto = Producto(
            nombre="Billetera",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2,
            precio_compra=100,
            precio_venta=100
        )
        with self.assertRaises(ValidationError):
            producto.clean()

    def test_codigo_barras_unico(self):
        Producto.objects.create(
            nombre="Zapato",
            marca=self.marca,
            categoria=self.categoria,
            codigo_barras="123ABC"
        )
        producto2 = Producto(
            nombre="Zapato Deportivo",
            marca=self.marca,
            categoria=self.categoria,
            codigo_barras="123abc"
        )
        with self.assertRaises(ValidationError):
            producto2.clean()


class KardexModelTest(TestCase):

    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Converse")
        self.categoria = Categoria.objects.create(descripcion="Calzado")
        self.producto = Producto.objects.create(
            nombre="Tenis",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2
        )

    def test_kardex_entrada_actualiza_stock(self):
        """
        Verifica que una entrada suma al stock al crear (por el signal post_save)
        y resta al anular (por el método delete())
        """
        # Stock inicial: 10
        entrada = Kardex.objects.create(
            tipo='entrada',
            cantidad=Decimal('5.00'),
            producto=self.producto,
            detalle="Compra inicial"
        )

        # Al crear, el signal post_save suma al stock
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('15.00'))  # 10 + 5

        # Al anular (delete), revierte la entrada
        entrada.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('10.00'))  # 15 - 5

        # Verificar que se marcó como anulado
        entrada.refresh_from_db()
        self.assertIn("ANULADO", entrada.detalle)

    def test_kardex_salida_actualiza_stock(self):
        """
        Verifica que una salida resta del stock al crear (por el signal post_save)
        y suma al anular (por el método delete())
        """
        # Stock inicial: 10
        salida = Kardex.objects.create(
            tipo='salida',
            cantidad=Decimal('3.00'),
            producto=self.producto,
            detalle="Venta a cliente"
        )

        # Al crear, el signal post_save resta del stock
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('7.00'))  # 10 - 3

        # Al anular (delete), revierte la salida
        salida.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('10.00'))  # 7 + 3

        # Verificar que se marcó como anulado
        salida.refresh_from_db()
        self.assertIn("ANULADO", salida.detalle)

    def test_kardex_no_anula_dos_veces(self):
        """
        Verifica que un kardex no se anule dos veces
        """
        kardex = Kardex.objects.create(
            tipo='entrada',
            cantidad=Decimal('2.00'),
            producto=self.producto,
            detalle="Entrada de prueba"
        )

        # Stock después de la entrada: 10 + 2 = 12
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('12.00'))

        # Primera anulación
        kardex.delete()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, Decimal('10.00'))  # 12 - 2

        kardex.refresh_from_db()
        self.assertIn("ANULADO", kardex.detalle)
        detalle_primera_anulacion = kardex.detalle
        stock_primera_anulacion = self.producto.stock

        # Intentar anular de nuevo
        kardex.delete()
        self.producto.refresh_from_db()
        kardex.refresh_from_db()

        # El detalle no debe cambiar (sigue igual)
        self.assertEqual(kardex.detalle, detalle_primera_anulacion)
        # El stock no debe cambiar (sigue igual)
        self.assertEqual(self.producto.stock, stock_primera_anulacion)