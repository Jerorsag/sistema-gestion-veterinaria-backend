from django.urls import path
from transacciones.views.factura_view import (
    FacturaListCreateView,
    FacturaDetailView
)
from transacciones.views.pago_view import PagoListCreateView
from transacciones.views.metodo_pago_view import MetodoPagoListView

urlpatterns = [

    # Facturas
    path('facturas/', FacturaListCreateView.as_view(), name='factura-list-create'),
    path('facturas/<int:pk>/', FacturaDetailView.as_view(), name='factura-detail'),

    # Pagos
    path('pagos/', PagoListCreateView.as_view(), name='pago-list-create'),

    # Métodos de pago
    path('metodos-pago/', MetodoPagoListView.as_view(), name='metodo-pago-list'),
]