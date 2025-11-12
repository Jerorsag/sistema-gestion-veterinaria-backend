"""
Tests para los modelos del módulo de consultas
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from consultas.models import (
    Consulta,
    Prescripcion,
    Examen,
    HistorialVacuna,
    HistoriaClinica
)
from mascotas.models import Mascota, Raza, Especie
from usuarios.models import Veterinario, Cliente

User = get_user_model()


class ConsultaModelTest(TestCase):
    """Tests para el modelo Consulta"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario base
        self.user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        # Crear veterinario
        self.veterinario = Veterinario.objects.create(
            usuario=self.user,
            licencia_profesional='VET-12345',
            especialidad='Medicina General'
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

        # Crear especie y raza
        self.especie = Especie.objects.create(nombre='Canino')
        self.raza = Raza.objects.create(
            nombre='Golden Retriever',
            especie=self.especie
        )

        # Crear mascota
        self.mascota = Mascota.objects.create(
            nombre='Max',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=730),
            sexo='M',
            color='Dorado',
            cliente=self.cliente
        )

    def test_crear_consulta_exitosa(self):
        """Prueba crear una consulta válida"""
        consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Perro con vómitos frecuentes',
            diagnostico='Gastritis aguda'
        )

        self.assertEqual(consulta.mascota, self.mascota)
        self.assertEqual(consulta.veterinario, self.veterinario)
        self.assertIsNotNone(consulta.fecha_consulta)
        self.assertIn('vómitos', consulta.descripcion_consulta)

    def test_consulta_sin_descripcion(self):
        """Prueba que una consulta sin descripción lanza ValidationError"""
        consulta = Consulta(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='',
            diagnostico='Gastritis'
        )

        with self.assertRaises(ValidationError):
            consulta.full_clean()

    def test_consulta_sin_diagnostico(self):
        """Prueba que una consulta sin diagnóstico lanza ValidationError"""
        consulta = Consulta(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Vómitos frecuentes',
            diagnostico=''
        )

        with self.assertRaises(ValidationError):
            consulta.full_clean()

    def test_str_consulta(self):
        """Prueba la representación en string de Consulta"""
        consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Revisión rutinaria',
            diagnostico='Saludable'
        )

        str_consulta = str(consulta)
        self.assertIn('Max', str_consulta)
        self.assertIn(consulta.fecha_consulta.strftime('%d/%m/%Y'), str_consulta)

    def test_get_prescripciones_count(self):
        """Prueba el método get_prescripciones_count"""
        consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Consulta de control',
            diagnostico='Normal'
        )

        self.assertEqual(consulta.get_prescripciones_count(), 0)

    def test_get_examenes_count(self):
        """Prueba el método get_examenes_count"""
        consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Consulta de control',
            diagnostico='Normal'
        )

        self.assertEqual(consulta.get_examenes_count(), 0)

    def test_get_estado_vacunacion_consulta(self):
        """Prueba el método get_estado_vacunacion_consulta"""
        consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Vacunación',
            diagnostico='Normal'
        )

        estado = consulta.get_estado_vacunacion_consulta()
        self.assertEqual(estado, "No registrado")


