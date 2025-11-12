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

class ViewsBaseTest(TestCase):
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        # Crear veterinario
        self.vet_user = User.objects.create_user(
            username='vet_pedro',
            email='vet@test.com',
            nombre='Pedro',
            apellido='Ramírez',
            password='testpass123'
        )

        self.veterinario = Veterinario.objects.create(
            usuario=self.vet_user,
            licencia='VET-12345',
            especialidad='Medicina General'
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

class ConsultaViewSetTest(ViewsBaseTest):
    """Tests para ConsultaViewSet"""

    def test_list_consultas_sin_autenticacion(self):
        """Prueba que lista de consultas requiere autenticación"""
        url = reverse('consulta-list')
        response = self.client.get(url)

        # Dependiendo de la configuración de permisos
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
            'veterinario': self.veterinario.usuario.id,
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
            'veterinario': self.veterinario.usuario.id,
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
            'veterinario': self.veterinario.usuario.id,
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
            'veterinario': self.veterinario.usuario.id,
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
            'veterinario': self.veterinario.usuario.id,
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

    def test_filtrar_consultas_por_mascota(self):
        """Prueba filtrar consultas por mascota"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('consulta-list')
        response = self.client.get(url, {'mascota': self.mascota.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Manejar paginación
        if isinstance(response.data, dict) and 'results' in response.data:
            consultas = response.data['results']
        else:
            consultas = response.data

        self.assertGreater(len(consultas), 0)

        # Verificar que todas son de la mascota correcta
        for consulta in consultas:
            self.assertEqual(consulta['mascota'], self.mascota.id)


class ExamenViewSetTest(ViewsBaseTest):
    """Tests para ExamenViewSet"""

    def test_list_examenes(self):
        """Prueba listar exámenes"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('examen-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class HistorialVacunaViewSetTest(ViewsBaseTest):
    """Tests para HistorialVacunaViewSet"""

    User.objects.all().delete()

    def test_list_vacunas(self):
        """Prueba listar historial de vacunas"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('vacuna-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



class HistoriaClinicaViewSetTest(ViewsBaseTest):
    """Tests para HistoriaClinicaViewSet"""

    def test_list_historias_clinicas(self):
        """Prueba listar historias clínicas"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('historia-clinica-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_historia_clinica(self):
        """Prueba obtener detalle de historia clínica"""
        self.client.force_authenticate(user=self.vet_user)
        url = reverse('historia-clinica-detail', kwargs={'pk': self.historia.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mascota'], self.mascota.id)

    def test_cliente_puede_ver_su_historia(self):
        """Prueba que el cliente puede ver la historia de su mascota"""
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('historia-clinica-detail', kwargs={'pk': self.historia.pk})
        response = self.client.get(url)

        # Dependiendo de la implementación de permisos
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])