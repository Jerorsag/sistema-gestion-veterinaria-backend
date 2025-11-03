from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from mascotas.models import Mascota
from mascotas.serializers.mascota_serializer import MascotaSerializer
from rest_framework.exceptions import NotFound
"""
Vistas (API) para el módulo de mascotas.

Contiene las vistas para listar/crear mascotas y para obtener/actualizar/eliminar
una mascota concreta del cliente autenticado. Las vistas están protegidas y
requieren autenticación JWT (o el sistema de autenticación configurado en el proyecto).

Responden con mensajes amigables cuando no hay resultados o cuando el recurso
no pertenece al usuario autenticado.
"""

# Jeronimo Rodriguez - 11/03/2025

class MascotaListCreateView(generics.ListCreateAPIView):
    """
    Endpoint para listar y registrar mascotas del cliente autenticado.
    - GET: Lista las mascotas del cliente.
    - POST: Crea una nueva mascota asociada al cliente autenticado.
    """
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Devuelve solo las mascotas del cliente autenticado."""
        return Mascota.objects.filter(cliente__usuario=self.request.user)

    def perform_create(self, serializer):
        """Guarda la mascota asociada al cliente."""
        serializer.save()

    def list(self, request, *args, **kwargs):
        """Retorna la lista de mascotas para el cliente autenticado.

        Si el cliente no tiene mascotas registradas devuelve un mensaje
        claro en la respuesta para facilitar la interpretación desde clientes
        como Postman o aplicaciones frontend.

        Nota: si el proyecto tiene paginación activada, la estructura
        de la respuesta puede incluir `results`; aquí devolvemos una
        forma consistente con `results: []` cuando no hay datos.
        """
        conjunto_mascotas = self.get_queryset()

        # Si no existen mascotas para el cliente autenticado, devolvemos
        # una respuesta amigable en lugar de una lista vacía sin contexto.
        if not conjunto_mascotas.exists():
            return Response({
                'message': 'No tienes mascotas registradas.',
                'results': []
            }, status=status.HTTP_200_OK)

        # Si hay mascotas, delegamos en la implementación por defecto de DRF
        # para soportar paginación y serialización estándar.
        return super().list(request, *args, **kwargs)


class MascotaRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Permite consultar, actualizar o eliminar una mascota específica del cliente autenticado.
    """
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]

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