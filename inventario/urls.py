from rest_framework.routers import DefaultRouter
from .views import MarcaViewSet, CategoriaViewSet, ProductoViewSet, KardexViewSet

router = DefaultRouter()
router.register(r"marcas", MarcaViewSet)
router.register(r"categorias", CategoriaViewSet)
router.register(r"productos", ProductoViewSet)
router.register(r'kardex', KardexViewSet)

urlpatterns = router.urls
