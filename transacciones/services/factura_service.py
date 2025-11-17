from transacciones.models.factura import Factura
from transacciones.models.detalle_factura import DetalleFactura
from citas.models import Cita
from consultas.models import Consulta
from inventario.models import Producto
from django.core.exceptions import ValidationError


class FacturaService:

    @staticmethod
    def crear_factura_desde_cita(cita_id):
        try:
            cita = Cita.objects.get(id=cita_id)
        except Cita.DoesNotExist:
            raise ValidationError("La cita no existe.")

        if not cita.servicio:
            raise ValidationError("La cita no tiene un servicio asignado.")

        factura = Factura.objects.create(
            cliente=cita.mascota.cliente.usuario,
            cita=cita,
            total=0
        )

        # Crear detalle por el servicio
        DetalleFactura.objects.create(
            factura=factura,
            servicio=cita.servicio,
            cantidad=1,
            precio_unitario=cita.servicio.costo, 
            subtotal=cita.servicio.costo
        )

        factura.recalcular_totales()
        return factura

    @staticmethod
    def crear_factura_desde_consulta(consulta_id):
        try:
            consulta = Consulta.objects.get(id=consulta_id)
        except Consulta.DoesNotExist:
            raise ValidationError("La consulta no existe.")

        factura = Factura.objects.create(
            cliente=consulta.mascota.cliente.usuario,
            consulta=consulta,
            total=0
        )

        # Agregar productos prescritos (medicamentos)
        for prescripcion in consulta.prescripciones.all():
            producto = prescripcion.medicamento   

            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,                
                cantidad=prescripcion.cantidad,
                precio_unitario=producto.precio_venta, 
                subtotal=producto.precio_venta * prescripcion.cantidad
            )

        factura.recalcular_totales()
        return factura