"""
URL configuration for clinica_veterinaria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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

    # API v1
    path('api/v1/', include('usuarios.urls')),
    path('api/v1/', include('mascotas.urls')),
    path('api/v1/', include('consultas.urls')),
    path('api/v1/', include('inventario.urls')),
    path('api/v1/', include('citas.urls')),

    # OpenAPI schema + UIs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Personalización del admin
admin.site.site_header = "Sistema de Gestión Veterinaria"
admin.site.site_title = "SGV Admin"
admin.site.index_title = "Panel de Administración"