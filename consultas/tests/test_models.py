"""
Tests para los modelos del módulo de consultas
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal

from consultas.models import (
    Consulta,
    Prescripcion,
    Examen,
    HistorialVacuna,
    HistoriaClinica
)
from mascotas.models import Mascota, Raza, Especie
from usuarios.models import Veterinario, Cliente
from inventario.models import Producto, Marca, Categoria

User = get_user_model()


class DatosBaseTestCase(TestCase):
    """Configuración común para todos los tests de consultas"""

    def setUp(self):
        # Crear veterinario
        self.vet_user = User.objects.create_user(
            username='vet_test',
            email='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123'
        )
        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia='VET-12345'
        )

        # Crear cliente
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            nombre='María',
            apellido='García',
            password='testpass123'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            telefono='3001234567'
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
            cliente=self.cliente
        )

        # Crear consulta base
        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Consulta de prueba',
            diagnostico='Diagnóstico de prueba'
        )


class ConsultaModelTest(DatosBaseTestCase):
    """Tests para el modelo Consulta"""

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


class PrescripcionModelTest(DatosBaseTestCase):
    """Tests para el modelo Prescripción"""

    def setUp(self):
        super().setUp()

        self.marca = Marca.objects.create(descripcion='Laboratorio Veterinario')

        self.categoria = Categoria.objects.create(
            descripcion='Medicamentos',
            color='#FF5733'
        )

        self.medicamento = Producto.objects.create(
            descripcion='Metoclopramida 10mg',
            marca=self.marca,
            categoria=self.categoria,
            stock=Decimal('100.00'),
            stock_minimo=Decimal('10.00'),
            precio_venta=Decimal('15000.00'),
            precio_compra=Decimal('8000.00')
        )

    def test_crear_prescripcion_exitosa(self):
        """Prueba crear una prescripción válida referenciando producto existente"""
        prescripcion = Prescripcion.objects.create(
            consulta=self.consulta,
            medicamento=self.medicamento,
            cantidad=3,
            indicaciones='Administrar 1 tableta cada 8 horas por 3 días'
        )

        self.assertEqual(prescripcion.consulta, self.consulta)
        self.assertEqual(prescripcion.medicamento, self.medicamento)
        self.assertEqual(prescripcion.cantidad, 3)
        self.assertIn('tableta', prescripcion.indicaciones)

    def test_crear_prescripcion_sin_medicamento_falla(self):
        """Prueba que no se puede crear prescripción sin medicamento"""
        prescripcion = Prescripcion(
            consulta=self.consulta,
            medicamento=None,
            cantidad=3,
            indicaciones='Administrar cada 8 horas'
        )

        with self.assertRaises(ValidationError):
            prescripcion.full_clean()

    def test_prescripcion_cantidad_minima(self):
        """Prueba que la cantidad debe ser mayor a 0"""
        prescripcion = Prescripcion(
            consulta=self.consulta,
            medicamento=self.medicamento,
            cantidad=0,
            indicaciones='Administrar según indicación'
        )

        with self.assertRaises(ValidationError):
            prescripcion.full_clean()

    def test_str_prescripcion(self):
        """Prueba la representación en string"""
        prescripcion = Prescripcion.objects.create(
            consulta=self.consulta,
            medicamento=self.medicamento,
            cantidad=5,
            indicaciones='Cada 12 horas'
        )

        str_prescripcion = str(prescripcion)
        self.assertIn('Metoclopramida', str_prescripcion)
        self.assertIn('5', str_prescripcion)

    def test_prescripcion_sin_indicaciones(self):
        """Prueba que se puede crear prescripción sin indicaciones (campo opcional)"""
        prescripcion = Prescripcion.objects.create(
            consulta=self.consulta,
            medicamento=self.medicamento,
            cantidad=2
        )

        self.assertEqual(prescripcion.indicaciones, "")
        self.assertIsNotNone(prescripcion.fecha_prescripcion)

    def test_multiples_prescripciones_misma_consulta(self):
        """Prueba que se pueden tener múltiples prescripciones en una consulta"""
        # Crear otro medicamento
        otro_medicamento = Producto.objects.create(
            descripcion='Amoxicilina 500mg',
            marca=self.marca,
            categoria=self.categoria,
            stock=Decimal('50.00'),
            stock_minimo=Decimal('10.00'),
            precio_venta=Decimal('20000.00'),
            precio_compra=Decimal('12000.00')
        )

        Prescripcion.objects.create(
            consulta=self.consulta,
            medicamento=self.medicamento,
            cantidad=3
        )

        Prescripcion.objects.create(
            consulta=self.consulta,
            medicamento=otro_medicamento,
            cantidad=2
        )

        self.assertEqual(self.consulta.prescripciones.count(), 2)


class ExamenModelTest(DatosBaseTestCase):
    """Tests para el modelo Examen"""

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

    def test_str_examen(self):
        """Prueba la representación en string del examen"""
        examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='ECOGRAFIA',
            descripcion='Ecografía abdominal'
        )

        str_examen = str(examen)
        self.assertIn('Ecografía', str_examen)


class HistorialVacunaModelTest(DatosBaseTestCase):
    """Tests para el modelo HistorialVacuna"""

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


class HistoriaClinicaModelTest(DatosBaseTestCase):
    """Tests para el modelo HistoriaClinica"""
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
        # Crear primera historia
        HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

        # Intentar crear otra historia para la misma mascota debe fallar
        with self.assertRaises(Exception):
            HistoriaClinica.objects.create(
                mascota=self.mascota,
                estado_vacunacion_actual='PENDIENTE'
            )