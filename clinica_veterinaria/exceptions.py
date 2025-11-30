"""
Handler de excepciones personalizado para asegurar que siempre se devuelva JSON.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Handler personalizado de excepciones que siempre devuelve JSON.
    """
    # Llamar al handler por defecto de DRF
    response = exception_handler(exc, context)
    
    # Si DRF no maneja la excepción, crear una respuesta JSON
    if response is None:
        # Log del error para debugging
        logger.error(f"Excepción no manejada: {type(exc).__name__}: {str(exc)}")
        
        # Crear respuesta JSON genérica
        response = Response(
            {
                'detail': str(exc) if str(exc) else 'Ha ocurrido un error',
                'error_type': type(exc).__name__
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    else:
        # Asegurar que la respuesta tenga el formato correcto
        if not isinstance(response.data, dict):
            response.data = {'detail': str(response.data)}
    
    return response

