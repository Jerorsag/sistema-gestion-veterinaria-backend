from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from citas.models import Cita
from citas.patterns.state.state_factory import EstadoCitaFactory
from citas.patterns.composite import obtener_cupos_disponibles, AgendaDiaria
from citas.signals import cita_reagendada_signal
from usuarios.models import Usuario

from .interface import ICommand
from .utils import parsear_fecha_hora

class ReagendarCitaCommand(ICommand):
    def __init__(self, cita_id: int, nueva_fecha_str: str, usuario: Usuario):
        self.cita_id = cita_id
        self.nueva_fecha_str = nueva_fecha_str
        self.usuario = usuario

    def execute(self) -> Cita:
        try:
            cita = Cita.objects.get(id=self.cita_id)
        except Cita.DoesNotExist:
            raise ValidationError("La cita no existe.")

        # 1. Permisos
        es_propietario = cita.mascota.cliente.usuario == self.usuario
        es_admin = self.usuario.usuario_roles.filter(
            rol__nombre__in=['recepcionista', 'administrador']
        ).exists()

        if not es_propietario and not es_admin:
            raise PermissionDenied("No tienes permiso para reagendar esta cita.")

        # 2. Validaciones de Fecha y Disponibilidad
        nueva_fecha = parsear_fecha_hora(self.nueva_fecha_str)

        if nueva_fecha < timezone.now():
             raise ValidationError("No se puede reagendar al pasado.")

        horarios_libres = obtener_cupos_disponibles(cita.veterinario.id, nueva_fecha.date())
        if nueva_fecha.strftime("%H:%M") not in horarios_libres:
            raise ValidationError("El veterinario no está disponible.")

        # 3. Delegar al Estado (Validación de transición y actualización)
        estado_actual = EstadoCitaFactory.obtener_estado(cita.estado)
        estado_actual.reagendar(cita, nueva_fecha) # <- Polimorfismo

        # 4. Notificar
        cita_reagendada_signal.send(sender=Cita, cita=cita)
        return cita