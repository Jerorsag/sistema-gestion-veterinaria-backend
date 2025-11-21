"""
view y endpoints para Historia Clínica Consolidada.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count

# IMPORTANTE: Usar el modelo de consultas, NO de mascotas
from consultas.models import HistoriaClinica
from consultas.serializers.historia_clinica_serializers import (
    HistoriaClinicaSerializer,
    HistoriaClinicaDetalleSerializer,
    UltimaConsultaSerializer
)


class HistoriaClinicaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar historias clínicas consolidadas.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['mascota']
    search_fields = [
        'mascota__nombre',
        'mascota__cliente__usuario__nombre',
        'mascota__cliente__usuario__apellido'
    ]

    def get_queryset(self):
        """
        Filtra historias según el rol del usuario.
        """
        user = self.request.user

        queryset = HistoriaClinica.objects.select_related(
            'mascota',
            'mascota__cliente',
            'mascota__cliente__usuario',
            'mascota__especie',
            'mascota__raza'
        ).prefetch_related(
            'mascota__consultas'
        )

        # FILTRADO POR ROL
        if hasattr(user, 'cliente'):
            cliente = user.cliente
            return queryset.filter(mascota__cliente=cliente)

        # Si no tiene perfil_cliente, es VETERINARIO, PRACTICANTE, RECEPCIONISTA o ADMIN
        return queryset

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'retrieve' or self.action == 'por_mascota':
            return HistoriaClinicaDetalleSerializer
        elif self.action == 'ultima_consulta':
            return UltimaConsultaSerializer
        return HistoriaClinicaSerializer

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna la historia clínica de una mascota por su ID.
        """
        try:
            historia = self.get_queryset().get(mascota_id=mascota_id)
        except HistoriaClinica.DoesNotExist:
            return Response(
                {'detail': 'Esta mascota no tiene historia clínica registrada o no tienes permisos para verla'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(historia)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='ultima-consulta')
    def ultima_consulta(self, request, pk=None):
        """
        Retorna solo la última consulta de la historia clínica.
        """
        historia = self.get_object()
        serializer = UltimaConsultaSerializer(historia, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda avanzada de historias clínicas.
        """
        query = request.query_params.get('q', '')

        if not query:
            return Response(
                {'detail': 'Debe proporcionar un término de búsqueda'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Usar get_queryset() para respetar los permisos
        historias = self.get_queryset().filter(
            mascota__nombre__icontains=query
        ) | self.get_queryset().filter(
            mascota__cliente__usuario__nombre__icontains=query
        ) | self.get_queryset().filter(
            mascota__cliente__usuario__apellido__icontains=query
        )

        serializer = HistoriaClinicaSerializer(historias.distinct(), many=True, context={'request': request})
        return Response(serializer.data)