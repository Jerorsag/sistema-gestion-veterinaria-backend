"""
Tests para los serializers del módulo de consultas
"""

from django.test import TestCase
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
from consultas.serializers.consulta_serializers import (
    ConsultaListSerializer,
    ConsultaDetailSerializer,
    ConsultaCreateSerializer,
    ConsultaUpdateSerializer,
    ConsultaSerializer
)
from consultas.serializers.vacuna_serializers import (
    HistorialVacunaSerializer,
    HistorialVacunaCreateSerializer
)
from consultas.serializers.examen_serializers import (
    ExamenSerializer,
    ExamenCreateSerializer
)

from mascotas.models import Mascota, Raza, Especie
from usuarios.models import Veterinario, Cliente

User = get_user_model()


class ConsultaSerializerTest(TestCase):
    """Tests para los serializers de Consulta"""

    def setUp(self):
        """Configuración inicial"""
        # Crear usuario veterinario
        self.vet_user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Juan',
            apellido='Pérez',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia_profesional='VET-12345',
            especialidad='Medicina General'
        )

        # Crear usuario cliente
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

        # Crear consulta de prueba
        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Perro con vómitos frecuentes',
            diagnostico='Gastritis aguda',
            notas_adicionales='Dieta blanda por 3 días'
        )

    def test_consulta_list_serializer(self):
        """Prueba ConsultaListSerializer"""
        serializer = ConsultaListSerializer(self.consulta)
        data = serializer.data

        self.assertEqual(data['mascota_nombre'], 'Max')
        self.assertEqual(data['veterinario_nombre'], 'Juan Pérez')
        self.assertEqual(data['diagnostico'], 'Gastritis aguda')
        self.assertIn('estado_vacunacion', data)
        self.assertIn('total_prescripciones', data)

    def test_consulta_detail_serializer(self):
        """Prueba ConsultaDetailSerializer"""
        serializer = ConsultaDetailSerializer(self.consulta)
        data = serializer.data

        self.assertEqual(data['mascota'], self.mascota.id)
        self.assertIn('datos_personales', data)
        self.assertIn('prescripciones', data)
        self.assertIn('examenes', data)
        self.assertIn('vacunas', data)

    def test_consulta_detail_serializer_datos_personales(self):
        """Prueba que datos_personales se incluyen correctamente"""
        serializer = ConsultaDetailSerializer(self.consulta)
        data = serializer.data

        datos_personales = data['datos_personales']
        self.assertIsNotNone(datos_personales)
        self.assertIn('nombre', datos_personales)
        self.assertIn('telefono', datos_personales)
        self.assertIn('direccion', datos_personales)

    def test_consulta_create_serializer_valido(self):
        """Prueba crear consulta con datos válidos"""
        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Control de rutina',
            'diagnostico': 'Mascota saludable',
            'notas_adicionales': 'Próxima cita en 6 meses'
        }

        serializer = ConsultaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_consulta_create_sin_descripcion(self):
        """Prueba que falla sin descripción"""
        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': '',
            'diagnostico': 'Normal'
        }

        serializer = ConsultaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('descripcion_consulta', serializer.errors)

    def test_consulta_create_sin_diagnostico(self):
        """Prueba que falla sin diagnóstico"""
        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Control general',
            'diagnostico': ''
        }

        serializer = ConsultaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('diagnostico', serializer.errors)


    def test_consulta_create_con_examenes(self):
        """Prueba crear consulta con exámenes anidados"""
        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Requiere exámenes',
            'diagnostico': 'Pendiente de resultados',
            'examenes': [
                {
                    'tipo_examen': 'HEMOGRAMA',
                    'descripcion': 'Hemograma completo'
                },
                {
                    'tipo_examen': 'RAYOS_X',
                    'descripcion': 'Radiografía de tórax'
                }
            ]
        }

        serializer = ConsultaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_consulta_create_con_vacunas(self):
        """Prueba crear consulta con historial de vacunas"""
        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Plan de vacunación',
            'diagnostico': 'Normal',
            'vacunas': {
                'estado': 'PENDIENTE',
                'vacunas_descripcion': 'Rabia, Parvovirus'
            }
        }

        serializer = ConsultaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_consulta_update_serializer(self):
        """Prueba actualizar consulta"""
        data = {
            'descripcion_consulta': 'Consulta actualizada',
            'diagnostico': 'Diagnóstico actualizado',
            'notas_adicionales': 'Notas nuevas'
        }

        serializer = ConsultaUpdateSerializer(self.consulta, data=data, partial=True)
        self.assertTrue(serializer.is_valid())


class HistorialVacunaSerializerTest(TestCase):
    """Tests para serializers de HistorialVacuna"""

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
            telefono='3009876543'
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

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Vacunación',
            diagnostico='Normal'
        )

    def test_historial_vacuna_serializer(self):
        """Prueba HistorialVacunaSerializer básico"""
        vacuna = HistorialVacuna.objects.create(
            consulta=self.consulta,
            estado='PENDIENTE',
            vacunas_descripcion='Rabia, Parvovirus'
        )

        serializer = HistorialVacunaSerializer(vacuna)
        data = serializer.data

        self.assertEqual(data['estado'], 'PENDIENTE')
        self.assertIn('Rabia', data['vacunas_descripcion'])

    def test_historial_vacuna_create_serializer_valido(self):
        """Prueba crear historial de vacuna válido"""
        data = {
            'estado': 'EN_PROCESO',
            'vacunas_descripcion': 'Triple felina'
        }

        serializer = HistorialVacunaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_historial_vacuna_al_dia_sin_descripcion(self):
        """Prueba que al día no requiere descripción"""
        data = {
            'estado': 'AL_DIA',
            'vacunas_descripcion': ''
        }

        serializer = HistorialVacunaCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_historial_vacuna_pendiente_requiere_descripcion(self):
        """Prueba que pendiente requiere descripción"""
        data = {
            'estado': 'PENDIENTE',
            'vacunas_descripcion': ''
        }

        serializer = HistorialVacunaCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ExamenSerializerTest(TestCase):
    """Tests para serializers de Examen"""

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

        self.especie = Especie.objects.create(nombre='Felino')
        self.raza = Raza.objects.create(nombre='Siamés', especie=self.especie)

        self.mascota = Mascota.objects.create(
            nombre='Michi',
            especie=self.especie,
            raza=self.raza,
            fecha_nacimiento=timezone.now().date() - timedelta(days=1095),
            sexo='H',
            cliente=self.cliente
        )

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Requiere diagnóstico',
            diagnostico='Pendiente de exámenes'
        )

    def test_examen_serializer(self):
        """Prueba ExamenSerializer básico"""
        examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='HEMOGRAMA',
            descripcion='Hemograma completo de rutina'
        )

        serializer = ExamenSerializer(examen)
        data = serializer.data

        self.assertEqual(data['tipo_examen'], 'HEMOGRAMA')
        self.assertIn('Hemograma', data['descripcion'])

    def test_examen_create_serializer_valido(self):
        """Prueba crear examen válido"""
        data = {
            'tipo_examen': 'ECOGRAFIA',
            'descripcion': 'Ecografía abdominal completa'
        }

        serializer = ExamenCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_examen_create_sin_descripcion(self):
        """Prueba que descripción es opcional"""
        data = {
            'tipo_examen': 'RAYOS_X',
            'descripcion': ''
        }

        serializer = ExamenCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_examen_tipo_valido(self):
        """Prueba que solo acepta tipos válidos"""
        data = {
            'tipo_examen': 'TIPO_INVALIDO',
            'descripcion': 'Test'
        }

        serializer = ExamenCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())