from django.urls import path
from mascotas.views.mascota_views import (
    MascotaListCreateView,
    MascotaRetrieveUpdateDeleteView,
)

# Jeronimo Rodriguez - 11/03/2025

urlpatterns = [
    path('mascotas/', MascotaListCreateView.as_view(), name='mascotas-list-create'),
    # Models use UUID primary keys (BaseModel.id is a UUIDField). Use the uuid converter so DRF views receive UUIDs.
    path('mascotas/<int:pk>/', MascotaRetrieveUpdateDeleteView.as_view(), name='mascota-detail'),
]