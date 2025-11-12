"""
Views y endpoinds para gestionar Exámenes médicos.
"""
from django_filters.rest_framework import DjangoFilterBackend
from pytest_django.fixtures import client
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from consultas.models import Examen
from consultas.serializers.examen_serializers import ExamenSerializer, ExamenListSerializer


class ExamenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    para gestión de exámenes médicos.
    """
    queryset = Examen.objects.all().select_related('consulta')
    serializer_class = ExamenSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['consulta', 'tipo_examen']
    search_fields = ['tipo_examen', 'descripcion']
    ordering_fields = ['fecha_orden']
    ordering = ['-fecha_orden']

    def get_serializer_class(self):
        """Retorna el serializer apropiado"""
        if self.action == 'list':
            return ExamenListSerializer
        return ExamenSerializer

    def get_queryset(self):
        """ Filtra exámenes según permisos del usuario."""
        user = self.request.user
        queryset = super().get_queryset()

        #Admins ven todo
        if user.is_staff:
            return queryset

        #Veterinarios y practicantes ven todo
        if hasattr(user, 'perfil_veterinario') or hasattr(user, 'perfil_practicante'):
            return queryset

        #Clientes solo ven exámenes de sus mascotas
        if hasattr(user, 'perfil_cliente'):
            cliente = user.perfil_cliente
            return queryset.filter(consulta__mascota__cliente=cliente)

        # Sin rol: sin acceso
        return queryset.none()

    @action(detail=False, methods=['get'], url_path='consulta/(?P<consulta_id>[^/.]+)')
    def por_consulta(self, request, consulta_id=None):
        """Retorna todos los exámenes de una consulta."""
        examenes = self.get_queryset().filter(consulta_id=consulta_id)
        serializer = self.get_serializer(examenes, many=True)
        return Response(serializer.data)