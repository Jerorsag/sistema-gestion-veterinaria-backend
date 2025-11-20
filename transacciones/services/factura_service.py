from datetime import datetime
from transacciones.models.factura import Factura
from transacciones.models.pago import Pago
from transacciones.models.detalle_factura import DetalleFactura
from citas.models import Cita
from consultas.models import Consulta
from django.core.exceptions import ValidationError
from transacciones.patterns.state_factory import EstadoFacturaFactory
from notificaciones.patterns.strategies.factura_email import FacturaGeneradaEmail, FacturaPagadaEmail


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

        context = {
            "cliente_nombre": factura.cliente.get_full_name(),
            "factura_id": factura.id,
            "fecha_emision": factura.fecha.strftime("%d/%m/%Y %H:%M"),
            "estado": factura.estado,
            "total": factura.total,
            "detalles": factura.detalles.all(),
            "url_historial": "https://frontend/usuario/facturas",
            "anio_actual": datetime.now().year,
        }

        FacturaGeneradaEmail(context, factura.cliente.email).send()

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

        context = {
            "cliente_nombre": factura.cliente.get_full_name(),
            "factura_id": factura.id,
            "fecha_emision": factura.fecha.strftime("%d/%m/%Y %H:%M"),
            "estado": factura.estado,
            "total": factura.total,
            "detalles": factura.detalles.all(),
            "url_historial": "https://frontend/usuario/facturas",
            "anio_actual": datetime.now().year,
        }

        FacturaGeneradaEmail(context, factura.cliente.email).send()
        
        return factura
    
    
    @staticmethod
    def pagar_factura(factura_id, metodo_pago, monto, referencia=""):
        factura = Factura.objects.get(id=factura_id)

        pago = Pago.objects.create(
            factura=factura,
            metodo=metodo_pago,    # Aquí ya es MetodoPago
            monto=monto,
            referencia=referencia
        )

        if factura.estado == "PAGADA":
            context = {
                "cliente_nombre": factura.cliente.get_full_name(),
                "factura_id": factura.id,
                "total": factura.total,
                "metodo_pago": pago.metodo.nombre,  
                "fecha_pago": pago.fecha.strftime("%d/%m/%Y %H:%M"),  
                "detalles": factura.detalles.all(),
            }

            FacturaPagadaEmail(context, factura.cliente.email).send()

        return factura
    

    @staticmethod
    def anular_factura(factura_id):
        factura = Factura.objects.get(id=factura_id)
        estado = EstadoFacturaFactory.obtener_estado(factura.estado)

        # Aplicar lógica de cambio de estado
        estado.anular(factura)

        return factura