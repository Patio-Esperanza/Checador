"""
Configuración del scheduler para reportes automáticos
"""
from datetime import datetime, timedelta
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from reportes.models import ConfiguracionReporte
from reportes.services.email_service import EmailReportService


def enviar_reporte_semanal_job():
    """
    Job que se ejecuta semanalmente para enviar el reporte
    """
    print(f"[{timezone.now()}] Ejecutando job de reporte semanal...")
    
    # Calcular periodo (semana actual: lunes hasta hoy)
    hoy = timezone.now().date()
    dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
    fecha_inicio = hoy - timedelta(days=dias_desde_lunes)  # Lunes de esta semana
    fecha_fin = hoy  # Hasta hoy
    
    # Enviar reporte
    email_service = EmailReportService(fecha_inicio, fecha_fin)
    resultado = email_service.enviar_reporte_semanal()
    
    if resultado['success']:
        print(f"✓ {resultado['message']}")
    else:
        print(f"✗ {resultado['message']}")


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Elimina ejecuciones de jobs antiguas (por defecto: mayores a 7 días)
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """
    Inicia el scheduler con los jobs configurados
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Obtener configuración
    try:
        config = ConfiguracionReporte.objects.first()
        if not config:
            # Crear configuración por defecto si no existe
            config = ConfiguracionReporte.objects.create(
                dia_envio=1,  # Lunes
                hora_envio='08:00:00'
            )
            print("Configuración de reporte creada con valores por defecto")
        
        if config.activo:
            # Configurar job semanal
            # dia_envio: 1=Lunes, 2=Martes, ..., 7=Domingo
            # APScheduler usa: 0=Lunes, 1=Martes, ..., 6=Domingo
            day_of_week = config.dia_envio - 1 if config.dia_envio > 0 else 0
            
            hora = config.hora_envio.hour
            minuto = config.hora_envio.minute
            
            scheduler.add_job(
                enviar_reporte_semanal_job,
                trigger=CronTrigger(
                    day_of_week=day_of_week,
                    hour=hora,
                    minute=minuto
                ),
                id="enviar_reporte_semanal",
                max_instances=1,
                replace_existing=True,
                name="Envío de reporte semanal de asistencias"
            )
            
            dia_nombre = dict(ConfiguracionReporte.DIA_SEMANA_CHOICES).get(config.dia_envio)
            print(f"✓ Scheduler configurado: Reporte cada {dia_nombre} a las {config.hora_envio}")
        else:
            print("⚠ Scheduler no iniciado: El envío de reportes está desactivado")
            return None
            
    except Exception as e:
        print(f"Error al configurar scheduler: {e}")
        return None
    
    # Job para limpiar ejecuciones antiguas (diario a las 00:00)
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(hour=0, minute=0),
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
        name="Limpiar ejecuciones antiguas de jobs"
    )
    
    # Iniciar scheduler
    scheduler.start()
    print("✓ Scheduler de reportes iniciado correctamente")
    
    return scheduler
