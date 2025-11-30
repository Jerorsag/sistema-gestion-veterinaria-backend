"""
Endpoint para probar SendGrid API directamente (siguiendo la documentación oficial).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
import os
import traceback

class TestSendGridDirectView(APIView):
    """
    Prueba SendGrid API directamente siguiendo la documentación oficial.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        to_email = request.data.get('email', 'jrodriguez_25@cue.edu.co')
        
        try:
            # Obtener API Key (igual que en el backend)
            api_key = (
                getattr(settings, 'SENDGRID_API_KEY', None) or 
                getattr(settings, 'EMAIL_HOST_PASSWORD', None) or
                os.getenv('SENDGRID_API_KEY') or
                os.getenv('EMAIL_HOST_PASSWORD')
            )
            
            if not api_key:
                return Response({
                    'success': False,
                    'error': 'SENDGRID_API_KEY no está configurado'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Limpiar el API Key completamente (igual que en el backend)
            api_key = str(api_key).strip()
            # Eliminar comillas si están al inicio/final
            if (api_key.startswith('"') and api_key.endswith('"')) or \
               (api_key.startswith("'") and api_key.endswith("'")):
                api_key = api_key[1:-1].strip()
            # Eliminar saltos de línea y espacios múltiples
            api_key = api_key.replace('\n', '').replace('\r', '').replace('\t', '')
            while '  ' in api_key:
                api_key = api_key.replace('  ', ' ')
            
            # Log del API Key (parcial)
            api_key_preview = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else "***"
            print(f"📧 Usando API Key: {api_key_preview}")
            print(f"📧 Longitud: {len(api_key)} caracteres")
            print(f"📧 Empieza con: {api_key[:3]}")
            print(f"📧 Termina con: ...{api_key[-3:]}")
            
            # Crear cliente SendGrid (siguiendo documentación oficial)
            sg = SendGridAPIClient(api_key)
            
            # Crear mensaje (siguiendo documentación oficial)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sgvnotificaciones15@gmail.com')
            
            # Parsear from_email si tiene formato "Nombre <email>"
            if '<' in from_email and '>' in from_email:
                import re
                match = re.match(r'(.+?)\s*<(.+?)>', from_email)
                if match:
                    from_email = match.group(2).strip()
            
            print(f"📧 From email: {from_email}")
            print(f"📧 To email: {to_email}")
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject='Test Email desde Render - SendGrid API',
                plain_text_content='Este es un correo de prueba usando SendGrid API directamente.',
                html_content='<h1>Test Email</h1><p>Este es un correo de prueba usando SendGrid API directamente.</p>'
            )
            
            # Enviar (siguiendo documentación oficial)
            print(f"📧 Enviando email via SendGrid API...")
            response = sg.send(message)
            
            print(f"📧 Respuesta de SendGrid:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {response.headers}")
            print(f"   Body: {response.body}")
            
            if response.status_code in [200, 201, 202]:
                return Response({
                    'success': True,
                    'message': f'Email enviado exitosamente a {to_email}',
                    'status_code': response.status_code,
                    'api_key_preview': api_key_preview
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Error al enviar email',
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.body.decode('utf-8') if response.body else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            # Diagnóstico específico para error 401
            diagnostic_info = {}
            if '401' in str(e) or 'Unauthorized' in str(e):
                diagnostic_info = {
                    'possible_causes': [
                        'El API Key no tiene permisos de "Mail Send"',
                        'El email remitente no está verificado en SendGrid',
                        'El API Key está incorrecto o ha sido revocado',
                        'El API Key no tiene acceso completo (Full Access)'
                    ],
                    'steps_to_fix': [
                        '1. Ve a SendGrid Dashboard > Settings > API Keys',
                        '2. Verifica que tu API Key tenga permisos "Mail Send" o "Full Access"',
                        '3. Ve a Settings > Sender Authentication',
                        '4. Verifica que el email "sgvnotificaciones15@gmail.com" esté verificado',
                        '5. Si no está verificado, haz clic en "Verify a Single Sender"',
                        '6. Revisa tu email y confirma la verificación',
                        '7. Si el problema persiste, crea un nuevo API Key con "Full Access"'
                    ],
                    'api_key_info': {
                        'preview': api_key_preview if 'api_key_preview' in locals() else 'N/A',
                        'length': len(api_key) if 'api_key' in locals() else 0,
                        'starts_with': api_key[:3] if 'api_key' in locals() and len(api_key) >= 3 else 'N/A'
                    },
                    'from_email': from_email if 'from_email' in locals() else 'N/A'
                }
            
            print("=" * 50)
            print("TEST SENDGRID DIRECT - ERROR:")
            print(f"  Error: {str(e)}")
            print(f"  Tipo: {type(e).__name__}")
            if diagnostic_info:
                print("\n🔍 DIAGNÓSTICO 401:")
                print("   Posibles causas:")
                for cause in diagnostic_info.get('possible_causes', []):
                    print(f"   - {cause}")
                print("\n   Pasos para resolver:")
                for step in diagnostic_info.get('steps_to_fix', []):
                    print(f"   {step}")
            print("  Traceback:")
            print(traceback.format_exc())
            print("=" * 50)
            
            response_data = {
                'success': False,
                'message': 'Error al enviar email',
                'details': error_details
            }
            
            if diagnostic_info:
                response_data['diagnostic'] = diagnostic_info
            
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

