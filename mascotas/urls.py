from django.urls import path
from mascotas.views.mascota_views import (
    MascotaListCreateView,
    MascotaRetrieveUpdateDeleteView,
    EspecieListView,
    RazaListView,
)

# Jeronimo Rodriguez - 11/03/2025

urlpatterns = [
    path('mascotas/especies/', EspecieListView.as_view(), name='especies-list'),
    path('mascotas/razas/', RazaListView.as_view(), name='razas-list'),
    path('mascotas/', MascotaListCreateView.as_view(), name='mascotas-list-create'),
    # Use integer primary keys (BaseModel.id es BigAutoField en este proyecto).
    path('mascotas/<int:pk>/', MascotaRetrieveUpdateDeleteView.as_view(), name='mascota-detail'),
]