"""
view y endpoinds para gestionar Consultas Veterinarias.
Endpoints:
- POST /api/consultas/ - Crear consulta (Formulario "Crear Historias Clínicas")
- GET /api/consultas/ - Listar consultas (Ver consultas que se han realizado)
- GET /api/consultas/{id}/ - Ver detalle de consulta (para la vista del propietario por si quiere ver los detalles de la historia clinica)
- PUT /api/consultas/{id}/ - Actualizar consulta (El veterinario puede realizar actualizaciones de una historia especifica)
- DELETE /api/consultas/{id}/ - Eliminar consulta (Se realizo una consulta equivocada el veterinario la puede eliminar)
- GET /api/consultas/mascota/{mascota_id}/ - Consultas de una mascota específica (muestra las consultas especificas de una mascota)

"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from clinica_veterinaria.consultas.models import Consulta
from clinica_veterinaria.consultas.serializers.consulta_serializers import (
    ConsultaSerializer,
    ConsultaListSerializer,
    ConsultaDetailSerializer,
    ConsultaCreateSerializer
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
        Permisos:
        Propietarios: Solo consultas de sus mascotas
        Veterinarios: Todas las consultas que atendieron
        Admin/Recepcionistas: Todas las consultas
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
        """
        Guarda la consulta asignando automáticamente el veterinario actual.
        - Crear/actualizar la HistoriaClinica
        - Actualizar el estado de vacunación de la mascota
        - Descontar el inventario ( Prescripcion)
        """
        serializer.save(veterinario=self.request.user)

    @action(detail=False, methods=['get'], url_path='mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Retorna todas las consultas de una mascota específica.
        GET /api/consultas/mascota/{mascota_id}/
        Usado para ver el historial completo de consultas de una mascota.
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
        GET /api/consultas/veterinario/{veterinario_id}/
        Usado para reportes y análisis de desempeño.
        """
        consultas = self.get_queryset().filter(veterinario_id=veterinario_id)
        serializer = ConsultaListSerializer(consultas, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def datos_personales(self, request, pk=None):
        """
        Retorna los datos personales de la mascota de esta consulta.
        GET /api/consultas/{id}/datos_personales/
        Útil para verificar los datos auto-rellenados en el formulario.
        """
        consulta = self.get_object()
        datos = consulta.get_datos_personales()
        return Response(datos)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de consultas.
        GET /api/consultas/estadisticas/
        Incluye: Total de consultas, Consultas por mes, Diagnósticos más frecuentes
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

        # Diagnósticos más frecuentes
        diagnosticos_frecuentes = queryset.values('diagnostico').annotate(
            total=Count('id')
        ).order_by('-total')[:10]

        return Response({
            'total_consultas': total,
            'consultas_por_mes': list(por_mes),
            'diagnosticos_frecuentes': list(diagnosticos_frecuentes),
        })