from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from transacciones.services.factura_service import FacturaService


class CrearFacturaDesdeCita(APIView):
    def post(self, request, cita_id):
        factura = FacturaService.crear_factura_desde_cita(cita_id)
        return Response({
            "message": "Factura creada desde cita",
            "factura_id": factura.id
        }, status=status.HTTP_201_CREATED)


class CrearFacturaDesdeConsulta(APIView):
    def post(self, request, consulta_id):
        factura = FacturaService.crear_factura_desde_consulta(consulta_id)
        return Response({
            "message": "Factura creada desde consulta",
            "factura_id": factura.id
        }, status=status.HTTP_201_CREATED)