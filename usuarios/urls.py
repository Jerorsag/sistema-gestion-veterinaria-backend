from django.urls import path
from . import views
from usuarios.views.auth_views import RegistroView

urlpatterns = [
    # Registro público
     path('auth/register/', RegistroView.as_view(), name='registro')
]