from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from usuarios.models import Usuario, Rol
from usuarios.serializers.crud_serializer import (
    UsuarioListSerializer,
    UsuarioDetailSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    CambiarPasswordSerializer
)
from usuarios.serializers.user_serializer import RolSerializer
from usuarios.permissions import (
    IsAdministrador,
    CanManageUsers,
    IsOwnerOrAdmin
)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión completa de usuarios del sistema veterinario.
    
    Este ViewSet proporciona endpoints para todas las operaciones CRUD sobre usuarios,
    incluyendo funcionalidades especiales como activación/suspensión de cuentas,
    cambio de contraseña y búsqueda avanzada.

    Endpoints principales:
    - GET /usuarios/: Lista todos los usuarios (requiere autenticación)
    - POST /usuarios/: Crea nuevo usuario (requiere ser admin o recepcionista)
    - GET /usuarios/{id}/: Detalle de usuario específico
    - PUT/PATCH /usuarios/{id}/: Actualización de usuario
    - DELETE /usuarios/{id}/: Eliminación lógica de usuario

    Endpoints especiales:
    - POST /usuarios/{id}/activar/: Activa un usuario
    - POST /usuarios/{id}/suspender/: Suspende un usuario
    - POST /usuarios/{id}/cambiar_password/: Cambio de contraseña
    - GET /usuarios/me/: Información del usuario actual
    - GET /usuarios/buscar/: Búsqueda avanzada
    - GET /usuarios/estadisticas/: Estadísticas de usuarios

    Permisos por operación:
    - Listado/Detalle: Cualquier usuario autenticado
    - Creación: Administradores y Recepcionistas (estos últimos solo pueden crear clientes)
    - Actualización: El propio usuario o un Administrador
    - Eliminación: Solo Administradores
    - Activar/Suspender: Solo Administradores
    
    Notas de implementación:
    - Utiliza soft delete para preservar histórico
    - Soporta filtrado por estado y rol
    - Incluye búsqueda por username, email y nombre
    - Optimizado con select_related para perfiles y prefetch_related para roles
    """
    
    queryset = Usuario.objects.filter(deleted_at__isnull=True).select_related(
        'perfil_veterinario',
        'perfil_practicante',
        'perfil_cliente'
    ).prefetch_related('usuario_roles__rol')
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'usuario_roles__rol__nombre']
    search_fields = ['username', 'email', 'nombre', 'apellido']
    ordering_fields = ['created_at', 'nombre', 'apellido']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'list':
            return UsuarioListSerializer
        elif self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        return UsuarioDetailSerializer
    
    def get_permissions(self):
        """
        Define los permisos requeridos según la acción solicitada.

        Este método implementa una lógica de dos niveles para determinar permisos:
        1. Primero verifica si la acción tiene permisos específicos definidos
           via decorador @action(permission_classes=[...])
        2. Si no hay permisos específicos, aplica el mapeo predeterminado
           basado en el tipo de acción CRUD

        Returns:
            list: Lista de instancias de clases de permisos aplicables

        Notas de implementación:
        - Las acciones decoradas con @action tienen prioridad
        - Todas las acciones requieren autenticación base
        - Los permisos se acumulan (todos deben pasar)
        """
        # Si la acción tiene permisos definidos por el decorador @action,
        # respetarlos primero. El decorador añade el atributo
        # `permission_classes` al método correspondiente.
        action_name = getattr(self, 'action', None)
        if action_name:
            action_func = getattr(self, action_name, None)
            if action_func is not None and hasattr(action_func, 'permission_classes'):
                return [perm() for perm in getattr(action_func, 'permission_classes')]

        # Mapeo por acción por defecto (para las acciones CRUD principales)
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, CanManageUsers]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def perform_destroy(self, instance):
        """Implementa eliminación lógica (soft delete)."""
        instance.soft_delete()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Retorna la información del usuario autenticado."""
        serializer = UsuarioDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def cambiar_password(self, request, pk=None):
        """Permite al usuario cambiar su contraseña."""
        usuario = self.get_object()
        serializer = CambiarPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Cambiar la contraseña
            usuario.set_password(serializer.validated_data['password_nueva'])
            usuario.save()
            
            return Response(
                {'detail': 'Contraseña actualizada correctamente.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdministrador])
    def activar(self, request, pk=None):
        """
        Activa un usuario que se encuentra suspendido o inactivo.
        
        Este endpoint permite a los administradores reactivar cuentas de usuario
        que hayan sido suspendidas o desactivadas. Al activar un usuario:
        - Su estado cambia a 'activo'
        - Se establece is_active=True en su cuenta
        - Puede volver a iniciar sesión y acceder al sistema
        
        Permisos requeridos:
        - Usuario autenticado
        - Rol de administrador
        
        Returns:
            Response: Mensaje de éxito con estado HTTP 200
        """
        usuario = self.get_object()
        usuario.estado = 'activo'
        usuario.is_active = True
        usuario.save()
        
        return Response(
            {'detail': f'Usuario {usuario.username} activado correctamente.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdministrador])
    def suspender(self, request, pk=None):
        """
        Suspende temporalmente un usuario activo del sistema.
        
        Este endpoint permite a los administradores suspender cuentas de usuario
        por motivos administrativos o de seguridad. Al suspender un usuario:
        - Su estado cambia a 'suspendido'
        - Se establece is_active=False en su cuenta
        - No podrá iniciar sesión hasta ser reactivado
        
        Validaciones:
        - No permite la auto-suspensión (un admin no puede suspender su propia cuenta)
        - Requiere permisos de administrador
        
        Permisos requeridos:
        - Usuario autenticado
        - Rol de administrador
        
        Returns:
            Response: Mensaje de éxito con estado HTTP 200 o error 400 si intenta
                     auto-suspenderse
        """
        usuario = self.get_object()
        
        # No permitir auto-suspensión
        if usuario.id == request.user.id:
            return Response(
                {'detail': 'No puedes suspender tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario.estado = 'suspendido'
        usuario.is_active = False
        usuario.save()
        
        return Response(
            {'detail': f'Usuario {usuario.username} suspendido correctamente.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def buscar(self, request):
        """
        Realiza una búsqueda avanzada de usuarios con múltiples criterios.
        
        Este endpoint permite buscar usuarios combinando varios criterios:
        - Texto libre (busca en username, email, nombre, apellido)
        - Filtrado por rol específico
        - Filtrado por estado del usuario
        
        Parámetros de query:
        - q (str): Texto a buscar en campos de usuario
        - rol (str): Nombre del rol para filtrar
        - estado (str): Estado del usuario (default: 'activo')
        
        Características:
        - Búsqueda case-insensitive en todos los campos
        - Soporte para paginación de resultados
        - Excluye usuarios eliminados (soft-deleted)
        
        Returns:
            Response: Lista paginada de usuarios que coinciden con los criterios,
                     serializados con UsuarioListSerializer
        """
        query = request.query_params.get('q', '')
        rol = request.query_params.get('rol', None)
        estado = request.query_params.get('estado', 'activo')
        
        usuarios = self.queryset.filter(estado=estado)
        
        if query:
            usuarios = usuarios.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(nombre__icontains=query) |
                Q(apellido__icontains=query)
            )
        
        if rol:
            usuarios = usuarios.filter(usuario_roles__rol__nombre=rol)
        
        # Paginar resultados
        page = self.paginate_queryset(usuarios)
        if page is not None:
            serializer = UsuarioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales sobre los usuarios del sistema.
        
        Este endpoint proporciona un resumen estadístico que incluye:
        - Total de usuarios activos en el sistema
        - Total de usuarios por estado (activo/suspendido)
        - Distribución de usuarios por rol
        
        Las estadísticas excluyen usuarios eliminados (soft-deleted) y
        se calculan utilizando agregaciones de Django para eficiencia.
        
        Permisos:
        - Requiere autenticación
        - Acceso limitado a administradores
        
        Returns:
            Response: Diccionario con estadísticas agregadas:
                     - total_usuarios: int
                     - usuarios_activos: int
                     - usuarios_por_rol: dict[str, int]
        """
        if not request.user.usuario_roles.filter(rol__nombre='administrador').exists():
            return Response(
                {'detail': 'No tienes permisos para ver estadísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count
        
        stats = {
            'total_usuarios': Usuario.objects.filter(deleted_at__isnull=True).count(),
            'usuarios_activos': Usuario.objects.filter(
                estado='activo',
                deleted_at__isnull=True
            ).count(),
            'usuarios_por_rol': {}
        }
        
        # Contar usuarios por rol
        roles_count = Rol.objects.annotate(
            total=Count('rol_usuarios', filter=Q(
                rol_usuarios__usuario__deleted_at__isnull=True
            ))
        ).values('nombre', 'total')
        
        for rol in roles_count:
            stats['usuarios_por_rol'][rol['nombre']] = rol['total']
        
        return Response(stats)


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para gestionar la información de roles del sistema.
    
    Este ViewSet proporciona endpoints para consultar los roles disponibles
    y los usuarios asignados a cada rol. No permite modificaciones ya que
    los roles son predefinidos en el sistema.

    Endpoints disponibles:
    - GET /roles/: Lista todos los roles del sistema
    - GET /roles/{id}/: Obtiene detalles de un rol específico
    - GET /roles/{id}/usuarios/: Lista usuarios que tienen el rol especificado

    Notas de implementación:
    - Hereda de ReadOnlyModelViewSet para garantizar solo operaciones de lectura
    - Utiliza autenticación pero no requiere roles específicos para consultar
    - Los resultados de usuarios por rol excluyen usuarios eliminados (soft-deleted)
    """
    
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def usuarios(self, request, pk=None):
        """Lista los usuarios que tienen este rol."""
        rol = self.get_object()
        usuarios = Usuario.objects.filter(
            usuario_roles__rol=rol,
            deleted_at__isnull=True
        )
        
        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response(serializer.data)