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
import logging

logger = logging.getLogger(__name__)

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
                        
                        # SendGrid puede devolver la lista en diferentes formatos
                        if isinstance(body, dict):
                            # Formato 1: {'results': [{'from': {'email': '...'}}, ...]}
                            if 'results' in body:
                                for sender in body.get('results', []):
                                    # Puede venir como sender['from']['email'] o sender['email']
                                    email = None
                                    if isinstance(sender, dict):
                                        if 'from' in sender and isinstance(sender['from'], dict):
                                            email = sender['from'].get('email', '')
                                        elif 'email' in sender:
                                            email = sender.get('email', '')
                                        elif 'from_email' in sender:
                                            email = sender.get('from_email', '')
                                    
                                    if email:
                                        verified_emails.append(email.lower())
                            
                            # Formato 2: Lista directa
                            elif isinstance(body, list):
                                for sender in body:
                                    if isinstance(sender, dict):
                                        email = sender.get('from', {}).get('email', '') or sender.get('email', '')
                                        if email:
                                            verified_emails.append(email.lower())
                        
                        # También buscar en otros campos posibles
                        if not verified_emails and isinstance(body, dict):
                            # Buscar en cualquier campo que contenga 'email'
                            def extract_emails(obj, emails_list):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if 'email' in key.lower() and isinstance(value, str) and '@' in value:
                                            emails_list.append(value.lower())
                                        else:
                                            extract_emails(value, emails_list)
                                elif isinstance(obj, list):
                                    for item in obj:
                                        extract_emails(item, emails_list)
                            
                            extract_emails(body, verified_emails)
                            
                    except Exception as parse_error:
                        print(f"⚠️ Error parseando respuesta de verified_senders: {parse_error}")
                        print(f"   Body recibido: {body if 'body' in locals() else 'N/A'}")
                        # Si no podemos parsear, asumimos que no podemos verificar
                        pass
                    
                    # Verificar si el email está en la lista (comparación case-insensitive)
                    from_email_lower = from_email.lower()
                    if verified_emails and from_email_lower in verified_emails:
                        diagnostic['from_email_status'] = 'verified'
                        diagnostic['recommendations'].append(
                            f'✅ El email remitente "{from_email}" está verificado'
                        )
                    elif verified_emails:
                        # Hay emails verificados pero este no está en la lista
                        diagnostic['from_email_status'] = 'not_in_list'
                        diagnostic['recommendations'].extend([
                            f'⚠️ El email "{from_email}" no aparece en la lista de emails verificados',
                            f'   Emails verificados encontrados: {", ".join(verified_emails[:3])}...',
                            '   → Si el email está verificado en el Dashboard, esto puede ser un problema de permisos de la API',
                            '   → El email puede funcionar correctamente aunque no aparezca aquí'
                        ])
                    else:
                        # No se pudieron extraer emails de la respuesta
                        diagnostic['from_email_status'] = 'cannot_parse_response'
                        diagnostic['recommendations'].append(
                            '⚠️ No se pudo extraer la lista de emails verificados de la respuesta de SendGrid'
                        )
                else:
                    diagnostic['from_email_status'] = 'cannot_check'
                    diagnostic['recommendations'].append(
                        f'⚠️ No se pudo verificar el estado del email remitente (Status: {response.status_code})'
                    )
            except Exception as email_error:
                diagnostic['from_email_status'] = 'error_checking'
                error_str = str(email_error)
                # Si es un error 403, probablemente no tiene permisos para verificar
                if '403' in error_str or 'Forbidden' in error_str:
                    diagnostic['recommendations'].append(
                        '⚠️ No se tienen permisos para verificar el estado del email remitente vía API',
                        '   → Si el email está verificado en SendGrid Dashboard, debería funcionar correctamente',
                        '   → El error 401 al enviar emails puede deberse a otro problema'
                    )
                else:
                    diagnostic['recommendations'].append(
                        f'⚠️ Error al verificar email remitente: {error_str}'
                    )
            
            # 5. Resumen y recomendaciones finales
            if diagnostic['api_key_status'] in ['unauthorized', 'invalid_format', 'not_found']:
                diagnostic['recommendations'].append(
                    '\n🔧 ACCIÓN REQUERIDA: Corrige el problema del API Key antes de continuar'
                )
            
            # Solo marcar como error crítico si realmente no está verificado
            # Si no podemos verificar vía API pero el API Key es válido, asumimos que está bien
            if diagnostic['from_email_status'] == 'not_verified':
                diagnostic['recommendations'].append(
                    '\n🔧 ACCIÓN REQUERIDA: Verifica el email remitente en SendGrid'
                )
            elif diagnostic['from_email_status'] in ['cannot_check', 'error_checking', 'cannot_parse_response', 'not_in_list']:
                # Si el API Key es válido, probablemente el email también lo está
                # Solo no podemos verificarlo vía API
                if diagnostic['api_key_status'] in ['valid_with_permissions', 'format_valid']:
                    diagnostic['recommendations'].append(
                        '\n✅ NOTA: No se pudo verificar el email vía API, pero si está verificado en SendGrid Dashboard, debería funcionar'
                    )
            
            # El éxito depende principalmente del API Key
            # Si el API Key es válido, asumimos que puede funcionar aunque no podamos verificar el email
            success = diagnostic['api_key_status'] in ['valid_with_permissions', 'format_valid']
            
            # Si el email está verificado, mejor aún
            if diagnostic['from_email_status'] == 'verified':
                success = True
            
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

