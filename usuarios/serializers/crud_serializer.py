from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from usuarios.models import Veterinario, Practicante, Cliente, Usuario, Rol, UsuarioRol
from usuarios.serializers.user_serializer import RolSerializer, VeterinarioSerializer, PracticanteSerializer, ClienteSerializer

# Jerónimo Rodríguez - 06/11/2025
# Serializers para operaciones CRUD de usuarios en el sistema veterinario
class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listar usuarios en el sistema.
    
    Este serializer proporciona una vista simplificada de usuarios para listados,
    incluyendo información básica y roles, optimizado para rendimiento en
    colecciones grandes.
    
    Campos personalizados:
    - roles: Lista de nombres de roles (usando display names)
    - nombre_completo: Nombre y apellido concatenados
    
    Notas de implementación:
    - Usa select_related para optimizar queries de roles
    - Excluye campos innecesarios para listados (perfiles, timestamps)
    - Proporciona solo la información esencial para listados
    """
    
    roles = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'nombre', 'apellido',
            'nombre_completo', 'estado', 'roles', 'created_at'
        ]
    
    def get_roles(self, obj):
        """Obtiene los roles del usuario."""
        return [ur.rol.get_nombre_display() for ur in obj.usuario_roles.select_related('rol')]
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo."""
        return obj.get_full_name()


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para mostrar todos los detalles de un usuario.
    
    Este serializer incluye toda la información disponible de un usuario,
    incluyendo sus perfiles específicos (veterinario, practicante, cliente)
    y sus roles asignados.
    
    Características:
    - Incluye timestamps de auditoría (created_at, updated_at)
    - Expone todos los perfiles asociados como read-only
    - Proporciona información detallada de roles
    
    Notas de implementación:
    - Los perfiles son read_only para prevenir modificación directa
    - Los campos de auditoría y el ID son read_only por seguridad
    - Utiliza RolSerializer para información detallada de roles
    """
    
    roles = serializers.SerializerMethodField()
    perfil_veterinario = VeterinarioSerializer(read_only=True)
    perfil_practicante = PracticanteSerializer(read_only=True)
    perfil_cliente = ClienteSerializer(read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'nombre', 'apellido',
            'estado', 'roles', 'created_at', 'updated_at',
            'perfil_veterinario', 'perfil_practicante', 'perfil_cliente'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles(self, obj):
        """Obtiene información detallada de los roles."""
        return RolSerializer(
            [ur.rol for ur in obj.usuario_roles.select_related('rol')],
            many=True
        ).data


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de usuarios."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    roles = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        write_only=True
    )
    
    # Campos de perfil según el rol
    perfil_veterinario = VeterinarioSerializer(required=False)
    perfil_practicante = PracticanteSerializer(required=False)
    perfil_cliente = ClienteSerializer(required=False)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'nombre', 'apellido', 'estado', 'roles',
            'perfil_veterinario', 'perfil_practicante', 'perfil_cliente'
        ]
    
    def validate(self, attrs):
        """Validaciones personalizadas."""
        # Validar contraseñas coincidentes
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        
        # Validar roles existentes
        roles_input = attrs.get('roles', [])
        roles_validos = dict(Rol.ROLES_DISPONIBLES).keys()
        
        for rol_nombre in roles_input:
            if rol_nombre not in roles_validos:
                raise serializers.ValidationError({
                    'roles': f'El rol "{rol_nombre}" no es válido.'
                })
        
        # Validar que veterinarios tengan perfil
        if 'veterinario' in roles_input and 'perfil_veterinario' not in attrs:
            raise serializers.ValidationError({
                'perfil_veterinario': 'Los veterinarios deben tener perfil completo.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crea el usuario y sus perfiles asociados."""
        # Extraer datos de perfiles
        roles_data = validated_data.pop('roles')
        perfil_veterinario_data = validated_data.pop('perfil_veterinario', None)
        perfil_practicante_data = validated_data.pop('perfil_practicante', None)
        perfil_cliente_data = validated_data.pop('perfil_cliente', None)
        validated_data.pop('password_confirm')
        
        # Crear usuario
        password = validated_data.pop('password')
        usuario = Usuario.objects.create_user(password=password, **validated_data)
        
        # Asignar roles
        for rol_nombre in roles_data:
            rol, _ = Rol.objects.get_or_create(nombre=rol_nombre)
            UsuarioRol.objects.create(usuario=usuario, rol=rol)
        
        # Crear perfiles según el rol
        if perfil_veterinario_data:
            Veterinario.objects.create(usuario=usuario, **perfil_veterinario_data)
        
        if perfil_practicante_data:
            Practicante.objects.create(usuario=usuario, **perfil_practicante_data)
        
        if perfil_cliente_data:
            Cliente.objects.create(usuario=usuario, **perfil_cliente_data)
        
        return usuario


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
    

class CambiarPasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña."""
    
    password_actual = serializers.CharField(required=True, write_only=True)
    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    password_nueva_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validar contraseñas."""
        if attrs['password_nueva'] != attrs['password_nueva_confirm']:
            raise serializers.ValidationError({
                'password_nueva_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def validate_password_actual(self, value):
        """Validar que la contraseña actual sea correcta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value