from rest_framework import generics
from transacciones.models.factura import Factura
from transacciones.serializers.factura_serializer import FacturaSerializer


class FacturaListCreateView(generics.ListCreateAPIView):
    queryset = Factura.objects.all().select_related(
        'cliente', 'cita', 'consulta'
    ).prefetch_related('detalles')
    serializer_class = FacturaSerializer

    def perform_create(self, serializer):
        # Asignar el cliente autenticado SIEMPRE
        serializer.save(cliente=self.request.user)


class FacturaDetailView(generics.RetrieveAPIView):
    queryset = Factura.objects.all().select_related(
        'cliente', 'cita', 'consulta'
    ).prefetch_related('detalles')
    serializer_class = FacturaSerializer