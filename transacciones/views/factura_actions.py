from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from transacciones.services.factura_service import FacturaService
from transacciones.serializers.factura_serializer import FacturaSerializer
from transacciones.models.metodo_pago import MetodoPago
from transacciones.models.factura import Factura
from notificaciones.patterns.strategies.factura_email import FacturaEnvioManualEmail

class PagarFacturaView(APIView):

    def post(self, request, factura_id):

        metodo_id = request.data.get("metodo_pago")
        monto = request.data.get("monto")
        referencia = request.data.get("referencia", "")

        if not metodo_id or not monto:
            return Response(
                {"error": "Debe enviar 'metodo_pago' y 'monto'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            metodo = MetodoPago.objects.get(id=metodo_id)
        except MetodoPago.DoesNotExist:
            return Response(
                {"error": "Método de pago no válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        factura = FacturaService.pagar_factura(
            factura_id=factura_id,
            metodo_pago=metodo,
            monto=monto,
            referencia=referencia
        )

        return Response(
            {"message": "Factura pagada correctamente.", "factura_id": factura.id, "estado": factura.estado},
            status=status.HTTP_200_OK
        )


class AnularFacturaView(APIView):

    def post(self, request, factura_id):
        factura = FacturaService.anular_factura(factura_id)
        return Response(FacturaSerializer(factura).data)
    

class EnviarFacturaEmailView(APIView):
    def post(self, request, factura_id):
        try:
            factura = Factura.objects.get(id=factura_id)

            context = {
                "cliente_nombre": factura.cliente.get_full_name(),
                "factura_id": factura.id,
                "total": factura.total,
                "fecha": factura.fecha.strftime("%d/%m/%Y %H:%M"),
                "estado": factura.estado,
                "detalles": factura.detalles.all()
            }

            FacturaEnvioManualEmail(context, factura.cliente.email).send()

            return Response(
                {"mensaje": "Factura enviada correctamente."},
                status=status.HTTP_200_OK
            )
        except Factura.DoesNotExist:
            return Response({"error": "Factura no encontrada"}, status=404)