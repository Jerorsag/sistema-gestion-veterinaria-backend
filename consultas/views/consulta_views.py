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
from consultas.signals import consulta_consentimiento_signal
from consultas.serializers.consulta_serializers import (
    ConsultaSerializer,
    ConsultaListSerializer,
    ConsultaDetailSerializer,
    ConsultaCreateSerializer
)
from consultas.services.consulta_service import (
    crear_consulta,
    obtener_datos_personales
)
from consultas.services.consentimiento_service import enviar_consentimiento
from consultas.services.consulta_estadisticas_service import (
    estadisticas_consultas
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
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'list':
            return ConsultaListSerializer
        elif self.action == 'retrieve':
            return ConsultaDetailSerializer
        elif self.action == 'create':
            return ConsultaCreateSerializer
        return ConsultaSerializer

    def get_queryset(self):
        """
        Filtra las consultas según el rol del usuario.
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Si es propietario (cliente), solo sus mascotas
        if hasattr(user, 'mascotas'):
            return queryset.filter(mascota__propietario=user)

        # Si es veterinario, puede ver todas (o solo las suyas según regla de negocio)
        # Por ahora permitimos que vea todas
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        """
        Guarda la consulta asignando automáticamente el veterinario actual.
        """
        if hasattr(user, "perfil_veterinario") and user.perfil_veterinario is not None:
            serializer.save(veterinario=user.perfil_veterinario)
        else:
            raise ValidationError({"detail": "El usuario autenticado no tiene un perfil de veterinario asociado."})

    @action(detail=True, methods=['post'], url_path='enviar-consentimiento')
    def enviar_consentimiento_view(self, request, pk=None):
        consulta = self.get_object()

        enviar_consentimiento(consulta)
        return Response({"detail": "Solicitud enviada correctamente"}, status=200)

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna todas las consultas de una mascota específica.
        """
        consultas = self.get_queryset().filter(mascota_id=mascota_id)

        # Verificar permisos: el propietario solo puede ver sus mascotas
        if consultas.exists():
            primera_consulta = consultas.first()
            if hasattr(request.user, 'mascotas'):
                if primera_consulta.mascota.propietario != request.user:
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
        consulta = self.get_object()
        datos = obtener_datos_personales(consulta)
        return Response(datos)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        data = estadisticas_consultas(self.get_queryset())
        return Response(data)