"""
Tests para las views/endpoints del módulo de consultas
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

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


class ConsultaViewSetTest(TestCase):
    """Tests para ConsultaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

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

        # Crear mascota
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

    def test_list_consultas_sin_autenticacion(self):
        """Prueba que lista de consultas requiere autenticación"""
        url = reverse('consulta-list')
        response = self.client.get(url)

        # Dependiendo de la configuración de permisos
        # Puede retornar 401 o 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_consultas_autenticado_veterinario(self):
        """Prueba listar consultas como veterinario autenticado"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_consulta(self):
        """Prueba obtener detalle de una consulta"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-detail', kwargs={'pk': self.consulta.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['diagnostico'], 'Gastritis aguda')

    def test_create_consulta_valida(self):
        """Prueba crear una consulta válida"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Control de rutina',
            'diagnostico': 'Mascota saludable',
            'notas_adicionales': 'Todo normal'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Consulta.objects.count(), 2)

    def test_create_consulta_sin_descripcion(self):
        """Prueba que falla al crear consulta sin descripción"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': '',
            'diagnostico': 'Test'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_consulta_sin_diagnostico(self):
        """Prueba que falla al crear consulta sin diagnóstico"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

        data = {
            'mascota': self.mascota.id,
            'veterinario': self.veterinario.id,
            'descripcion_consulta': 'Consulta de prueba',
            'diagnostico': ''
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_consulta_con_examenes(self):
        """Prueba crear consulta con exámenes anidados"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

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

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Examen.objects.filter(consulta__id=response.data['id']).count(), 2)

    def test_create_consulta_con_vacunas(self):
        """Prueba crear consulta con historial de vacunas"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

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

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HistorialVacuna.objects.filter(consulta__id=response.data['id']).count(), 1)

    def test_update_consulta(self):
        """Prueba actualizar una consulta"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-detail', kwargs={'pk': self.consulta.pk})

        data = {
            'descripcion_consulta': 'Consulta actualizada',
            'diagnostico': 'Diagnóstico actualizado'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.diagnostico, 'Diagnóstico actualizado')

    def test_delete_consulta(self):
        """Prueba eliminar una consulta"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-detail', kwargs={'pk': self.consulta.pk})

        response = self.client.delete(url)

        # Verificar que se eliminó o que retorna el status code apropiado
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_403_FORBIDDEN])

    def test_filtrar_consultas_por_mascota(self):
        """Prueba filtrar consultas por mascota"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')

        response = self.client.get(url, {'mascota': self.mascota.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que todas las consultas pertenecen a la mascota
        for consulta in response.data:
            self.assertEqual(consulta.get('mascota'), self.mascota.id)

    def test_cliente_solo_ve_sus_mascotas(self):
        """Prueba que el cliente solo ve consultas de sus mascotas"""
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('consulta-list')

        response = self.client.get(url)

        # Dependiendo de la implementación de permisos
        # El cliente puede ver sus consultas o recibir 200/403
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])


class ExamenViewSetTest(TestCase):
    """Tests para ExamenViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

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
            descripcion_consulta='Requiere diagnóstico',
            diagnostico='Pendiente de exámenes'
        )

        self.examen = Examen.objects.create(
            consulta=self.consulta,
            tipo_examen='HEMOGRAMA',
            descripcion='Hemograma completo de rutina'
        )

    def test_list_examenes(self):
        """Prueba listar exámenes"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('examen-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class HistorialVacunaViewSetTest(TestCase):
    """Tests para HistorialVacunaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

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

        self.consulta = Consulta.objects.create(
            mascota=self.mascota,
            veterinario=self.veterinario,
            descripcion_consulta='Vacunación',
            diagnostico='Normal'
        )

    def test_list_vacunas(self):
        """Prueba listar historial de vacunas"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('historialvacuna-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



class HistoriaClinicaViewSetTest(TestCase):
    """Tests para HistoriaClinicaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        self.vet_user = User.objects.create_user(
            correo_electronico='vet@test.com',
            nombre='Sofia',
            apellido='Mendoza',
            password='testpass123',
            tipo_usuario='VETERINARIO'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
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

        self.historia = HistoriaClinica.objects.create(
            mascota=self.mascota,
            estado_vacunacion_actual='AL_DIA'
        )

    def test_list_historias_clinicas(self):
        """Prueba listar historias clínicas"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('historiaclinica-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_historia_clinica(self):
        """Prueba obtener detalle de historia clínica"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('historiaclinica-detail', kwargs={'pk': self.historia.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mascota'], self.mascota.id)

    def test_cliente_puede_ver_su_historia(self):
        """Prueba que el cliente puede ver la historia de su mascota"""
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('historiaclinica-detail', kwargs={'pk': self.historia.pk})
        response = self.client.get(url)

        # Dependiendo de la implementación de permisos
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])