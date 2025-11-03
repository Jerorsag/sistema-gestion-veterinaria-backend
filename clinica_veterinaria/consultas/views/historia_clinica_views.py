"""
view y endpoinds para Historia Clínica Consolidada.

Endpoints:
- GET /api/historias-clinicas/ - Listar historias (filtradas por rol)
- GET /api/historias-clinicas/{id}/ - Ver historia completa de una mascota
- GET /api/historias-clinicas/mascota/{mascota_id}/ - Por ID de mascota
- GET /api/historias-clinicas/{id}/ultima-consulta/ - Solo última consulta
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from clinica_veterinaria.consultas.models import HistoriaClinica
from clinica_veterinaria.consultas.serializers.historia_clinica_serializers import (
    HistoriaClinicaSerializer,
    HistoriaClinicaDetalleSerializer,
    UltimaConsultaSerializer
)


class HistoriaClinicaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    para visualizar historias clínicas consolidadas.
    """

    queryset = HistoriaClinica.objects.all().select_related(
        'mascota',
        'mascota__propietario'
    )
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['mascota', 'estado_vacunacion_actual']
    search_fields = ['mascota__nombre', 'mascota__propietario__first_name', 'mascota__propietario__last_name']

    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'retrieve' or self.action == 'por_mascota':
            return HistoriaClinicaDetalleSerializer
        elif self.action == 'ultima_consulta':
            return UltimaConsultaSerializer
        return HistoriaClinicaSerializer

    def get_queryset(self):
        """
        Filtra historias según el rol del usuario.
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Si es propietario, solo sus mascotas
        if hasattr(user, 'mascotas'):
            return queryset.filter(mascota__propietario=user)

        # Veterinarios, Admin y Recepcionistas ven todo
        return queryset

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna la historia clínica de una mascota por su ID.
        GET /api/historias-clinicas/mascota/{mascota_id}/
        """
        try:
            historia = self.get_queryset().get(mascota_id=mascota_id)
        except HistoriaClinica.DoesNotExist:
            return Response(
                {'detail': 'Esta mascota no tiene historia clínica registrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(historia)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='ultima-consulta')
    def ultima_consulta(self, request, pk=None):
        """
        Retorna solo la última consulta de la historia clínica.
        GET /api/historias-clinicas/{id}/ultima-consulta/
        """
        historia = self.get_object()
        serializer = UltimaConsultaSerializer(historia, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Retorna un resumen ejecutivo de la historia clínica.

        GET /api/historias-clinicas/{id}/resumen/
        Incluye:Total de consultas, Última consulta,Estado de vacunación,Medicamentos más frecuentes, Diagnósticos recurrentes
        """
        historia = self.get_object()

        # Diagnósticos recurrentes
        from django.db.models import Count
        diagnosticos = historia.mascota.consultas.values('diagnostico').annotate(
            veces=Count('id')
        ).order_by('-veces')[:5]

        return Response({
            'mascota': {
                'nombre': historia.mascota.nombre,
                'edad': historia.mascota.calcular_edad(),
            },
            'total_consultas': historia.get_total_consultas(),
            'ultima_consulta': {
                'fecha': historia.get_ultima_consulta().fecha_consulta if historia.get_ultima_consulta() else None,
                'diagnostico': historia.get_ultima_consulta().diagnostico if historia.get_ultima_consulta() else None,
            },
            'estado_vacunacion': historia.get_estado_vacunacion_actual_display(),
            'medicamentos_frecuentes': list(historia.get_medicamentos_frecuentes(limit=5)),
            'diagnosticos_recurrentes': list(diagnosticos),
        })

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda avanzada de historias clínicas.
        GET /api/historias-clinicas/buscar/?q=Max
        Busca por:Nombre de mascota, Nombre de propietario
        """
        query = request.query_params.get('q', '')

        if not query:
            return Response(
                {'detail': 'Debe proporcionar un término de búsqueda'},
                status=status.HTTP_400_BAD_REQUEST
            )

        historias = self.get_queryset().filter(
            mascota__nombre__icontains=query
        ) | self.get_queryset().filter(
            mascota__propietario__first_name__icontains=query
        ) | self.get_queryset().filter(
            mascota__propietario__last_name__icontains=query
        )

        serializer = HistoriaClinicaSerializer(historias, many=True, context={'request': request})
        return Response(serializer.data)