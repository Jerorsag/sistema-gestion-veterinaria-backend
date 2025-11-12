from rest_framework import status
from rest_framework.test import APITestCase
from inventario.models import Marca, Categoria, Producto, Kardex

class UrlsTests(APITestCase):

    def setUp(self):
        self.marca = Marca.objects.create(descripcion="Puma")
        self.categoria = Categoria.objects.create(descripcion="Tenis")
        self.producto = Producto.objects.create(
            nombre="RS-X",
            descripcion="Zapatillas deportivas",
            marca=self.marca,
            categoria=self.categoria,
            stock=10,
            stock_minimo=2,
            codigo_barras="987654321",
            codigo_interno="PX01",
            precio_venta=250000,
            precio_compra=150000,
        )
        self.kardex = Kardex.objects.create(
            producto=self.producto,
            tipo="entrada",
            cantidad=5,
            detalle="Reposición"
        )

    def test_list_marcas(self):
        response = self.client.get("/api/marcas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_categorias(self):
        response = self.client.get("/api/categorias/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_productos(self):
        response = self.client.get("/api/productos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_kardex(self):
        response = self.client.get("/api/kardex/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_producto(self):
        data = {
            "nombre": "Sudadera",
            "descripcion": "Sudadera deportiva",
            "marca_id": self.marca.id,
            "categoria_id": self.categoria.id,
            "stock": 5,
            "stock_minimo": 1,
            "codigo_barras": "ABC123",
            "codigo_interno": "SUD001",
            "precio_venta": 120000,
            "precio_compra": 80000,
        }
        response = self.client.post("/api/productos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nombre"], "Sudadera")