from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from checador.storage_backends import MediaStorage
from empleados.models import Empleado

# Zona horaria de México
MEXICO_TZ = ZoneInfo('America/Mexico_City')


def fecha_mexico():
    """Retorna la fecha actual en zona horaria de México"""
    return timezone.now().astimezone(MEXICO_TZ).date()


class RegistroAsistencia(models.Model):
    """Modelo para registrar asistencias de empleados"""

    TIPO_REGISTRO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='registros',
        verbose_name='Empleado'
    )
    fecha = models.DateField(
        default=fecha_mexico,
        verbose_name='Fecha'
    )
    hora_entrada = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Entrada'
    )
    hora_salida = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Salida'
    )
    horas_trabajadas = models.FloatField(
        default=0,
        verbose_name='Horas Trabajadas'
    )

    # Reconocimiento facial
    reconocimiento_facial = models.BooleanField(
        default=False,
        verbose_name='Reconocimiento Facial'
    )
    foto_registro = models.ImageField(
        storage=MediaStorage(),
        upload_to='asistencias/',
        null=True,
        blank=True,
        verbose_name='Foto de Registro'
    )
    confianza_reconocimiento = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Confianza del Reconocimiento',
        help_text='Porcentaje de confianza del reconocimiento facial'
    )

    # Ubicación (opcional para GPS)
    ubicacion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Ubicación'
    )
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Latitud'
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Longitud'
    )

    # Validación y estado
    retardo = models.BooleanField(
        default=False,
        verbose_name='Retardo'
    )
    justificado = models.BooleanField(
        default=False,
        verbose_name='Justificado'
    )
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['-fecha', '-hora_entrada']
        unique_together = ['empleado', 'fecha']

    def __str__(self):
        return f"{self.empleado.codigo_empleado} - {self.fecha}"

    def calcular_horas_trabajadas(self):
        """Calcula las horas trabajadas si hay entrada y salida"""
        if self.hora_entrada and self.hora_salida:
            entrada = datetime.combine(self.fecha, self.hora_entrada)
            salida = datetime.combine(self.fecha, self.hora_salida)

            # Si la salida es antes que la entrada, asumir que es el día siguiente
            if salida < entrada:
                salida += timedelta(days=1)

            diferencia = salida - entrada
            self.horas_trabajadas = diferencia.total_seconds() / 3600
            return self.horas_trabajadas
        return 0

    def verificar_retardo(self):
        """Verifica si el empleado llegó tarde según su horario"""
        if not self.hora_entrada:
            return False

        # Obtener el horario/turno del empleado para este día
        turno_info = self._obtener_turno_del_dia()
        if not turno_info:
            return False

        hora_entrada_esperada, tolerancia_minutos, cruza_medianoche = turno_info

        entrada_esperada = datetime.combine(self.fecha, hora_entrada_esperada)
        entrada_real = datetime.combine(self.fecha, self.hora_entrada)
        tolerancia = timedelta(minutes=tolerancia_minutos)

        # Para turnos nocturnos, la entrada puede ser en la noche (ej: 23:00)
        # Si la hora de entrada real es temprano en la mañana, puede ser del día anterior
        if cruza_medianoche:
            # Si la entrada esperada es de noche (>18:00) y la real es de día (<12:00)
            # significa que no marcó entrada ayer, no es retardo normal
            if hora_entrada_esperada.hour >= 18 and self.hora_entrada.hour < 12:
                # Entrada fuera de horario, pero no calculamos retardo aquí
                self.retardo = False
                return False

        self.retardo = entrada_real > (entrada_esperada + tolerancia)
        return self.retardo

    def _obtener_turno_del_dia(self):
        """
        Obtiene la información del turno para este día.
        Retorna: (hora_entrada, tolerancia_minutos, cruza_medianoche) o None
        Prioridad: RolMensual > Horario > AsignacionTurno
        """
        from turnos.models import RolMensual, AsignacionTurno

        dia_semana = self.fecha.isoweekday()

        # 1. Buscar en RolMensual
        try:
            rol = RolMensual.objects.select_related('turno').get(
                empleado=self.empleado,
                fecha=self.fecha,
                es_descanso=False,
                turno__isnull=False
            )
            if rol.turno:
                return (rol.turno.hora_entrada, 10, rol.turno.cruza_medianoche)
        except RolMensual.DoesNotExist:
            pass

        # 2. Buscar en Horario del día
        try:
            horario = self.empleado.horarios.select_related('turno').get(
                dia_semana=dia_semana,
                activo=True
            )
            cruza = horario.turno.cruza_medianoche if horario.turno else (horario.hora_salida < horario.hora_entrada)
            return (horario.hora_entrada, horario.tolerancia_minutos, cruza)
        except:
            pass

        # 3. Buscar en AsignacionTurno
        from django.db.models import Q
        asignaciones = AsignacionTurno.objects.filter(
            empleado=self.empleado,
            activo=True,
            fecha_inicio__lte=self.fecha
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=self.fecha)
        ).select_related('turno')

        for asignacion in asignaciones:
            if asignacion.aplica_en_fecha(self.fecha):
                return (asignacion.turno.hora_entrada, 10, asignacion.turno.cruza_medianoche)

        return None

    def save(self, *args, **kwargs):
        """Override save para calcular campos automáticamente"""
        if self.hora_entrada and self.hora_salida:
            self.calcular_horas_trabajadas()
        if self.hora_entrada:
            self.verificar_retardo()
        super().save(*args, **kwargs)

    @property
    def esta_completo(self):
        """Verifica si el registro tiene entrada y salida"""
        return bool(self.hora_entrada and self.hora_salida)

    @property
    def tiempo_trabajado_str(self):
        """Retorna las horas trabajadas en formato legible"""
        if self.horas_trabajadas:
            horas = int(self.horas_trabajadas)
            minutos = int((self.horas_trabajadas - horas) * 60)
            return f"{horas}h {minutos}m"
        return "0h 0m"
