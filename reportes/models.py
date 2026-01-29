from django.db import models
from django.core.validators import EmailValidator


class ConfiguracionReporte(models.Model):
    """Configuración para el envío de reportes semanales"""
    
    DIA_SEMANA_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, se enviarán los reportes semanales'
    )
    dia_envio = models.IntegerField(
        choices=DIA_SEMANA_CHOICES,
        default=1,
        verbose_name='Día de Envío',
        help_text='Día de la semana para enviar el reporte (1=Lunes, 7=Domingo)'
    )
    hora_envio = models.TimeField(
        default='08:00:00',
        verbose_name='Hora de Envío',
        help_text='Hora del día para enviar el reporte'
    )
    asunto_correo = models.CharField(
        max_length=255,
        default='Reporte Semanal de Asistencias',
        verbose_name='Asunto del Correo'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
    
    def __str__(self):
        dia = dict(self.DIA_SEMANA_CHOICES).get(self.dia_envio)
        return f"Reporte {dia} a las {self.hora_envio} ({'Activo' if self.activo else 'Inactivo'})"


class DestinatarioReporte(models.Model):
    """Destinatarios para los reportes semanales"""
    
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        validators=[EmailValidator()]
    )
    nombre = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre',
        help_text='Nombre del destinatario (opcional)'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, recibirá los reportes'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Destinatario de Reporte'
        verbose_name_plural = 'Destinatarios de Reportes'
        ordering = ['email']
    
    def __str__(self):
        if self.nombre:
            return f"{self.nombre} <{self.email}>"
        return self.email


class HistorialReporte(models.Model):
    """Historial de reportes enviados"""
    
    ESTADO_CHOICES = [
        ('enviado', 'Enviado'),
        ('error', 'Error'),
    ]
    
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Envío')
    fecha_inicio = models.DateField(verbose_name='Fecha Inicio del Periodo')
    fecha_fin = models.DateField(verbose_name='Fecha Fin del Periodo')
    destinatarios = models.TextField(
        verbose_name='Destinatarios',
        help_text='Lista de emails separados por coma'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='enviado',
        verbose_name='Estado'
    )
    mensaje_error = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error'
    )
    numero_empleados = models.IntegerField(
        default=0,
        verbose_name='Número de Empleados en Reporte'
    )
    
    class Meta:
        verbose_name = 'Historial de Reporte'
        verbose_name_plural = 'Historial de Reportes'
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"Reporte {self.fecha_inicio} - {self.fecha_fin} ({self.estado})"
