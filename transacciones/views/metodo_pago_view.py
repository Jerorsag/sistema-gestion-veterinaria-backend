from rest_framework import generics
from transacciones.models.metodo_pago import MetodoPago
from transacciones.serializers.metodo_pago_serializer import MetodoPagoSerializer


class MetodoPagoListView(generics.ListAPIView):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer