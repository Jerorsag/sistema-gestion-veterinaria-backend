from django.apps import AppConfig

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinica_veterinaria.inventario'

    def ready(self):
        # Importa las señales para activar el patrón Observer
        import clinica_veterinaria.inventario.signals
