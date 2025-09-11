from django.apps import AppConfig


class GynecologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gynecology'
    verbose_name = 'Ginecología'
    
    def ready(self):
        # Importar señales si las hay
        pass