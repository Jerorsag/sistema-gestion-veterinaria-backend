"""
Configuración de URLs del módulo de Consultas.

Este archivo define todas las rutas de la API para el módulo de gestión de consultas.

Estructura de URLs:
- /api/consultas/ → Gestión de consultas veterinarias
- /api/historias-clinicas/ → Vista consolidada de historias clínicas
- /api/prescripciones/ → Gestión de medicamentos recetados
- /api/examenes/ → Gestión de exámenes médicos
- /api/vacunas/ → Gestión de historial de vacunas

Además de las rutas custom definidas con @action en cada ViewSet.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.consulta_views import ConsultaViewSet
from .views.historia_clinica_views import HistoriaClinicaViewSet
from .views.prescripcion_views import PrescripcionViewSet
from .views.examen_views import ExamenViewSet
from .views.vacuna_views import HistorialVacunaViewSet


# Crear el router de Django REST Framework
router = DefaultRouter()


# Consultas: /api/consultas/
router.register(r'consultas',ConsultaViewSet,basename='consulta')

# Historias Clínicas: /api/historias-clinicas/
router.register(r'historias-clinicas', HistoriaClinicaViewSet,basename='historia-clinica')

# Prescripciones: /api/prescripciones/
router.register(r'prescripciones', PrescripcionViewSet, basename='prescripcion')

# Exámenes: /api/examenes/
router.register(r'examenes', ExamenViewSet, basename='examen')

# Vacunas: /api/vacunas/
router.register(r'vacunas', HistorialVacunaViewSet, basename='vacuna')

# Nombre de la app para namespacing
app_name = 'consultas'

# Patrones de URL
urlpatterns = [
    # Incluir todas las rutas generadas por el router
    path('', include(router.urls)),
]