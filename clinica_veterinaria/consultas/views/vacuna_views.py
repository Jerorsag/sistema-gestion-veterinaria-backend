"""
 viewa y endpoinds para gestionar Historial de Vacunas.

Endpoints:
- GET /api/vacunas/ - Listar registros de vacunas
- GET /api/vacunas/{id}/ - Ver detalle
- POST /api/vacunas/ - Crear registro individual
- PUT /api/vacunas/{id}/ - Actualizar registro
- DELETE /api/vacunas/{id}/ - Eliminar registro
- GET /api/vacunas/mascota/{mascota_id}/ - Por mascota
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from clinica_veterinaria.consultas.models import HistorialVacuna
from clinica_veterinaria.consultas.serializers.vacuna_serializers import (
    HistorialVacunaSerializer,
    HistorialVacunaCreateSerializer
)


class HistorialVacunaViewSet(viewsets.ModelViewSet):
    """
    para gestión del historial de vacunas.
    """

    queryset = HistorialVacuna.objects.all().select_related('consulta')
    serializer_class = HistorialVacunaSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Retorna el serializer apropiado"""
        if self.action == 'create':
            return HistorialVacunaCreateSerializer
        return HistorialVacunaSerializer

    def get_queryset(self):
        """Filtra registros según permisos del usuario"""
        user = self.request.user
        queryset = super().get_queryset()

        # Si es propietario, solo registros de sus mascotas
        if hasattr(user, 'mascotas'):
            return queryset.filter(consulta__mascota__propietario=user)

        return queryset

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna el historial de vacunación de una mascota.
        GET /api/vacunas/mascota/{mascota_id}/ Ordenado cronológicamente (más reciente primero).
        """
        vacunas = self.get_queryset().filter(consulta__mascota_id=mascota_id)
        serializer = self.get_serializer(vacunas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='consulta/(?P<consulta_id>[^/.]+)')
    def por_consulta(self, request, consulta_id=None):
        """
        Retorna el registro de vacunas de una consulta específica.
        GET /api/vacunas/consulta/{consulta_id}/
        """
        vacunas = self.get_queryset().filter(consulta_id=consulta_id)
        serializer = self.get_serializer(vacunas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas_vacunacion(self, request):
        """
        Retorna estadísticas del estado de vacunación.
        GET /api/vacunas/estadisticas-vacunacion/
        Incluye:
        - Total por estado (Al día, Pendiente, En proceso, Ninguna)
        - Vacunas más aplicadas
        """
        from django.db.models import Count

        por_estado = self.get_queryset().values('estado').annotate(
            total=Count('id')
        )

        return Response({
            'por_estado': list(por_estado),
        })