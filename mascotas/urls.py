from django.urls import path
from mascotas.views.mascota_views import (
    MascotaListCreateView,
    MascotaRetrieveUpdateDeleteView,
)

# Jeronimo Rodriguez - 11/03/2025

urlpatterns = [
    path('mascotas/', MascotaListCreateView.as_view(), name='mascotas-list-create'),
    # Use integer primary keys (BaseModel.id es BigAutoField en este proyecto).
    path('mascotas/<int:pk>/', MascotaRetrieveUpdateDeleteView.as_view(), name='mascota-detail'),
]