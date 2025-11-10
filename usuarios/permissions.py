from rest_framework import permissions

# Jerónimo Rodríguez - 06/11/2025
# Serializers para permisos segun Rol
class IsAdministrador(permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene el rol de administrador.

    Este permiso se usa para proteger acciones que solo deben ser accesibles
    para administradores del sistema, como la gestión de usuarios, activación
    y suspensión de cuentas.

    Ejemplos de uso:
        @action(detail=True, permission_classes=[IsAuthenticated, IsAdministrador])
        def activar(self, request, pk=None):
            ...

    Comportamiento:
        - Requiere que el usuario esté autenticado
        - Realiza una búsqueda case-insensitive del rol 'administrador'
        - Retorna False si el usuario no está autenticado o no tiene el rol
    """

    message = 'Solo los administradores pueden realizar esta acción.'

    def has_permission(self, request, view):
        """Verifica si el usuario tiene rol de administrador."""
        if not request.user or not request.user.is_authenticated:
            return False
        # Comprobar que el usuario tenga el rol 'administrador' (case-insensitive)
        return request.user.usuario_roles.filter(rol__nombre__iexact='administrador').exists()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que verifica si el usuario es el propietario del recurso o es administrador.

    Este permiso se utiliza para endpoints donde un usuario debe poder gestionar
    sus propios recursos, mientras que los administradores mantienen acceso
    completo a todos los recursos.

    Comportamiento:
        - Permite acceso si el usuario es administrador
        - Permite acceso si el usuario es el propietario del objeto
        - Deniega acceso en cualquier otro caso
    
    Nota: 
        Este permiso asume que el objeto tiene un ID que puede compararse
        con el ID del usuario autenticado.
    """
    
    message = 'Solo puedes editar tu propio perfil o ser administrador.'
    
    def has_object_permission(self, request, view, obj):
        """Verifica si el usuario es el dueño del objeto o administrador."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si es administrador, tiene acceso total
        is_admin = request.user.usuario_roles.filter(rol__nombre__iexact='administrador').exists()
        if is_admin:
            return True
        
        # Si es el dueño del objeto
        if isinstance(obj, request.user.__class__):
            return obj.id == request.user.id
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permite lectura a todos pero escritura solo a administradores."""
    
    def has_permission(self, request, view):
        """Permite GET, HEAD, OPTIONS a todos; otros métodos solo a admins."""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.usuario_roles.filter(
            rol__nombre__iexact='administrador'
        ).exists()


class CanManageUsers(permissions.BasePermission):
    """Permiso para administradores y recepcionistas que pueden gestionar usuarios."""
    
    message = 'No tienes permisos para gestionar usuarios.'
    
    def has_permission(self, request, view):
        """Verifica si puede gestionar usuarios."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores tienen acceso completo
        is_admin = request.user.usuario_roles.filter(rol__nombre__iexact='administrador').exists()
        if is_admin:
            return True
        
        # Recepcionistas solo pueden crear clientes (POST)
        is_recep = request.user.usuario_roles.filter(rol__nombre__iexact='recepcionista').exists()
        if is_recep and request.method == 'POST':
            return True
        
        return False


class HasRolePermission(permissions.BasePermission):
    """
    Permiso configurable que verifica si un usuario tiene al menos uno
    de los roles especificados.

    Este permiso es flexible y puede utilizarse para proteger endpoints
    que requieren roles específicos o combinaciones de roles.

    Args:
        allowed_roles (list): Lista de nombres de roles permitidos.
                            Los nombres son case-insensitive.

    Ejemplo de uso:
        @action(
            detail=True,
            permission_classes=[IsAuthenticated, HasRolePermission(['veterinario', 'practicante'])]
        )
        def atender_mascota(self, request, pk=None):
            ...

    Notas de implementación:
        - Los nombres de roles se normalizan a minúsculas para comparación
        - La validación es case-insensitive para mayor robustez
        - Si el usuario tiene múltiples roles, basta con que uno coincida
    """
    message = 'No tienes el rol requerido para realizar esta acción.'

    def __init__(self, allowed_roles):
        """
        Args:
            allowed_roles: Lista de roles permitidos
        """
        self.allowed_roles = allowed_roles
        super().__init__()
    
    def has_permission(self, request, view):
        """Verifica si el usuario tiene alguno de los roles permitidos."""
        if not request.user or not request.user.is_authenticated:
            return False
        # Retorna True si el usuario tiene alguno de los roles en allowed_roles
        # Hacemos comparación case-insensitive para mayor robustez:
        allowed_normalized = [r.lower() for r in self.allowed_roles]
        return request.user.usuario_roles.filter(rol__nombre__in=allowed_normalized).exists()


class IsVeterinario(permissions.BasePermission):
    """Permiso para verificar si el usuario es veterinario."""
    
    message = 'Solo los veterinarios pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        """Verifica si el usuario tiene rol de veterinario."""
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.usuario_roles.filter(rol__nombre__iexact='veterinario').exists()


class IsRecepcionista(permissions.BasePermission):
    """Permiso para verificar si el usuario es recepcionista."""
    
    message = 'Solo los recepcionistas pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        """Verifica si el usuario tiene rol de recepcionista."""
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.usuario_roles.filter(rol__nombre__iexact='recepcionista').exists()


class IsCliente(permissions.BasePermission):
    """Permiso para verificar si el usuario es cliente."""
    
    message = 'Solo los clientes pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        """Verifica si el usuario tiene rol de cliente."""
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.usuario_roles.filter(rol__nombre__iexact='cliente').exists()