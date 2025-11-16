"""
Serializers package - Centraliza todos los serializers del módulo usuarios.
Proporciona una interfaz unificada para importar serializers.
"""

# Auth serializers
from .auth import (
    CustomTokenObtainPairSerializer,
    RegistroSerializer,
    UsuarioPerfilSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordConfirmSerializer,
    RegistroPendienteSerializer,
)

# CRUD serializers
from .crud import (
    UsuarioListSerializer,
    UsuarioDetailSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    CambiarPasswordSerializer,
)

# Profile serializers
from .profiles import (
    RolSerializer,
    VeterinarioSerializer,
    PracticanteSerializer,
    ClienteSerializer,
)

__all__ = [
    # Auth
    'CustomTokenObtainPairSerializer',
    'RegistroSerializer',
    'UsuarioPerfilSerializer',
    'ResetPasswordRequestSerializer',
    'ResetPasswordConfirmSerializer',
    'RegistroPendienteSerializer',
    # CRUD
    'UsuarioListSerializer',
    'UsuarioDetailSerializer',
    'UsuarioCreateSerializer',
    'UsuarioUpdateSerializer',
    'CambiarPasswordSerializer',
    # Profiles
    'RolSerializer',
    'VeterinarioSerializer',
    'PracticanteSerializer',
    'ClienteSerializer',
]