class PrescripcionModelTest(TestCase):
    """Tests para el modelo Prescripción"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario y veterinario
        self.user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.user,
            licencia_profesional='VET-12345'
        )

        # Crear cliente y mascota
        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='María',
            apellido='García',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3001234567'
        )

        self.especie = Especie.objects.create(nombre='Canino')
        self.raza = Raza.objects.create(nombre='Beagle', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Rocky',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=365),
            sexo='M',
            cliente=self.cliente
        )

        # Crear consulta
        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Control rutinario',
            diagnostico='Saludable'
        )

    def test_crear_prescripcion_sin_medicamento_falla(self):
        """Prueba que no se puede crear prescripción sin medicamento"""
        # Este test requiere el modelo Producto de inventario
        # Se comenta hasta que esté disponible
        pass

    def test_prescripcion_cantidad_minima(self):
        """Prueba que la cantidad debe ser mayor a 0"""
        # Este test requiere el modelo Producto de inventario
        pass

    def test_str_prescripcion(self):
        """Prueba la representación en string"""
        # Este test requiere el modelo Producto de inventario
        pass


class ExamenModelTest(TestCase):
    """Tests para el modelo Examen"""

    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Ana',
            apellido='López',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.user,
            licencia_profesional='VET-98765'
        )

        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='Carlos',
            apellido='Martínez',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3009876543'
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
            descripcion_consulta='Consulta de diagnóstico',
            diagnostico='Requiere exámenes'
        )

    def test_crear_examen_hemograma(self):
        """Prueba crear un examen de hemograma"""
        examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='HEMOGRAMA',
            descripcion='Hemograma completo de rutina'
        )

        self.assertEqual(examen.tipo_examen, 'HEMOGRAMA')
        self.assertEqual(examen.get_tipo_examen_display(), 'Hemograma completo')
        self.assertIsNotNone(examen.fecha_orden)

    def test_crear_examen_rayos_x(self):
        """Prueba crear un examen de rayos X"""
        examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='RAYOS_X',
            descripcion='Radiografía de tórax'
        )

        self.assertEqual(examen.tipo_examen, 'RAYOS_X')
        self.assertIn('Rayos X', str(examen))

    def test_str_examen(self):
        """Prueba la representación en string del examen"""
        examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='ECOGRAFIA',
            descripcion='Ecografía abdominal'
        )

        str_examen = str(examen)
        self.assertIn('Ecografía', str_examen)


class HistorialVacunaModelTest(TestCase):
    """Tests para el modelo HistorialVacuna"""

    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Pedro',
            apellido='Ramírez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.user,
            licencia_profesional='VET-11111'
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
            telefono='3005551234'
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

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Vacunación',
            diagnostico='Normal'
        )

    def test_crear_vacuna_al_dia(self):
        """Prueba crear registro de vacunas al día"""
        vacuna = HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='AL_DIA',
            vacunas_descripcion=''
        )

        self.assertEqual(vacuna.estado, 'AL_DIA')
        self.assertEqual(vacuna.get_estado_display(), 'Al día')

    def test_crear_vacuna_pendiente_con_descripcion(self):
        """Prueba crear registro de vacunas pendientes con descripción"""
        vacuna = HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion='Rabia, Parvovirus, Moquillo'
        )

        self.assertEqual(vacuna.estado, 'PENDIENTE')
        self.assertIn('Rabia', vacuna.vacunas_descripcion)

    def test_vacuna_pendiente_sin_descripcion_falla(self):
        """Prueba que vacuna pendiente sin descripción falla validación"""
        vacuna = HistorialVacuna(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion=''
        )

        with self.assertRaises(ValidationError):
            vacuna.full_clean()

    def test_vacuna_en_proceso_sin_descripcion_falla(self):
        """Prueba que vacuna en proceso sin descripción falla validación"""
        vacuna = HistorialVacuna(
            consulta=self.consulta,
            estado='EN_PROCESO',
            vacunas_descripcion='   '
        )

        with self.assertRaises(ValidationError):
            vacuna.full_clean()

    def test_str_historial_vacuna(self):
        """Prueba la representación en string"""
        vacuna = HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion='Triple felina'
        )

        str_vacuna = str(vacuna)
        self.assertIn('Pendiente', str_vacuna)
        self.assertIn('Triple felina', str_vacuna)


class HistoriaClinicaModelTest(TestCase):
    """Tests para el modelo HistoriaClinica"""

    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Sofia',
            apellido='Mendoza',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.user,
            licencia_profesional='VET-22222'
        )

        self.cliente_user = User.objects.create_user(
            correo_electronico='cliente@test.com',
            nombre='Diego',
            apellido='Rojas',
            password='testpass123',
            tipo_usuario='CLIENTE'
        )

        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3007778888'
        )

        self.especie = Especie.objects.create(nombre='Canino')
        self.raza = Raza.objects.create(nombre='Husky', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Zeus',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=1460),
            sexo='M',
            cliente=self.cliente
        )

    def test_crear_historia_clinica(self):
        """Prueba crear una historia clínica"""
        historia = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

        self.assertEqual(historia.mascota, self.mascota)
        self.assertEqual(historia.estado_vacunacion_actual, 'AL_DIA')
        self.assertIsNotNone(historia.fecha_creacion)

    def test_str_historia_clinica(self):
        """Prueba la representación en string"""
        historia = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='PENDIENTE'
        )

        str_historia = str(historia)
        self.assertIn('Zeus', str_historia)
        self.assertIn('Historia Clínica', str_historia)

    def test_get_total_consultas_sin_consultas(self):
        """Prueba get_total_consultas cuando no hay consultas"""
        historia = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

        self.assertEqual(historia.get_total_consultas(), 0)

    def test_get_total_consultas_con_consultas(self):
        """Prueba get_total_consultas con consultas registradas"""
        historia = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

        # Crear consultas
        Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Primera consulta',
            diagnostico='Normal'
        )

        Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Segunda consulta',
            diagnostico='Normal'
        )

        self.assertEqual(historia.get_total_consultas(), 2)

    def test_relacion_onetoone_mascota(self):
        """Prueba la relación OneToOne con mascota"""
        historia1 = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

        # Intentar crear otra historia para la misma mascota debe fallar
        with self.assertRaises(Exception):
            historia2 = HistoriaClinica.objects.create(
                mascota=self.mascota,
                estado_vacunacion_actual='PENDIENTE'
            )