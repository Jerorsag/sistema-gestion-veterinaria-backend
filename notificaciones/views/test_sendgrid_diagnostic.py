"""
Endpoint de diagnóstico completo para SendGrid.
Verifica permisos del API Key y estado del email remitente.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from sendgrid import SendGridAPIClient
from django.conf import settings
import os
import traceback

class TestSendGridDiagnosticView(APIView):
    """
    Diagnóstico completo de SendGrid: verifica API Key y email remitente.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Endpoint GET para diagnóstico sin enviar email."""
        diagnostic = {
            'api_key_status': 'unknown',
            'api_key_info': {},
            'from_email_status': 'unknown',
            'from_email': None,
            'recommendations': []
        }
        
        try:
            # 1. Verificar API Key
            api_key = (
                getattr(settings, 'SENDGRID_API_KEY', None) or 
                getattr(settings, 'EMAIL_HOST_PASSWORD', None) or
                os.getenv('SENDGRID_API_KEY') or
                os.getenv('EMAIL_HOST_PASSWORD')
            )
            
            if not api_key:
                diagnostic['api_key_status'] = 'not_found'
                diagnostic['recommendations'].append(
                    '❌ SENDGRID_API_KEY no está configurado en Render Dashboard'
                )
                return Response({
                    'success': False,
                    'diagnostic': diagnostic,
                    'message': 'SENDGRID_API_KEY no configurado'
                }, status=status.HTTP_200_OK)
            
            api_key = api_key.strip()
            api_key_preview = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else "***"
            
            diagnostic['api_key_info'] = {
                'preview': api_key_preview,
                'length': len(api_key),
                'starts_with': api_key[:3] if len(api_key) >= 3 else 'N/A',
                'format_valid': api_key.startswith('SG.') if len(api_key) >= 3 else False
            }
            
            # 2. Verificar formato del API Key
            if not api_key.startswith('SG.'):
                diagnostic['api_key_status'] = 'invalid_format'
                diagnostic['recommendations'].append(
                    '❌ El API Key no tiene el formato correcto (debe empezar con "SG.")'
                )
            else:
                diagnostic['api_key_status'] = 'format_valid'
                diagnostic['recommendations'].append(
                    '✅ El formato del API Key es correcto'
                )
            
            # 3. Intentar verificar permisos haciendo una llamada simple a la API
            try:
                sg = SendGridAPIClient(api_key)
                # Intentar obtener información del usuario (requiere permisos básicos)
                response = sg.client.user.profile.get()
                if response.status_code == 200:
                    diagnostic['api_key_status'] = 'valid_with_permissions'
                    diagnostic['recommendations'].append(
                        '✅ El API Key es válido y tiene permisos básicos'
                    )
                else:
                    diagnostic['api_key_status'] = 'invalid_or_no_permissions'
                    diagnostic['recommendations'].append(
                        f'⚠️ El API Key puede no tener permisos suficientes (Status: {response.status_code})'
                    )
            except Exception as api_error:
                if '401' in str(api_error) or 'Unauthorized' in str(api_error):
                    diagnostic['api_key_status'] = 'unauthorized'
                    diagnostic['recommendations'].extend([
                        '❌ El API Key no tiene permisos o está incorrecto',
                        '   → Ve a SendGrid Dashboard > Settings > API Keys',
                        '   → Verifica que el API Key tenga "Full Access" o al menos "Mail Send"',
                        '   → Si es necesario, crea un nuevo API Key con "Full Access"'
                    ])
                else:
                    diagnostic['api_key_status'] = 'error_checking'
                    diagnostic['recommendations'].append(
                        f'⚠️ Error al verificar permisos: {str(api_error)}'
                    )
            
            # 4. Verificar email remitente
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sgvnotificaciones15@gmail.com')
            
            # Parsear from_email si tiene formato "Nombre <email>"
            if '<' in from_email and '>' in from_email:
                import re
                match = re.match(r'(.+?)\s*<(.+?)>', from_email)
                if match:
                    from_email = match.group(2).strip()
            
            diagnostic['from_email'] = from_email
            
            # Intentar verificar si el email está verificado (esto requiere permisos adicionales)
            try:
                sg = SendGridAPIClient(api_key)
                # Intentar obtener información del sender
                response = sg.client.verified_senders.get()
                if response.status_code == 200:
                    verified_emails = []
                    try:
                        body = response.body
                        if isinstance(body, bytes):
                            import json
                            body = json.loads(body.decode('utf-8'))
                        if isinstance(body, dict) and 'results' in body:
                            verified_emails = [sender.get('from', {}).get('email', '') for sender in body.get('results', [])]
                    except:
                        pass
                    
                    if from_email in verified_emails:
                        diagnostic['from_email_status'] = 'verified'
                        diagnostic['recommendations'].append(
                            f'✅ El email remitente "{from_email}" está verificado'
                        )
                    else:
                        diagnostic['from_email_status'] = 'not_verified'
                        diagnostic['recommendations'].extend([
                            f'❌ El email remitente "{from_email}" NO está verificado',
                            '   → Ve a SendGrid Dashboard > Settings > Sender Authentication',
                            '   → Haz clic en "Verify a Single Sender"',
                            '   → Ingresa el email y confirma la verificación desde tu correo'
                        ])
                else:
                    diagnostic['from_email_status'] = 'cannot_check'
                    diagnostic['recommendations'].append(
                        '⚠️ No se pudo verificar el estado del email remitente (puede requerir permisos adicionales)'
                    )
            except Exception as email_error:
                diagnostic['from_email_status'] = 'error_checking'
                diagnostic['recommendations'].append(
                    f'⚠️ Error al verificar email remitente: {str(email_error)}'
                )
            
            # 5. Resumen y recomendaciones finales
            if diagnostic['api_key_status'] in ['unauthorized', 'invalid_format', 'not_found']:
                diagnostic['recommendations'].append(
                    '\n🔧 ACCIÓN REQUERIDA: Corrige el problema del API Key antes de continuar'
                )
            
            if diagnostic['from_email_status'] == 'not_verified':
                diagnostic['recommendations'].append(
                    '\n🔧 ACCIÓN REQUERIDA: Verifica el email remitente en SendGrid'
                )
            
            success = (
                diagnostic['api_key_status'] in ['valid_with_permissions', 'format_valid'] and
                diagnostic['from_email_status'] in ['verified', 'cannot_check']
            )
            
            return Response({
                'success': success,
                'diagnostic': diagnostic,
                'message': 'Diagnóstico completado' if success else 'Se encontraron problemas que deben resolverse'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'diagnostic': diagnostic,
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

