from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('nombre', models.CharField(max_length=100)),
                ('apellido', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('estado', models.CharField(default='activo', max_length=20)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('intentos_fallidos', models.IntegerField(default=0)),
                ('bloqueado_hasta', models.DateTimeField(blank=True, null=True)),
            ],
            options={'db_table': 'usuarios'},
        ),

        migrations.CreateModel(
            name='UsuarioPendiente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('verification_code', models.CharField(max_length=255)),
            ],
            options={'db_table': 'usuarios_pendientes'},
        ),

        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=50, unique=True)),
                ('descripcion', models.TextField(blank=True)),
            ],
            options={'db_table': 'roles'},
        ),

        migrations.CreateModel(
            name='UsuarioRol',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuario_roles', to='usuarios.usuario')),
                ('rol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rol_usuarios', to='usuarios.rol')),
            ],
            options={'db_table': 'usuario_roles'},
        ),

        migrations.CreateModel(
            name='Veterinario',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_veterinario', to='usuarios.usuario')),
                ('licencia', models.CharField(max_length=50, unique=True)),
                ('especialidad', models.CharField(max_length=100, blank=True)),
                ('horario', models.TextField(blank=True)),
            ],
            options={'db_table': 'veterinarios'},
        ),

        migrations.CreateModel(
            name='Practicante',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_practicante', to='usuarios.usuario')),
                ('tutor_veterinario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='practicantes', to='usuarios.veterinario')),
                ('universidad', models.CharField(max_length=200, blank=True)),
                ('periodo_practica', models.CharField(max_length=100, blank=True)),
            ],
            options={'db_table': 'practicantes'},
        ),

        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_cliente', to='usuarios.usuario')),
                ('telefono', models.CharField(max_length=20, blank=True)),
                ('direccion', models.TextField(blank=True)),
            ],
            options={'db_table': 'clientes'},
        ),

        migrations.CreateModel(
            name='ResetPasswordToken',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('usado', models.BooleanField(default=False)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reset_tokens', to='usuarios.usuario')),
            ],
            options={'db_table': 'reset_password_tokens'},
        ),
    ]
# Generated by Django 4.2.7 on 2025-11-04 02:33

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre')),
                ('apellido', models.CharField(max_length=100, verbose_name='Apellido')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Correo electrónico')),
                ('username', models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(message='El nombre de usuario solo puede contener letras, números y @/./+/-/_', regex='^[\\w.@+-]+$')], verbose_name='Nombre de usuario')),
                ('password', models.CharField(max_length=255)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo'), ('suspendido', 'Suspendido')], default='activo', max_length=20, verbose_name='Estado')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Es staff')),
                ('is_active', models.BooleanField(default=True, verbose_name='Está activo')),
                ('intentos_fallidos', models.IntegerField(default=0)),
                ('bloqueado_hasta', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
                'db_table': 'usuarios',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('administrador', 'Administrador'), ('veterinario', 'Veterinario'), ('practicante', 'Practicante'), ('recepcionista', 'Recepcionista'), ('cliente', 'Cliente')], max_length=50, unique=True, verbose_name='Nombre del rol')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
                'db_table': 'roles',
            },
        ),
        migrations.CreateModel(
            name='UsuarioPendiente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Correo electrónico')),
                ('password', models.CharField(max_length=255, verbose_name='Contraseña')),
                ('verification_code', models.CharField(max_length=255, verbose_name='Código de verificación')),
            ],
            options={
                'verbose_name': 'Usuario Pendiente',
                'verbose_name_plural': 'Usuarios Pendientes',
                'db_table': 'usuarios_pendientes',
            },
        ),
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_cliente', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('telefono', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('direccion', models.TextField(blank=True, verbose_name='Dirección')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'clientes',
            },
        ),
        migrations.CreateModel(
            name='Veterinario',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_veterinario', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('licencia', models.CharField(max_length=50, unique=True, verbose_name='Número de licencia')),
                ('especialidad', models.CharField(blank=True, max_length=100, verbose_name='Especialidad')),
                ('horario', models.TextField(blank=True, verbose_name='Horario de atención')),
            ],
            options={
                'verbose_name': 'Veterinario',
                'verbose_name_plural': 'Veterinarios',
                'db_table': 'veterinarios',
            },
        ),
        migrations.CreateModel(
            name='UsuarioRol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rol_usuarios', to='usuarios.rol')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuario_roles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Usuario-Rol',
                'verbose_name_plural': 'Usuarios-Roles',
                'db_table': 'usuario_roles',
                'unique_together': {('usuario', 'rol')},
            },
        ),
        migrations.CreateModel(
            name='Practicante',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='perfil_practicante', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('universidad', models.CharField(blank=True, max_length=200, verbose_name='Universidad')),
                ('periodo_practica', models.CharField(blank=True, max_length=100, verbose_name='Período de práctica')),
                ('tutor_veterinario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='practicantes', to='usuarios.veterinario')),
            ],
            options={
                'verbose_name': 'Practicante',
                'verbose_name_plural': 'Practicantes',
                'db_table': 'practicantes',
            },
        ),
    ]
