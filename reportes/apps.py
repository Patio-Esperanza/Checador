from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes'
    
    def ready(self):
        """Se ejecuta cuando la app está lista"""
        # Solo iniciar scheduler en el proceso principal (no en migraciones, etc.)
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # En desarrollo con runserver
            from reportes.scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception as e:
                print(f"Error al iniciar scheduler: {e}")
        elif 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            # En producción con gunicorn
            from reportes.scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception as e:
                print(f"Error al iniciar scheduler: {e}")
