from rest_framework.permissions import BasePermission
from usuarios.models import UsuarioRol


class MascotaListPermission(BasePermission):
    """
    Permiso personalizado para controlar el acceso a la lista de mascotas.

    Reglas:
    - Solo usuarios autenticados pueden acceder.
    - La visibilidad de mascotas depende del rol del usuario:
        * ADMIN, VETERINARIO, RECEPCIONISTA: ven todas las mascotas.
        * CLIENTE: solo ve sus propias mascotas (filtrado en queryset).
    """

    message = "No tienes permisos para acceder a este recurso."

    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        
        La lógica de filtrado por rol se ejecuta en view.get_queryset().
        """
        return request.user and request.user.is_authenticated
