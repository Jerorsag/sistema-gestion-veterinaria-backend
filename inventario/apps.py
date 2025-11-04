from django.apps import AppConfig

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'

    def ready(self):
        # Importa las señales para activar el patrón Observer
        import inventario.signals
