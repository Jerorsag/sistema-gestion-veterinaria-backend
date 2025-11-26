from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound, ValidationError
from mascotas.models import Mascota, Especie, Raza
from mascotas.serializers.mascota_serializer import (
    MascotaSerializer,
    EspecieSerializer,
    RazaSerializer,
)
from mascotas.permissions import MascotaListPermission

"""
Vistas (API) para el módulo de mascotas.

Contiene las vistas para listar/crear mascotas y para obtener/actualizar/eliminar
una mascota concreta del cliente autenticado. Las vistas están protegidas y
requieren autenticación JWT (o el sistema de autenticación configurado en el proyecto).

Responden con mensajes amigables cuando no hay resultados o cuando el recurso
no pertenece al usuario autenticado.
"""

# Jeronimo Rodriguez - 11/03/2025

def _obtener_rol_usuario(usuario):
    """
    Obtiene el primer rol asociado al usuario.
    
    Args:
        usuario: Instancia de Usuario
        
    Returns:
        str: nombre del rol (ej: 'administrador', 'veterinario', 'recepcionista', 'cliente')
             o None si no tiene rol asignado
    """
    usuario_rol = usuario.usuario_roles.first()
    if usuario_rol:
        return usuario_rol.rol.nombre
    return None


class MascotaListCreateView(generics.ListCreateAPIView):
    """
    Endpoint para listar y registrar mascotas según el rol del usuario.
    
    - GET: Lista las mascotas según el rol:
        * ADMIN, VETERINARIO, RECEPCIONISTA: ven todas las mascotas.
        * CLIENTE: solo ve sus propias mascotas.
    - POST: Crea una nueva mascota asociada al cliente autenticado.
    """
    serializer_class = MascotaSerializer
    permission_classes = [MascotaListPermission]

    def get_queryset(self):
        """
        Filtra las mascotas según el rol del usuario autenticado.
        
        Reglas:
        - ADMIN, VETERINARIO, RECEPCIONISTA: retornan todas las mascotas.
        - CLIENTE: retornan solo las mascotas donde mascota.cliente.usuario == request.user.
        """
        usuario = self.request.user
        rol = _obtener_rol_usuario(usuario)
        
        # Roles que pueden ver todas las mascotas
        roles_acceso_total = ['administrador', 'veterinario', 'recepcionista']
        
        if rol in roles_acceso_total:
            # Acceso total a todas las mascotas
            return Mascota.objects.all()
        elif rol == 'cliente':
            # Solo mascotas del cliente autenticado
            return Mascota.objects.filter(cliente__usuario=usuario)
        else:
            # Si no tiene rol o rol desconocido, retorna vacío (seguridad por defecto)
            return Mascota.objects.none()

    def perform_create(self, serializer):
        """Guarda la mascota asociada al cliente."""
        serializer.save()

    def list(self, request, *args, **kwargs):
        """Retorna la lista de mascotas según el rol del usuario.

        Si no hay mascotas disponibles para el rol, devuelve un mensaje
        claro para facilitar la interpretación desde clientes como Postman
        o aplicaciones frontend.
        """
        conjunto_mascotas = self.get_queryset()

        if not conjunto_mascotas.exists():
            return Response({
                'message': 'No hay mascotas disponibles para tu rol.',
                'results': []
            }, status=status.HTTP_200_OK)

        return super().list(request, *args, **kwargs)


class EspecieListView(generics.ListAPIView):
    """
    Lista todas las especies disponibles para poblar selects en el frontend.
    """

    queryset = Especie.objects.all()
    serializer_class = EspecieSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class RazaListView(generics.ListAPIView):
    """
    Lista las razas filtradas por especie (parámetro obligatorio `especie`).
    """

    serializer_class = RazaSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        especie_param = self.request.query_params.get("especie")
        if especie_param is None:
            raise ValidationError({"especie": "El parámetro especie es obligatorio."})

        try:
            especie_id = int(especie_param)
        except (TypeError, ValueError):
            raise ValidationError({"especie": "Debe ser un ID numérico válido."})

        queryset = Raza.objects.filter(especie_id=especie_id)
        if not queryset.exists() and not Especie.objects.filter(id=especie_id).exists():
            raise NotFound(detail="La especie indicada no existe.")
        return queryset


class MascotaRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Permite consultar, actualizar o eliminar una mascota específica del cliente autenticado.
    """
    serializer_class = MascotaSerializer
    permission_classes = [MascotaListPermission]

    def get_queryset(self):
        return Mascota.objects.filter(cliente__usuario=self.request.user)

    def get_object(self):
        """Obtiene la mascota solicitada y maneja errores de forma amigable.

        - Valida que el parámetro de búsqueda esté presente en la URL.
        - Intenta recuperar la mascota solo dentro del conjunto del cliente
          autenticado (evita que un usuario acceda a mascotas de otro).
        - Si no se encuentra, lanza `NotFound` con un mensaje claro.
        """

        # Campo por el cual se hará la búsqueda (por defecto 'pk' o lo
        # que haya sido configurado en la vista).
        campo_busqueda = self.lookup_field
        argumento_url_busqueda = self.lookup_url_kwarg or campo_busqueda
        valor_busqueda = self.kwargs.get(argumento_url_busqueda)

        # Si no se proporcionó el valor en la URL, mostrar un error claro.
        if valor_busqueda is None:
            raise NotFound(detail='Se requiere el identificador de la mascota en la URL.')

        try:
            # Buscar la mascota únicamente dentro del queryset del cliente
            # autenticado para asegurar que el usuario no accede a recursos
            # de terceros.
            mascota = self.get_queryset().get(**{campo_busqueda: valor_busqueda})
        except Mascota.DoesNotExist:
            # Mensaje claro para el cliente indicando que no se encontró la mascota
            # o que no pertenece al usuario autenticado.
            raise NotFound(detail='Mascota no encontrada o no pertenece al usuario autenticado.')

        # Ejecutar los chequeos de permisos estándar (si se hubieran definido)
        self.check_object_permissions(self.request, mascota)
        return mascota

        # Ejecutar los chequeos de permisos estándar (si se hubieran definido)
        self.check_object_permissions(self.request, mascota)
        return mascota