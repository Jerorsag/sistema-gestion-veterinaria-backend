"""
view y endpoinds para gestionar Prescripciones de medicamentos.

Endpoints:
- GET /api/prescripciones/ - Listar prescripciones
- GET /api/prescripciones/{id}/ - Ver detalle
- POST /api/prescripciones/ - Crear prescripción individual
- PUT /api/prescripciones/{id}/ - Actualizar prescripción
- DELETE /api/prescripciones/{id}/ - Eliminar prescripción
- GET /api/prescripciones/consulta/{consulta_id}/ - Por consulta
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from clinica_veterinaria.consultas.models import Prescripcion
from clinica_veterinaria.consultas.serializers.prescripcion_serializers import (
    PrescripcionSerializer,
    PrescripcionCreateSerializer,
    PrescripcionListSerializer
)


class PrescripcionViewSet(viewsets.ModelViewSet):
    """
    para gestión de prescripciones.
    Integración con Inventario:
    - Valida stock disponible antes de crear
    - Descuenta automáticamente del inventario (via signal)
    - Genera alertas si el stock es bajo
    """

    queryset = Prescripcion.objects.all().select_related(
        'consulta',
        'medicamento'
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return PrescripcionListSerializer
        elif self.action == 'create':
            return PrescripcionCreateSerializer
        return PrescripcionSerializer

    def get_queryset(self):
        """Filtra prescripciones según permisos del usuario"""
        user = self.request.user
        queryset = super().get_queryset()

        # Si es propietario, solo prescripciones de sus mascotas
        if hasattr(user, 'mascotas'):
            return queryset.filter(consulta__mascota__propietario=user)

        return queryset

    @action(detail=False, methods=['get'], url_path='consulta/(?P<consulta_id>[^/.]+)')
    def por_consulta(self, request, consulta_id=None):
        """
        Retorna todas las prescripciones de una consulta.
        GET /api/prescripciones/consulta/{consulta_id}/
        """
        prescripciones = self.get_queryset().filter(consulta_id=consulta_id)
        serializer = PrescripcionSerializer(prescripciones, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='medicamento/(?P<medicamento_id>[^/.]+)')
    def por_medicamento(self, request, medicamento_id=None):
        """
        Retorna todas las veces que se ha prescrito un medicamento.
        GET /api/prescripciones/medicamento/{medicamento_id}/
        Útil para análisis de uso de medicamentos.
        """
        prescripciones = self.get_queryset().filter(medicamento_id=medicamento_id)
        serializer = PrescripcionListSerializer(prescripciones, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mas_prescritos(self, request):
        """
        Retorna los medicamentos más prescritos.
        GET /api/prescripciones/mas-prescritos/
        Útil para reportes y gestión de inventario.
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