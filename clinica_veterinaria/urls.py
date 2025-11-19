from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings


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
            'health': request.build_absolute_uri('/api/health/')
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Root
    path('api/', api_root, name='api_root'),

    # Health check
    path('api/health/', health, name='health'),

    # API v1
    #path('api/v1/', include('usuarios.urls')),
    #path('api/v1/', include('mascotas.urls')),
    path('api/v1/', include('inventario.urls')),
]

# 👇 Agrega esto al final del archivo
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Personalización del admin
admin.site.site_header = "Sistema de Gestión Veterinaria"
admin.site.site_title = "SGV Admin"
admin.site.index_title = "Panel de Administración"
