from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from notificaciones.views.test_email import TestEmailView

# Importar test_sendgrid_direct solo si existe
try:
    from notificaciones.views.test_sendgrid_direct import TestSendGridDirectView
    TEST_SENDGRID_DIRECT_AVAILABLE = True
except ImportError:
    TEST_SENDGRID_DIRECT_AVAILABLE = False

# Importar test_sendgrid_diagnostic
try:
    from notificaciones.views.test_sendgrid_diagnostic import TestSendGridDiagnosticView
    TEST_SENDGRID_DIAGNOSTIC_AVAILABLE = True
except ImportError:
    TEST_SENDGRID_DIAGNOSTIC_AVAILABLE = False

# Importar create_superuser (temporal)
try:
    from usuarios.views.admin.create_superuser import CreateSuperuserView
    CREATE_SUPERUSER_AVAILABLE = True
except ImportError:
    CREATE_SUPERUSER_AVAILABLE = False

def health(request):
    """Endpoint de health check para monitoreo."""
    return JsonResponse({
        'status': 'ok',
        'service': 'Sistema de Gestión Veterinaria',
        'version': '1.0.0'
    })


def api_root(request):
    """Endpoint raíz de la API con información básica."""
    return JsonResponse({
        'message': 'Bienvenido a la API del Sistema de Gestión Veterinaria',
        'version': '1.0.0',
        'endpoints': {
            'auth': request.build_absolute_uri('/api/v1/auth/'),
            'health': request.build_absolute_uri('/api/health/'),
            'docs': request.build_absolute_uri('/api/docs/'),
            'redoc': request.build_absolute_uri('/api/redoc/')
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Root
    path('api/', api_root, name='api_root'),

    # Health check
    path('api/health/', health, name='health'),
    
    # ⚠️ TEMPORAL: Endpoints de prueba de email (eliminar después)
    path('api/test-email/', TestEmailView.as_view(), name='test_email'),
]

# Agregar endpoints de SendGrid solo si están disponibles
if TEST_SENDGRID_DIRECT_AVAILABLE:
    urlpatterns.append(
        path('api/test-sendgrid-direct/', TestSendGridDirectView.as_view(), name='test_sendgrid_direct')
    )

if TEST_SENDGRID_DIAGNOSTIC_AVAILABLE:
    urlpatterns.append(
        path('api/test-sendgrid-diagnostic/', TestSendGridDiagnosticView.as_view(), name='test_sendgrid_diagnostic')
    )

# ⚠️ TEMPORAL: Endpoint para crear superuser (eliminar después de crear el superuser)
if CREATE_SUPERUSER_AVAILABLE:
    urlpatterns.append(
        path('api/create-superuser/', CreateSuperuserView.as_view(), name='create_superuser')
    )

urlpatterns += [
    # API v1
    path('api/v1/', include('usuarios.urls')),
    path('api/v1/', include('mascotas.urls')),
    path('api/v1/', include('consultas.urls')),
    path('api/v1/', include('inventario.urls')),
    path('api/v1/', include('citas.urls')),
    path('api/v1/', include('transacciones.urls')),

    # OpenAPI schema + UIs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Personalización del admin
admin.site.site_header = "Sistema de Gestión Veterinaria"
admin.site.site_title = "SGV Admin"
admin.site.index_title = "Panel de Administración"
