from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .test_base import CitasAPITestCase
from citas.models import Cita
from citas.patterns.state import EstadoCita

class CP022ReagendarTest(CitasAPITestCase):

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.cliente_user)
        manana = timezone.now() + timedelta(days=1)
        self.fecha_futura = manana.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Creamos la cita original
        self.cita = Cita.objects.create(
            mascota=self.mascota, veterinario=self.vet_user, 
            servicio=self.servicio, fecha_hora=self.fecha_futura,
            estado=EstadoCita.AGENDADA
        )

    def test_reagendar_cita_exitosa(self):
        """CP-022: Reagendar una cita existente (200 OK)"""
        nueva_fecha = self.fecha_futura + timedelta(hours=2)
        url = reverse('cita-reagendar', kwargs={'pk': self.cita.id})
        
        response = self.client.post(url, {"fecha_hora": nueva_fecha.isoformat()}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.fecha_hora, nueva_fecha)