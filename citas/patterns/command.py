from datetime import datetime
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from citas.patterns.composite import obtener_horarios_disponibles
from ..models import Cita, Servicio
from .state import EstadoCita
from usuarios.models import Usuario
from mascotas.models import Mascota
from citas.signals import cita_agendada_signal,  cita_cancelada_signal, cita_reagendada_signal



def agendar_nueva_cita(data: dict, usuario: Usuario) -> Cita:
    """
    Servicio (Patrón Command) para crear una nueva cita (RF-004).
    Se encarga de orquestar la validación, creación y notificación de una nueva cita.
    """
    mascota_id = data.get('mascota_id')
    veterinario_id = data.get('veterinario_id')
    servicio_id = data.get('servicio_id')
    fecha_hora_input = data.get('fecha_hora')

    # --- Manejo robusto de fecha y hora ---
    fecha_hora = None

    if isinstance(fecha_hora_input, str):
        # Si viene como string (desde JSON)
        fecha_str = fecha_hora_input.rstrip("Z")
        try:
            fecha_hora = datetime.fromisoformat(fecha_str)
        except ValueError:
            raise ValidationError("Formato de fecha inválido. Usa: YYYY-MM-DDThh:mm:ssZ")

        if timezone.is_naive(fecha_hora):  # sin zona horaria
            fecha_hora = timezone.make_aware(fecha_hora)

    elif isinstance(fecha_hora_input, datetime):
        # Si ya viene como datetime (DRF lo parseó)
        fecha_hora = fecha_hora_input if timezone.is_aware(fecha_hora_input) else timezone.make_aware(fecha_hora_input)

    else:
        raise ValidationError("El campo 'fecha_hora' tiene un tipo no válido.")

    # --- Validación de lógica de negocio ---
    try:
        mascota = Mascota.objects.get(id=mascota_id)
        veterinario = Usuario.objects.get(id=veterinario_id)
        servicio = Servicio.objects.get(id=servicio_id)
    except (Mascota.DoesNotExist, Usuario.DoesNotExist, Servicio.DoesNotExist):
        raise ValidationError("La mascota, veterinario o servicio no existen.")

    # --- Permisos ---
    if 'cliente' in [r.rol.nombre for r in usuario.usuario_roles.all()]:
        if mascota.cliente.usuario != usuario:
            raise PermissionDenied("No tienes permiso para agendar citas para esta mascota.")

    # --- Validación de fecha ---
    if fecha_hora < timezone.now():
        raise ValidationError("No se pueden agendar citas en el pasado.")

    # --- Verificar disponibilidad ---
    horarios_libres = obtener_horarios_disponibles(veterinario.id, fecha_hora.date())
    if fecha_hora.strftime("%H:%M") not in horarios_libres:
        raise ValidationError("El veterinario no está disponible a esta hora.")

    # --- Crear la cita ---
    cita = Cita.objects.create(
        mascota=mascota,
        veterinario=veterinario,
        servicio=servicio,
        fecha_hora=fecha_hora,
        observaciones=data.get('observaciones', ''),
        estado=EstadoCita.AGENDADA
    )

    # --- Notificar ---
    cita_agendada_signal.send(sender=Cita, cita=cita)

    return cita

def cancelar_cita(cita_id: str, usuario: Usuario) -> Cita:
    """
    Servicio (Patrón Command) para cancelar una cita (RF-007).
    Implementa Patrón State (Agendada -> Cancelada).
    Implementa Patrón Observer (Notifica cancelación).

    RESPONSABILIDAD: Orquestar la validación, cambio de estado (cancelación)
    y notificación de una cita.
    """
    try:
        cita = Cita.objects.get(id=cita_id)
    except Cita.DoesNotExist:
        raise ValidationError("La cita no existe.")

    # Verificación de permisos (RF-007):
    es_propietario = cita.mascota.cliente.usuario == usuario
    roles_usuario = [r.rol.nombre for r in usuario.usuario_roles.all()]
    es_rol_administrativo = any(r in ['recepcionista', 'administrador', 'veterinario'] for r in roles_usuario)

    if not es_propietario and not es_rol_administrativo:
        raise PermissionDenied("No tienes permiso para cancelar esta cita.")

    # Lógica del Patrón State
    if cita.estado == EstadoCita.CANCELADA:
        raise ValidationError("Esta cita ya ha sido cancelada.")
    if cita.estado == EstadoCita.COMPLETADA:
        raise ValidationError("No se puede cancelar una cita ya completada.")

    cita.estado  = EstadoCita.CANCELADA
    cita.save()

    # Llamada al servicio de notificación
    cita_cancelada_signal.send(sender=Cita, cita=cita)

    return cita


def reagendar_cita(cita_id: str, nueva_fecha_hora_str: str, usuario: Usuario) -> Cita:
    """
    Servicio (Patrón Command) para reagendar una cita (RF-006).
    
    RESPONSABILIDAD: Orquestar la validación, cambio de fecha,
    y notificación de una cita.
    """
    try:
        cita = Cita.objects.get(id=cita_id)
    except Cita.DoesNotExist:
        raise ValidationError("La cita no existe.")

    # Verificación de permisos
    es_propietario = cita.mascota.cliente.usuario == usuario
    roles_usuario = [r.rol.nombre for r in usuario.usuario_roles.all()]
    es_rol_administrativo = any(r in ['recepcionista', 'administrador'] for r in roles_usuario)

    if not es_propietario and not es_rol_administrativo:
        raise PermissionDenied("No tienes permiso para reagendar esta cita.")

    # --- Lógica de Negocio ---
    # 1. Validar la nueva hora
    nueva_fecha_hora = timezone.make_aware(datetime.fromisoformat(nueva_fecha_hora_str.rstrip("Z")))

    # ¡REUTILIZAMOS el servicio de disponibilidad!
    horarios_libres = obtener_horarios_disponibles(cita.veterinario.id, nueva_fecha_hora.date())

    if nueva_fecha_hora.strftime("%H:%M") not in horarios_libres:
        raise ValidationError("Conflicto de Horario: El veterinario no está disponible a esta hora.")

    # 2. Actualizar
    cita.fecha_hora = nueva_fecha_hora
    cita.estado = EstadoCita.AGENDADA # Reactivamos si estaba cancelada
    cita.save()

    # 3. Notificar
    cita_reagendada_signal.send(sender=Cita, cita=cita)

    return cita
