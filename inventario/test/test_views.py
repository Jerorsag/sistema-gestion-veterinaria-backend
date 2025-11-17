from rest_framework import status
from rest_framework.test import APITestCase
from inventario.models import Marca, Categoria, Producto, Kardex


class MarcaViewSetTest(APITestCase):
    def test_crear_marca_exitosa(self):
        data = {"descripcion": "Nike"}
        response = self.client.post("/api/marcas/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["descripcion"], "Nike")

    def test_marca_duplicada(self):
        Marca.objects.create(descripcion="Nike")
        response = self.client.post("/api/marcas/", {"descripcion": "nike"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("duplicado", response.data["mensaje"])

    def test_marca_sin_descripcion(self):
        response = self.client.post("/api/marcas/", {"descripcion": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("requerida", response.data["mensaje"])


class CategoriaViewSetTest(APITestCase):
    def test_crear_categoria_exitosa(self):
        data = {"descripcion": "Deportes"}
        response = self.client.post("/api/categorias/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["descripcion"], "Deportes")

    def test_categoria_duplicada(self):
        Categoria.objects.create(descripcion="Ropa")
        response = self.client.post("/api/categorias/", {"descripcion": "ropa"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_categoria_sin_descripcion(self):
        response = self.client.post("/api/categorias/", {"descripcion": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductoViewSetTest(APITestCase):
    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Adidas")
        self.categoria = Categoria.objects.create(descripcion="Zapatos")

    def test_crear_producto_exitoso(self):
        data = {
            "nombre": "Ultraboost",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "stock": 10,
            "stock_minimo": 2,
            "precio_venta": 500000,
            "precio_compra": 300000,
            "codigo_barras": "ABC123",
            "codigo_interno": "P001"
        }
        response = self.client.post("/api/productos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nombre"], "Ultraboost")

    def test_producto_nombre_duplicado(self):
        Producto.objects.create(
            nombre="Gazelle",
            marca=self.marca,
            categoria=self.categoria,
            precio_compra=100000,
            precio_venta=200000
        )
        data = {
            "nombre": "gazelle",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "precio_compra": 120000,
            "precio_venta": 250000
        }
        response = self.client.post("/api/productos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("duplicado", response.data["mensaje"])

    def test_stock_minimo_mayor_stock(self):
        data = {
            "nombre": "Forum Low",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "stock": 5,
            "stock_minimo": 10,
            "precio_venta": 200000,
            "precio_compra": 100000
        }
        response = self.client.post("/api/productos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stock mínimo", response.data["mensaje"])

    def test_precio_compra_mayor_que_venta(self):
        data = {
            "nombre": "Campus",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "precio_compra": 300000,
            "precio_venta": 250000
        }
        response = self.client.post("/api/productos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("precio de compra", response.data["mensaje"])


class KardexViewSetTest(APITestCase):
    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Puma")
        self.categoria = Categoria.objects.create(descripcion="Accesorios")
        self.producto = Producto.objects.create(
            nombre="Guantes",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2,
            precio_venta=150000,
            precio_compra=80000,
        )

    def test_crear_entrada_kardex(self):
        data = {
            "tipo": "entrada",
            "cantidad": "5",
            "detalle": "Compra inicial",
            "producto": self.producto.id
        }
        response = self.client.post("/api/kardex/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filtrar_kardex_por_buscador(self):
        Kardex.objects.create(tipo="entrada", cantidad=3, producto=self.producto)
        response = self.client.get("/api/kardex/?buscador=Guantes")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_eliminar_kardex_actualiza_tipo(self):
        """
        CORREGIDO: Verifica que el detalle contenga 'ANULADO' (no el tipo)
        """
        kardex = Kardex.objects.create(tipo="entrada", cantidad=2, producto=self.producto, detalle="Compra")
        response = self.client.delete(f"/api/kardex/{kardex.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la respuesta contiene "ANULADO" en el detalle
        self.assertIn("ANULADO", response.data["detalle"])