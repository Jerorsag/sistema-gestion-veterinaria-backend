from rest_framework import status
from .test_base import CitasAPITestCase # <-- Importamos nuestra base
from citas.models import Cita
from citas.patterns.state import EstadoCita # <-- Importamos el State

class CancelacionTests(CitasAPITestCase):

    def test_cancelar_cita_exitosa(self):
        """Prueba de CP-023: Cancelar una cita."""
        cita = Cita.objects.create(
            mascota=self.mascota,
            veterinario=self.vet_user,
            servicio=self.servicio,
            fecha_hora=self.fecha_futura,
            estado=EstadoCita.AGENDADA 
        )
        
        url = f'/api/v1/citas/{cita.id}/cancelar/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refrescar la cita desde la BD
        cita.refresh_from_db()
        self.assertEqual(cita.estado, EstadoCita.CANCELADA) 