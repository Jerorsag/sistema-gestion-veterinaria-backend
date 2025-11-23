"""
Usuario Update Serializer - Actualización de usuarios y perfiles.
"""
from rest_framework import serializers
from usuarios.models import Usuario, Cliente, Veterinario, Practicante
from usuarios.serializers.profiles import VeterinarioSerializer, PracticanteSerializer, ClienteSerializer

class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualización de usuarios."""
    
    perfil_veterinario = VeterinarioSerializer(required=False)
    perfil_practicante = PracticanteSerializer(required=False)
    perfil_cliente = ClienteSerializer(required=False)
    
    class Meta:
        model = Usuario
        fields = [
            'email', 'nombre', 'apellido', 'estado',
            'perfil_veterinario', 'perfil_practicante', 'perfil_cliente'
        ]
    
    def update(self, instance, validated_data):
        """Actualiza el usuario y sus perfiles."""
        # Extraer datos de perfiles
        perfil_veterinario_data = validated_data.pop('perfil_veterinario', None)
        perfil_practicante_data = validated_data.pop('perfil_practicante', None)
        perfil_cliente_data = validated_data.pop('perfil_cliente', None)
        
        # Actualizar usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar perfiles
        if perfil_veterinario_data and hasattr(instance, 'perfil_veterinario'):
            for attr, value in perfil_veterinario_data.items():
                setattr(instance.perfil_veterinario, attr, value)
            instance.perfil_veterinario.save()
        
        if perfil_practicante_data and hasattr(instance, 'perfil_practicante'):
            for attr, value in perfil_practicante_data.items():
                setattr(instance.perfil_practicante, attr, value)
            instance.perfil_practicante.save()
        
        if perfil_cliente_data and hasattr(instance, 'perfil_cliente'):
            for attr, value in perfil_cliente_data.items():
                setattr(instance.perfil_cliente, attr, value)
            instance.perfil_cliente.save()
        
        return instance
