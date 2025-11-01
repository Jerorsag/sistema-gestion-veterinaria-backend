from django.urls import path
from . import views
from usuarios.views.auth_views import (
    CustomTokenObtainPairView, 
    RegistroView, 
    PerfilView
)

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Registro público
     path('auth/register/', RegistroView.as_view(), name='registro'),

     # Perfil del usuario autenticado
    path('perfil/', PerfilView.as_view(), name='perfil')
]