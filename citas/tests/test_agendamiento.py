from rest_framework import status
from .test_base import CitasAPITestCase # <-- Importamos nuestra base
from citas.models import Cita
from citas.patterns.state import EstadoCita # <-- Importamos el State

class AgendamientoTests(CitasAPITestCase):

    def test_agendar_cita_exitosa(self):
        """Prueba de CP-020: Agendar una cita exitosamente."""
        url = '/api/v1/citas/'
        data = {
            "mascota_id": self.mascota.id,          # <-- FIX #2: Usar ID como entero
            "veterinario_id": self.vet_user.id,    # <-- FIX #2: Usar ID como entero
            "servicio_id": self.servicio.id,      # <-- FIX #2: Usar ID como entero
            "fecha_hora": self.fecha_futura.isoformat()
        }

        response = self.client.post(url, data, format='json')

        # Comprobar que la respuesta fue "201 Created"
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cita.objects.count(), 1)
        self.assertEqual(Cita.objects.first().estado, EstadoCita.AGENDADA) # <-- FIX #1

    def test_agendar_cita_conflicto_horario(self):
        """Prueba de CP-021: Fallar al agendar en un horario ocupado."""
        url = '/api/v1/citas/'
        
        # 1. Crear la primera cita (exitosa)
        Cita.objects.create(
            mascota=self.mascota,
            veterinario=self.vet_user,
            servicio=self.servicio,
            fecha_hora=self.fecha_futura,
            estado=EstadoCita.AGENDADA
        )
        
        data = {
            "mascota_id": self.mascota.id, 
            "veterinario_id": self.vet_user.id,   
            "servicio_id": self.servicio.id,      
            "fecha_hora": self.fecha_futura.isoformat() # Misma fecha y hora
        }

        # 2. Intentar crear la segunda cita (debe fallar)
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Conflicto de Horario", str(response.data))
        self.assertEqual(Cita.objects.count(), 1) # Solo la primera debe existir