"""
Registro verificación serializers - Registro pendiente de verificación.
"""
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.utils import timezone
from usuarios.models import Usuario, UsuarioPendiente
from common.tasks import send_email


class RegistroPendienteSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar un usuario temporalmente (pendiente de verificación).
    Guarda los datos en UsuarioPendiente y envía el código por correo.
    """

    password_confirm = serializers.CharField(write_only=True)
    nombre = serializers.CharField(required=True)
    apellido = serializers.CharField(required=True)

    class Meta:
        model = UsuarioPendiente
        fields = ['email', 'password', 'password_confirm', 'nombre', 'apellido']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })

        if Usuario.objects.filter(email=attrs['email'].lower()).exists():
            raise serializers.ValidationError({
                'email': 'Este correo ya está registrado en el sistema.'
            })

        return attrs

    def create(self, validated_data):
        email = validated_data['email'].lower()
        password = make_password(validated_data.pop('password'))
        validated_data.pop('password_confirm')

        # Generar código de 6 dígitos
        verification_code = get_random_string(6, allowed_chars='0123456789')

        # Crear o actualizar el usuario pendiente
        usuario_pendiente, _ = UsuarioPendiente.objects.update_or_create(
            email=email,
            defaults={
                **validated_data,
                'password': password,
                'verification_code': verification_code,
                'created_at': timezone.now()
            }
        )

        # Enviar correo con el código (por consola)
        send_email(
            subject="Verifica tu cuenta - SGV",
            email_to=[email],
            html_template="emails/email_verification_template.html",
            context={
                "nombre": validated_data.get('nombre', ''),
                "code": verification_code
            }
        )

        return usuario_pendiente
