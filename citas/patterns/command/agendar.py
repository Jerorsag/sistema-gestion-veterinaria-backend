from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from citas.models import Cita, Servicio
from mascotas.models import Mascota
from usuarios.models import Usuario
from citas.patterns.state import EstadoCita
from citas.patterns.composite import obtener_cupos_disponibles, AgendaDiaria
from citas.signals import cita_agendada_signal

from .interface import ICommand
from .utils import parsear_fecha_hora

class AgendarCitaCommand(ICommand):
    def __init__(self, data: dict, usuario: Usuario):
        self.data = data
        self.usuario = usuario

    def execute(self) -> Cita:
        mascota_id = self.data.get('mascota_id')
        veterinario_id = self.data.get('veterinario_id')
        servicio_id = self.data.get('servicio_id')
        fecha_hora_input = self.data.get('fecha_hora')

        # 1. Helper
        fecha_hora = parsear_fecha_hora(fecha_hora_input)

        # 2. Validaciones
        try:
            mascota = Mascota.objects.get(id=mascota_id)
            veterinario = Usuario.objects.get(id=veterinario_id)
            servicio = Servicio.objects.get(id=servicio_id)
        except (Mascota.DoesNotExist, Usuario.DoesNotExist, Servicio.DoesNotExist):
            raise ValidationError("La mascota, veterinario o servicio no existen.")

        self._verificar_permisos(mascota)

        if fecha_hora < timezone.now():
            raise ValidationError("No se pueden agendar citas en el pasado.")

        horarios_libres = obtener_cupos_disponibles(veterinario.id, fecha_hora.date())
        if fecha_hora.strftime("%H:%M") not in horarios_libres:
            raise ValidationError("El veterinario no está disponible a esta hora.")

        # 3. Ejecución
        cita = Cita.objects.create(
            mascota=mascota,
            veterinario=veterinario,
            servicio=servicio,
            fecha_hora=fecha_hora,
            observaciones=self.data.get('observaciones', ''),
            estado=EstadoCita.AGENDADA
        )

        cita_agendada_signal.send(sender=Cita, cita=cita)
        return cita

    def _verificar_permisos(self, mascota):
        if hasattr(self.usuario, 'perfil_cliente'):
             if mascota.cliente.usuario != self.usuario:
                raise PermissionDenied("No tienes permiso para esta mascota.")