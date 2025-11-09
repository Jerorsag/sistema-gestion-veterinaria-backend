"""
Views y endpoints para gestionar Prescripciones de productos (medicamentos)
"""
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from consultas.models import Prescripcion
from consultas.serializers.prescripcion_serializers import (
    PrescripcionSerializer,
    PrescripcionListSerializer
)


class PrescripcionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Integración con Inventario: Valida stock disponible antes de crear, Descuenta automáticamente del inventario (via signal), Genera alertas si el stock es bajo
    """

    queryset = Prescripcion.objects.all().select_related(
        'consulta',
        'medicamento'  # Sigue siendo el campo FK → Producto
    )
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['consulta', 'medicamento']
    search_fields = ['medicamento__descripcion', 'indicaciones']
    ordering_fields = ['fecha_prescripcion']
    ordering = ['-fecha_prescripcion']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return PrescripcionListSerializer
        return PrescripcionSerializer

    def get_queryset(self):
        """
        Filtra prescripciones según permisos del usuario.
        Prioridad: Admin > Veterinario/Practicante > Cliente
        """
        user = self.request.user
        queryset = super().get_queryset()

        #Admins ven todo
        if user.is_staff:
            return queryset

        #Veterinarios y practicantes ven todo
        if hasattr(user, 'perfil_veterinario') or hasattr(user, 'perfil_practicante'):
            return queryset

        #Clientes solo ven prescripciones de sus mascotas
        if hasattr(user, 'perfil_cliente'):
            cliente = user.perfil_cliente
            return queryset.filter(consulta__mascota__cliente=cliente)

        # Sin rol: sin acceso
        return queryset.none()

    @action(detail=False, methods=['get'], url_path='consulta/(?P<consulta_id>[^/.]+)')
    def por_consulta(self, request, consulta_id=None):
        """
        Retorna todas las prescripciones de una consulta.
        """
        prescripciones = self.get_queryset().filter(consulta_id=consulta_id)
        serializer = PrescripcionSerializer(prescripciones, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='producto/(?P<producto_id>[^/.]+)')
    def por_producto(self, request, producto_id=None):
        """
        Retorna todas las veces que se ha prescrito un producto.
        """
        prescripciones = self.get_queryset().filter(medicamento_id=producto_id)
        serializer = PrescripcionListSerializer(prescripciones, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mas_prescritos(self, request):
        """
        Retorna los productos más prescritos.
        """
        from django.db.models import Count, Sum

        mas_prescritos = self.get_queryset().values(
            'medicamento__id',
            'medicamento__nombre'
        ).annotate(
            veces_prescrito=Count('id'),
            cantidad_total=Sum('cantidad')
        ).order_by('-veces_prescrito')[:10]

        return Response(list(mas_prescritos))
