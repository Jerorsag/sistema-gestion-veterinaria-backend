"""
Patrón Chain of Responsibility aplicado al proceso de autenticación de usuarios.

Permite encadenar validaciones independientes para el login, desacoplando cada paso.
"""

class ManejadorLogin:
    """Interfaz base para los manejadores de la cadena."""
    def __init__(self, siguiente=None):
        self.siguiente = siguiente
    def manejar(self, request):
        if self.siguiente:
            return self.siguiente.manejar(request)
        return True

class ValidadorCredenciales(ManejadorLogin):
    """Valida usuario y contraseña usando el backend de autenticación de Django."""
    def manejar(self, request):
        from django.contrib.auth import authenticate

        username = request.get('usuario')
        password = request.get('password')

        user = authenticate(username=username, password=password)
        if user:
            # Attach authenticated user to the request dict for downstream handlers
            request['user_obj'] = user
            return super().manejar(request)
        return False

class ValidadorRol(ManejadorLogin):
    """Valida el rol del usuario (basado en el usuario autenticado si está disponible)."""
    def manejar(self, request):
        user = request.get('user_obj')
        if user and user.usuario_roles.exists():
            rol_nombre = user.usuario_roles.first().rol.nombre
            if rol_nombre in ['administrador', 'veterinario', 'cliente', 'practicante']:
                return super().manejar(request)
            return False

        # Fallback: permitir si el rol viene explícito y es válido
        rol = request.get('rol')
        if rol in ['administrador', 'veterinario', 'cliente', 'practicante']:
            return super().manejar(request)
        return False

class ValidadorEstado(ManejadorLogin):
    """Valida si el usuario está activo (usa el usuario autenticado si está disponible)."""
    def manejar(self, request):
        user = request.get('user_obj')
        if user:
            if getattr(user, 'estado', None) == 'activo':
                return super().manejar(request)
            return False

        # Fallback: usar el campo 'estado' del request
        if request.get('estado') == 'activo':
            return super().manejar(request)
        return False

# Ejemplo de uso:
def demo():
    # Configura la cadena de validadores
    cadena = ValidadorCredenciales(
        ValidadorRol(
            ValidadorEstado()
        )
    )
    request = {'usuario': 'admin', 'password': '1234', 'rol': 'administrador', 'estado': 'activo'}
    resultado = cadena.manejar(request)
    print('¿Login exitoso?', resultado)
