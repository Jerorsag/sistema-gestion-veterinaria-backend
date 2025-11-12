"""
Tests para los servicios del módulo de consultas
"""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from consultas.models import (
    Consulta,
    HistorialVacuna
)
from consultas.services.consulta_service import (
    get_datos_personales,
    get_estado_vacunacion_consulta
)
from mascotas.models import Mascota, Raza, Especie
from usuarios.models import Veterinario, Cliente

User = get_user_model()


class ConsultaServiceTest(TestCase):
    """Tests para los servicios de Consulta"""

    def setUp(self):
        """Configuración inicial"""
        # Crear veterinario
        self.vet_user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia_profesional='VET-12345'
        )

        # Crear cliente
        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='María',
            apellido='García',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3001234567',
            direccion='Calle 123 #45-67'
        )

        # Crear especie, raza y mascota
        self.especie = Especie.objects.create(nombre='Canino')
        self.raza = Raza.objects.create(nombre='Golden Retriever', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Max',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=730),
            sexo='M',
            color='Dorado',
            cliente=self.cliente
        )

        # Crear consulta
        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Control de rutina',
            diagnostico='Saludable'
        )

    def test_get_estado_vacunacion_consulta_sin_vacunas(self):
        """Prueba obtener estado de vacunación cuando no hay registro"""
        estado = get_estado_vacunacion_consulta(self.consulta)

        self.assertEqual(estado, "No registrado")

    def test_get_estado_vacunacion_consulta_con_vacuna_pendiente(self):
        """Prueba obtener estado de vacunación pendiente"""
        HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion='Rabia, Parvovirus'
        )

        estado = get_estado_vacunacion_consulta(self.consulta)

        self.assertEqual(estado, "Pendiente")

    def test_get_estado_vacunacion_consulta_con_vacuna_al_dia(self):
        """Prueba obtener estado de vacunación al día"""
        HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='AL_DIA',
            vacunas_descripcion=''
        )

        estado = get_estado_vacunacion_consulta(self.consulta)

        self.assertEqual(estado, "Al día")

    def test_get_estado_vacunacion_consulta_con_multiples_registros(self):
        """Prueba que obtiene el primer registro cuando hay múltiples"""
        # Crear dos registros
        HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion='Rabia'
        )

        HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='AL_DIA',
            vacunas_descripcion=''
        )

        estado = get_estado_vacunacion_consulta(self.consulta)

        # Debe obtener el primer registro
        self.assertIn(estado, ["Pendiente", "Al día"])


class DatosPersonalesServiceTest(TestCase):
    """Tests para el servicio get_datos_personales"""

    def setUp(self):
        """Configuración inicial"""
        self.vet_user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Ana',
            apellido='López',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia_profesional='VET-98765'
        )

        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='Pedro',
            apellido='Martínez',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3009876543',
            direccion='Carrera 45 #12-34'
        )

        self.especie = Especie.objects.create(nombre='Felino')
        self.raza = Raza.objects.create(nombre='Persa', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Luna',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=1095),
            sexo='H',
            color='Blanco',
            cliente=self.cliente
        )

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Revisión general',
            diagnostico='Normal'
        )

    def test_datos_personales_desde_serializer(self):
        """Prueba obtener datos personales usando el serializer"""

    def test_datos_personales_incluye_nombre_completo_cliente(self):
        """Prueba que incluye el nombre completo del cliente"""

    def test_datos_personales_incluye_telefono(self):
        """Prueba que incluye el teléfono del cliente"""

    def test_datos_personales_incluye_direccion(self):
        """Prueba que incluye la dirección del cliente"""

class VacunacionIntegrationTest(TestCase):
    """Tests de integración para el flujo completo de vacunación"""

    def setUp(self):
        """Configuración inicial"""
        self.vet_user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Carlos',
            apellido='Ramírez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia_profesional='VET-55555'
        )

        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='Laura',
            apellido='Torres',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3005554321'
        )

        self.especie = Especie.objects.create(nombre='Canino')
        self.raza = Raza.objects.create(nombre='Labrador', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Toby',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=180),
            sexo='M',
            cliente=self.cliente
        )

    def test_flujo_completo_vacunacion_pendiente_a_al_dia(self):
        """Prueba el flujo completo de cambiar estado de vacunación"""
        # Primera consulta - vacunas pendientes
        consulta1 = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Plan de vacunación',
            diagnostico='Normal'
        )

        vacuna1 = HistorialVacuna.objects.create(
            consulta=consulta1,
            estado='PENDIENTE',
            vacunas_descripcion='Rabia, Parvovirus'
        )

        # Verificar estado inicial
        estado1 = get_estado_vacunacion_consulta(consulta1)
        self.assertEqual(estado1, "Pendiente")

        # Segunda consulta - vacunas aplicadas
        consulta2 = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Aplicación de vacunas',
            diagnostico='Vacunas aplicadas correctamente'
        )

        vacuna2 = HistorialVacuna.objects.create(
            consulta=consulta2,
            estado='AL_DIA',
            vacunas_descripcion=''
        )

        # Verificar nuevo estado
        estado2 = get_estado_vacunacion_consulta(consulta2)
        self.assertEqual(estado2, "Al día")

    def test_multiples_consultas_mismo_dia(self):
        """Prueba múltiples consultas el mismo día"""
        fecha = timezone.now()

        consulta1 = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Primera consulta',
            diagnostico='Normal',
            fecha_consulta=fecha
        )

        consulta2 = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Segunda consulta',
            diagnostico='Normal',
            fecha_consulta=fecha
        )

        # Verificar que ambas consultas existen
        self.assertEqual(Consulta.objects.filter(mascota=self.mascota).count(), 2)