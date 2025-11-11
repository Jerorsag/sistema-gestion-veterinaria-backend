from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views.auth_views import (
    CustomTokenObtainPairView, 
    RegistroView, 
    logout_view,
    verificar_token_view,
    PerfilView
)
from usuarios.views.user_views import UsuarioViewSet, RolViewSet

# Configurar el router para los ViewSets
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/verify/', verificar_token_view, name='verify_token'),

    # Registro público
     path('auth/register/', RegistroView.as_view(), name='registro'),

     # Perfil del usuario autenticado
    path('perfil/', PerfilView.as_view(), name='perfil'),

    # Rutas del router (CRUD de usuarios y roles)
    path('', include(router.urls))
]