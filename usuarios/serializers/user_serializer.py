from rest_framework import serializers
from usuarios.models import Veterinario, Practicante, Cliente, Usuario, Rol

# Jerónimo Rodríguez - 06/11/2025
# Serializers para el modelo Rol
class RolSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Rol."""
    
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']
        read_only_fields = ['id']

# Jerónimo Rodríguez - 30/10/2025
# Serializers de perfiles específicos del sistema
class VeterinarioSerializer(serializers.ModelSerializer):
    """
    Serializer para representar y validar los datos del perfil de un Veterinario.

    Este serializer se utiliza para mostrar o editar información
    complementaria de usuarios con rol 'veterinario'.
    
    Incluye validación personalizada del campo 'licencia' para garantizar
    que no existan duplicados en la base de datos.
    """
    
    class Meta:
        model = Veterinario
        fields = ['licencia', 'especialidad', 'horario']
    
    def validate_licencia(self, value):
        """
        Valida que el número de licencia veterinaria sea único en el sistema.

        - Permite mantener la licencia existente si el objeto ya está instanciado.
        - Lanza un ValidationError si el número de licencia ya se encuentra
          registrado en otro perfil.

        Retorna:
            str: valor validado de la licencia si no hay conflictos.
        """
        if self.instance and self.instance.licencia == value:
            return value
        
        if Veterinario.objects.filter(licencia=value).exists():
            raise serializers.ValidationError("Esta licencia ya está registrada.")
        return value


class PracticanteSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de un usuario con rol 'practicante'.

    Incluye la información del tutor veterinario asignado, universidad
    de procedencia y el período de práctica profesional.

    El campo `tutor_veterinario_nombre` se obtiene dinámicamente mediante
    `SerializerMethodField` para mostrar el nombre legible del tutor.
    """
    
    tutor_veterinario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Practicante
        fields = ['tutor_veterinario', 'tutor_veterinario_nombre', 'universidad', 'periodo_practica']
    
    def get_tutor_veterinario_nombre(self, obj):
        """
        Retorna el nombre completo del tutor veterinario si existe.

        Si el practicante no tiene tutor asignado, retorna `None`.

        Args:
            obj (Practicante): instancia del modelo Practicante.
        Returns:
            str | None: nombre del tutor o None si no existe.
        """
        if obj.tutor_veterinario:
            return str(obj.tutor_veterinario)
        return None


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Cliente del sistema.

    Permite serializar la información complementaria del cliente,
    como su número telefónico y dirección.

    Es utilizado para mostrar o actualizar datos de contacto
    asociados a un usuario con rol 'cliente'.
    """
    
    class Meta:
        model = Cliente
        fields = ['telefono', 'direccion']