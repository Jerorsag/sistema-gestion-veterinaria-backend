from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime

from .models import Cita, Servicio
from . import serializers
from . import services

print("--- CARGANDO CITAS/VIEWS.PY (NUEVA VERSIÓN) ---")

class CitaViewSet(viewsets.ModelViewSet):
    """
    API Endpoint para la gestión de Citas (CRUD y acciones).
    Utiliza una arquitectura de capas, delegando la lógica a 'services.py'
    y la validación/ejecución a 'serializers.py'.
    """
    queryset = Cita.objects.all().select_related(
        'mascota', 'veterinario', 'servicio'
    )
    permission_classes = [IsAuthenticated] # Solo usuarios logueados

    def get_serializer_class(self):
        """Define qué serializer usar según la acción (POST, GET, etc)."""
        if self.action == 'create':
            # Usa el serializer de ESCRITURA para crear
            return serializers.CrearCitaSerializer
        
        if self.action == 'reagendar':
            # Usa el serializer de ESCRITURA para reagendar
            return serializers.ReagendarCitaSerializer
        
        # Para 'list', 'retrieve', 'cancelar' usamos el de LECTURA
        return serializers.CitaSerializer

    def get_queryset(self):
        """
        Filtra las citas según el rol del usuario (RF-005).
        - Clientes: solo ven sus citas.
        - Veterinarios: solo ven las citas asignadas a ellos.
        - Recepcionistas/Admin: ven todas.
        """
        user = self.request.user
        roles = [r.rol.nombre for r in user.usuario_roles.all()]

        if 'cliente' in roles:
            return self.queryset.filter(mascota__cliente__usuario=user)

        if 'veterinario' in roles:
            return self.queryset.filter(veterinario=user)

        if 'recepcionista' in roles or 'administrador' in roles:
            return self.queryset.all()

        return Cita.objects.none()

    # --- MÉTODOS CRUD SOBRESCRITOS ---

    def create(self, request, *args, **kwargs):
        """
        (CORREGIDO) Sobrescribe el método POST (Crear).
        La vista ahora es "delgada": solo pasa el contexto y llama a .save().
        La lógica real está en CrearCitaSerializer.create().
        """
        # 1. Pasamos el 'context' (que incluye el 'request.user')
        serializer = self.get_serializer(
            data=request.data, 
            context={'request': request} # <-- Clave para obtener el usuario
        )
        
        # 2. Validamos
        serializer.is_valid(raise_exception=True) 
        
        # 3. Guardamos
        # Esto llama a 'CrearCitaSerializer.create()' automáticamente
        cita_creada = serializer.save()

        # 4. Devolvemos la respuesta con el serializer de LECTURA
        response_serializer = serializers.CitaSerializer(cita_creada)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # --- ACCIONES PERSONALIZADAS ---

    @action(detail=False, methods=['get'], url_path='disponibilidad')
    def disponibilidad(self, request):
        """
        Endpoint para devolver los horarios libres.
        """
        veterinario_id = request.query_params.get('veterinario_id')
        fecha_str = request.query_params.get('fecha')

        if not veterinario_id or not fecha_str:
            return Response(
                {"error": "Se requieren 'veterinario_id' y 'fecha' (YYYY-MM-DD)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # La vista (recepcionista) solo llama al gerente (services)
        horarios = services.obtener_horarios_disponibles(veterinario_id, fecha)
        return Response({"horarios_disponibles": horarios}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """
        (PERFECTO) Endpoint para cancelar una cita. (RF-007)
        Llama al servicio de cancelación (Patrón Command y State).
        """
        try:
            # La vista no cancela, le dice al servicio que cancele.
            cita = services.cancelar_cita(cita_id=pk, usuario=request.user)
            response_serializer = serializers.CitaSerializer(cita)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Manejamos los errores de lógica de negocio (ej. "ya está cancelada")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reagendar')
    def reagendar(self, request, pk=None):
        """
        (CORREGIDO) Endpoint para reagendar una cita. (RF-006)
        La vista es "delgada": pasa el contexto y llama a .save().
        La lógica real está en ReagendarCitaSerializer.update().
        """
        # 1. Obtenemos la cita que queremos actualizar
        cita_instancia = self.get_object()

        # 2. Pasamos la instancia y el contexto al serializer
        serializer = self.get_serializer(
            instance=cita_instancia,    # <-- La cita a actualizar
            data=request.data,
            context={'request': request} # <-- Para el usuario
        )
        
        # 3. Validamos
        serializer.is_valid(raise_exception=True)

        # 4. Guardamos
        # Esto llama a 'ReagendarCitaSerializer.update()' automáticamente
        cita_actualizada = serializer.save()

        # 5. Devolvemos la respuesta con el serializer de LECTURA
        response_serializer = serializers.CitaSerializer(cita_actualizada)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ServicioViewSet(viewsets.ModelViewSet):

    """ Endpoint"""
    queryset = Servicio.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):

        """
        Define qué serializer usar según la acción (POST, GET, etc).
        """
        # Si la acción es crear, actualizar o actualizar parcialmente
        if self.action in ['create', 'update', 'partial_update']:
            # Usa el serializer de ESCRITURA
            return serializers.ServicioWriteSerializer

        # Para todas las demás acciones (list, retrieve), usa el de LECTURA
        return serializers.ServicioSerializer
