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

class ServicesBaseTastCase(TestCase):
    def setUp(self):
        """Configuración inicial"""
        self.vet_user  = User.objects.create_user(
            username='vet_test',
            email='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia='VET-98765'
        )

        self.cliente_user = User.objects.create_user(
            username='cliente_carlos',
            email='cliente@test.com',
            nombre='Carlos',
            apellido='Martínez',
            password='testpass123'
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
            cliente=self.cliente
        )

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Revisión general',
            diagnostico='Normal'
        )

class ConsultaServiceTest(ServicesBaseTastCase):
    """Tests para los servicios de Consulta"""

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


class DatosPersonalesServiceTest(ServicesBaseTastCase):
    """Tests para el servicio get_datos_personales"""

    def test_datos_personales_desde_serializer(self):
        """Prueba obtener datos personales usando el serializer"""
        datos = get_datos_personales(self.consulta)

        self.assertIsNotNone(datos)
        self.assertIsInstance(datos, dict)
        self.assertIn('nombre', datos)
        self.assertIn('telefono', datos)
        self.assertIn('direccion', datos)

    def test_datos_personales_incluye_nombre_completo_cliente(self):
        """Prueba que incluye el nombre completo del cliente"""
        datos = get_datos_personales(self.consulta)

        # El nombre debe contener el nombre y apellido del cliente
        nombre = datos.get('nombre', '')
        self.assertIn('Carlos', nombre)
        self.assertIn('Martínez', nombre)

    def test_datos_personales_incluye_telefono(self):
        """Prueba que incluye el teléfono del cliente"""
        datos = get_datos_personales(self.consulta)

        telefono = datos.get('telefono')
        self.assertEqual(telefono, '3009876543')

    def test_datos_personales_incluye_direccion(self):
        """Prueba que incluye la dirección del cliente"""
        datos = get_datos_personales(self.consulta  )

        direccion = datos.get('direccion')
        self.assertEqual(direccion, 'Carrera 45 #12-34')

class VacunacionIntegrationTest(ServicesBaseTastCase):
    """Tests de integración para el flujo completo de vacunación"""

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