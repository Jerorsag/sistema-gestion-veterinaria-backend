"""
 viewa y endpoinds para gestionar Historial de Vacunas.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from consultas.models import HistorialVacuna
from consultas.serializers.vacuna_serializers import (
    HistorialVacunaSerializer,
    HistorialVacunaListSerializer
)


class HistorialVacunaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    para gestión del historial de vacunas.
    """

    queryset = HistorialVacuna.objects.all().select_related('consulta')
    serializer_class = HistorialVacunaSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['consulta', 'estado']
    search_fields = ['vacunas_descripcion']
    ordering_fields = ['fecha_registro']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """Retorna el serializer apropiado"""
        if self.action == 'list':
            return HistorialVacunaListSerializer
        return HistorialVacunaSerializer

    def get_queryset(self):
        """
        Filtra registros según permisos del usuario.
        Prioridad: Admin > Veterinario/Practicante > Cliente
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Admins ven todo
        if user.is_staff:
            return queryset

        # Veterinarios y practicantes ven todo
        if hasattr(user, 'perfil_veterinario') or hasattr(user, 'perfil_practicante'):
            return queryset

        #Clientes solo ven registros de sus mascotas
        if hasattr(user, 'perfil_cliente'):
            cliente = user.perfil_cliente
            return queryset.filter(consulta__mascota__cliente=cliente)

        # Sin rol: sin acceso
        return queryset.none()

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna el historial de vacunación de una mascota.
        """
        vacunas = self.get_queryset().filter(consulta__mascota_id=mascota_id)
        serializer = self.get_serializer(vacunas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='consulta/(?P<consulta_id>[^/.]+)')
    def por_consulta(self, request, consulta_id=None):
        """
        Retorna el registro de vacunas de una consulta específica.
        """
        vacunas = self.get_queryset().filter(consulta_id=consulta_id)
        serializer = self.get_serializer(vacunas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas_vacunacion(self, request):
        """
        Retorna estadísticas del estado de vacunación.
        """
        from django.db.models import Count

        por_estado = self.get_queryset().values('estado').annotate(
            total=Count('id')
        )

        return Response({
            'por_estado': list(por_estado),
        })