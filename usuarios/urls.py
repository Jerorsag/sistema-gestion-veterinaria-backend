from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views.auth_views import (
    CustomTokenObtainPairView, 
    RegistroView, 
    logout_view,
    verificar_token_view,
    PerfilView
)

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/verify/', verificar_token_view, name='verify_token'),

    # Registro público
     path('auth/register/', RegistroView.as_view(), name='registro'),

     # Perfil del usuario autenticado
    path('perfil/', PerfilView.as_view(), name='perfil')
]