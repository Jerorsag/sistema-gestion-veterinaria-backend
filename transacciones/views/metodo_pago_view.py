from rest_framework import generics
from transacciones.models.metodo_pago import MetodoPago
from transacciones.serializers.metodo_pago_serializer import MetodoPagoSerializer


class MetodoPagoListView(generics.ListCreateAPIView):
    """
    Vista para listar y crear métodos de pago.
    
    Permite:
    - GET: Listar todos los métodos de pago
    - POST: Crear un nuevo método de pago
    """
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer