from django.urls import path
from . import views
from usuarios.views.auth_views import RegistroView, PerfilView

urlpatterns = [
    # Registro público
     path('auth/register/', RegistroView.as_view(), name='registro'),

     # Perfil del usuario autenticado
    path('perfil/', PerfilView.as_view(), name='perfil')
]