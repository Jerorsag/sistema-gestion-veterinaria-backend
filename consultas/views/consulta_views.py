"""
view y endpoinds para gestionar Consultas Veterinarias.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from consultas.models import Consulta
from consultas.serializers.consulta_serializers import (
    ConsultaSerializer,
    ConsultaListSerializer,
    ConsultaDetailSerializer,
    ConsultaCreateSerializer,
    ConsultaUpdateSerializer
)


class ConsultaViewSet(viewsets.ModelViewSet):
    """
    gestión completa de consultas veterinarias.
    """
    queryset = Consulta.objects.all().select_related(
        'mascota',
        'veterinario'
    ).prefetch_related(
        'prescripciones',
        'examenes',
        'vacunas'
    )
    permission_classes = [IsAuthenticated]

    # Filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['mascota', 'veterinario', 'fecha_consulta']
    search_fields = ['mascota__nombre', 'diagnostico', 'descripcion_consulta']
    ordering_fields = ['fecha_consulta', 'created_at']
    ordering = ['-fecha_consulta']

    def get_serializer_class(self):
        """ Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return ConsultaListSerializer
        elif self.action == 'retrieve':
            return ConsultaDetailSerializer
        elif self.action == 'create':
            return ConsultaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsultaUpdateSerializer
        return ConsultaSerializer

    def get_queryset(self):
        """ Filtra las consultas según el rol del usuario."""
        user = self.request.user
        queryset = super().get_queryset()

        # Admins ven todo
        if user.is_staff:
            return queryset

        # Veterinarios y practicantes ven todo
        if hasattr(user, 'perfil_veterinario') or hasattr(user, 'perfil_practicante'):
            return queryset

        # Clientes solo ven sus mascotas
        if hasattr(user, 'perfil_cliente'):
            cliente = user.perfil_cliente
            return queryset.filter(mascota__cliente=cliente)

        # Usuario sin rol específico: sin acceso
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        """ Guarda la consulta asignando automáticamente el veterinario actual. """
        if hasattr(user, "perfil_veterinario") and user.perfil_veterinario is not None:
            serializer.save(veterinario=user.perfil_veterinario)
        else:
            raise ValidationError({"detail": "El usuario autenticado no tiene un perfil de veterinario asociado."})

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna todas las consultas de una mascota específica.
        """
        consultas = self.get_queryset().filter(mascota_id=mascota_id)

        # Verificar permisos: el propietario solo puede ver sus mascotas
        if consultas.exists():
            primera_consulta = consultas.first()
            if hasattr(request.user, 'perfil_cliente'):
                cliente = request.user.perfil_cliente
                if primera_consulta.mascota.cliente != cliente:
                    return Response(
                        {'detail': 'No tiene permiso para ver las consultas de esta mascota'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        serializer = ConsultaListSerializer(consultas, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='veterinario/(?P<veterinario_id>[^/.]+)')
    def por_veterinario(self, request, veterinario_id=None):
        """
        Retorna todas las consultas atendidas por un veterinario.
        """
        consultas = self.get_queryset().filter(veterinario_id=veterinario_id)
        serializer = ConsultaListSerializer(consultas, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def datos_personales(self, request, pk=None):
        """
        Retorna los datos personales de la mascota de esta consulta.
        """
        consulta = self.get_object()
        datos = consulta.get_datos_personales()
        return Response(datos)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de consultas.
        """
        from django.db.models import Count
        from django.db.models.functions import TruncMonth

        queryset = self.get_queryset()

        # Total de consultas
        total = queryset.count()

        # Consultas por mes
        por_mes = queryset.annotate(
            mes=TruncMonth('fecha_consulta')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('-mes')[:6]

        return Response({
            'total_consultas': total,
            'consultas_por_mes': list(por_mes)
        })
