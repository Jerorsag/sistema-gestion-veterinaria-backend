from django.urls import path
from transacciones.views.factura_view import (
    FacturaListCreateView,
    FacturaDetailView
)
from transacciones.views.pago_view import PagoListCreateView
from transacciones.views.metodo_pago_view import MetodoPagoListView
from transacciones.views.factura_actions_view import (
    CrearFacturaDesdeCita,
    CrearFacturaDesdeConsulta
)


urlpatterns = [

    # Facturas
    path('facturas/', FacturaListCreateView.as_view(), name='factura-list-create'),
    path('facturas/<int:pk>/', FacturaDetailView.as_view(), name='factura-detail'),

    # Acciones especiales
    path("facturas/crear-desde-cita/<int:cita_id>/", CrearFacturaDesdeCita.as_view()),
    path("facturas/crear-desde-consulta/<int:consulta_id>/", CrearFacturaDesdeConsulta.as_view()),

    # Pagos
    path('pagos/', PagoListCreateView.as_view(), name='pago-list-create'),

    # Métodos de pago
    path('metodos-pago/', MetodoPagoListView.as_view(), name='metodo-pago-list'),
]