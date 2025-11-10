from datetime import time, timedelta
import datetime
from time import timezone
from rest_framework import status
from .test_base import CitasAPITestCase # <-- Importamos nuestra base
from citas.models import Cita
from citas.patterns.state import EstadoCita # <-- Importamos el State

class AgendamientoTests(CitasAPITestCase):

    def setUp(self):
        """Sobrescribimos el setUp de la clase base para añadir una fecha limpia."""
        # Primero, corremos el setUp() original de CitasAPITestCase
        super().setUp() 
        
        # FIX: Creamos una fecha "limpia" para las pruebas (ej. 10:00 AM)
        # Esto evita el error de enviar horas "sucias" como 10:55:34
        fecha_prueba = timezone.now().date() + timedelta(days=5)
        hora_prueba = time(10, 0) # 10:00 AM exactas
        
        # Convertimos la fecha y hora a un objeto datetime "aware" (consciente de zona horaria)
        self.fecha_hora_limpia = timezone.make_aware(
            datetime.combine(fecha_prueba, hora_prueba)
        )

    def test_agendar_cita_exitosa(self):
        """Prueba de CP-020: Agendar una cita exitosamente."""
        url = '/api/v1/citas/'
        
        # Usamos los IDs de entero (BigAutoField) como define el modelo common
        data = {
            "mascota_id": self.mascota.id,
            "veterinario_id": self.vet_user.id,
            "servicio_id": self.servicio.id,
            "fecha_hora": self.fecha_hora_limpia.isoformat() # Usamos la fecha limpia
        }

        response = self.client.post(url, data, format='json')

        # FIX: Ahora la respuesta debe ser 201
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
            "mascota_id": self.mascota.id,
            "veterinario_id": self.vet_user.id,
            "servicio_id": self.servicio.id,
            "fecha_hora": self.fecha_hora_limpia.isoformat() # Misma fecha y hora
        }

        # 2. Intentar crear la segunda cita (debe fallar)
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # FIX: Comprobamos el mensaje de error real que viene del servicio
        # (El servicio está en `citas/services/disponibilidad.py`)
        self.assertIn("El veterinario no está disponible a esta hora.", str(response.data))
        self.assertEqual(Cita.objects.count(), 1)