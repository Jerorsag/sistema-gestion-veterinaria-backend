from datetime import datetime, time, timedelta
from django.utils import timezone
from time import timezone
from rest_framework import status
from .test_base import CitasAPITestCase # <-- Importamos nuestra base
from citas.models import Cita
from citas.patterns.state import EstadoCita # <-- Importamos el State

class AgendamientoTests(CitasAPITestCase):

    def setUp(self):
        """Sobrescribimos el setUp de la clase base para añadir una fecha limpia."""
        super().setUp()
        
        # Creamos una fecha "limpia" para las pruebas (ej. 10:00 AM)
        # Esto soluciona el bug de enviar horas "sucias" (ej. 10:55:34)
        fecha_prueba = (timezone.now() + timedelta(days=5)).date()
        hora_prueba = time(10, 0) # 10:00 AM exactas
        
        # Convertimos la fecha y hora a un objeto datetime "aware"
        self.fecha_hora_limpia = timezone.make_aware(
            datetime.combine(fecha_prueba, hora_prueba)
        )

    def test_agendar_cita_exitosa(self):
        """Prueba de CP-020: Agendar una cita exitosamente."""
        url = '/api/v1/citas/'
        
        # FIX #2: (Arregla el 400 != 201)
        # Nuestros modelos usan BigAutoField (un entero), no un UUID.
        # El serializer espera un IntegerField.
        # Enviamos el .id directamente como un entero, no como un string.
        data = {
            "mascota_id": self.mascota.id,
            "veterinario_id": self.vet_user.id,
            "servicio_id": self.servicio.id,
            "fecha_hora": self.fecha_hora_limpia.isoformat() # Usamos la fecha limpia
        }

        response = self.client.post(url, data, format='json')

        # Añadimos 'response.data' al mensaje de error para ver qué falló
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Cita.objects.count(), 1)
        self.assertEqual(Cita.objects.first().estado, EstadoCita.AGENDADA)

    def test_agendar_cita_conflicto_horario(self):
        """Prueba de CP-021: Fallar al agendar en un horario ocupado."""
        url = '/api/v1/citas/'
        
        # 1. Crear la primera cita (exitosa) en la hora limpia
        Cita.objects.create(
            mascota=self.mascota,
            veterinario=self.vet_user,
            servicio=self.servicio,
            fecha_hora=self.fecha_hora_limpia,
            estado=EstadoCita.AGENDADA
        )
        
        data = {
            "mascota_id": self.mascota.id,            # <-- FIX #2
            "veterinario_id": self.vet_user.id,      # <-- FIX #2
            "servicio_id": self.servicio.id,        # <-- FIX #2
            "fecha_hora": self.fecha_hora_limpia.isoformat() # Misma fecha y hora
        }

        # 2. Intentar crear la segunda cita (debe fallar)
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # FIX #3: (Arregla el AssertionError de mensaje)
        # Comprobamos el mensaje de error real que viene del serializer/servicio
        # (El servicio está en `citas/patrones/composite.py`)
        self.assertIn("El veterinario no está disponible a esta hora.", str(response.data['non_field_errors']))
        self.assertEqual(Cita.objects.count(), 1)