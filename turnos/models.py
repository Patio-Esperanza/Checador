from django.db import models
from django.core.exceptions import ValidationError
from empleados.models import Empleado
from datetime import time, datetime, timedelta


class Turno(models.Model):
    """Modelo para definir turnos de trabajo"""
    
    TIPO_TURNO = [
        ('A', 'Turno A - Matutino'),
        ('B', 'Turno B - Vespertino'),
        ('C', 'Turno C - Nocturno'),
        ('FIJO', 'Turno Fijo'),
    ]
    
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre del Turno'
    )
    codigo = models.CharField(
        max_length=10,
        unique=True,
        choices=TIPO_TURNO,
        verbose_name='Código de Turno'
    )
    hora_entrada = models.TimeField(verbose_name='Hora de Entrada')
    hora_salida = models.TimeField(verbose_name='Hora de Salida')
    
    # Indica si el turno cruza medianoche (ej: 11PM a 7AM)
    cruza_medianoche = models.BooleanField(
        default=False,
        verbose_name='Cruza Medianoche'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name='Color (Hex)',
        help_text='Color para visualización en dashboard (ej: #3B82F6)'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.get_codigo_display()} ({self.hora_entrada.strftime('%H:%M')} - {self.hora_salida.strftime('%H:%M')})"
    
    def clean(self):
        """Validación personalizada"""
        # Validar si cruza medianoche
        if self.hora_entrada > self.hora_salida:
            self.cruza_medianoche = True
        elif self.hora_salida <= self.hora_entrada and not self.cruza_medianoche:
            raise ValidationError('La hora de salida debe ser posterior a la hora de entrada, o marcar que cruza medianoche.')
    
    @property
    def horas_duracion(self):
        """Calcula las horas de duración del turno"""
        entrada = datetime.combine(datetime.today(), self.hora_entrada)
        salida = datetime.combine(datetime.today(), self.hora_salida)
        
        if self.cruza_medianoche:
            salida += timedelta(days=1)
        
        diferencia = salida - entrada
        return diferencia.total_seconds() / 3600


class AsignacionTurno(models.Model):
    """Modelo para asignar turnos a empleados en periodos específicos"""
    
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='asignaciones_turno',
        verbose_name='Empleado'
    )
    turno = models.ForeignKey(
        Turno,
        on_delete=models.PROTECT,
        related_name='asignaciones',
        verbose_name='Turno'
    )
    
    # Rango de fechas de la asignación
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fin',
        help_text='Dejar en blanco para asignación indefinida'
    )
    
    # Días de la semana que aplica esta asignación
    # Si todos son False, aplica todos los días
    aplica_lunes = models.BooleanField(default=True, verbose_name='Lunes')
    aplica_martes = models.BooleanField(default=True, verbose_name='Martes')
    aplica_miercoles = models.BooleanField(default=True, verbose_name='Miércoles')
    aplica_jueves = models.BooleanField(default=True, verbose_name='Jueves')
    aplica_viernes = models.BooleanField(default=True, verbose_name='Viernes')
    aplica_sabado = models.BooleanField(default=False, verbose_name='Sábado')
    aplica_domingo = models.BooleanField(default=False, verbose_name='Domingo')
    
    notas = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Asignación de Turno'
        verbose_name_plural = 'Asignaciones de Turno'
        ordering = ['-fecha_inicio', 'empleado']
        indexes = [
            models.Index(fields=['empleado', 'fecha_inicio', 'fecha_fin']),
            models.Index(fields=['turno', 'fecha_inicio']),
        ]
    
    def __str__(self):
        fecha_fin_str = self.fecha_fin.strftime('%Y-%m-%d') if self.fecha_fin else 'Indefinido'
        return f"{self.empleado.codigo_empleado} - {self.turno.codigo} ({self.fecha_inicio.strftime('%Y-%m-%d')} - {fecha_fin_str})"
    
    def clean(self):
        """Validación personalizada"""
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Validar que al menos un día esté seleccionado
        dias_seleccionados = [
            self.aplica_lunes, self.aplica_martes, self.aplica_miercoles,
            self.aplica_jueves, self.aplica_viernes, self.aplica_sabado, self.aplica_domingo
        ]
        if not any(dias_seleccionados):
            raise ValidationError('Debe seleccionar al menos un día de la semana.')
        
        # Validar que no haya solapamiento de asignaciones para el mismo empleado
        if self.empleado_id:
            asignaciones_activas = AsignacionTurno.objects.filter(
                empleado=self.empleado,
                activo=True
            ).exclude(pk=self.pk)
            
            for asignacion in asignaciones_activas:
                # Si alguna asignación no tiene fecha_fin (indefinida)
                if not asignacion.fecha_fin:
                    if not self.fecha_fin or self.fecha_inicio <= asignacion.fecha_inicio:
                        # Verificar solapamiento de días
                        if self._hay_solapamiento_dias(asignacion):
                            raise ValidationError(
                                f'Ya existe una asignación activa para este empleado que solapa con este periodo y días.'
                            )
                # Verificar solapamiento de fechas
                elif (self.fecha_inicio <= asignacion.fecha_fin and 
                      (not self.fecha_fin or self.fecha_fin >= asignacion.fecha_inicio)):
                    if self._hay_solapamiento_dias(asignacion):
                        raise ValidationError(
                            f'Ya existe una asignación activa que solapa con este periodo y días: {asignacion}'
                        )
    
    def _hay_solapamiento_dias(self, otra_asignacion):
        """Verifica si hay solapamiento en los días de la semana con otra asignación"""
        mis_dias = [
            self.aplica_lunes, self.aplica_martes, self.aplica_miercoles,
            self.aplica_jueves, self.aplica_viernes, self.aplica_sabado, self.aplica_domingo
        ]
        otros_dias = [
            otra_asignacion.aplica_lunes, otra_asignacion.aplica_martes, otra_asignacion.aplica_miercoles,
            otra_asignacion.aplica_jueves, otra_asignacion.aplica_viernes, otra_asignacion.aplica_sabado,
            otra_asignacion.aplica_domingo
        ]
        
        # Si algún día coincide, hay solapamiento
        for i in range(7):
            if mis_dias[i] and otros_dias[i]:
                return True
        return False
    
    @property
    def dias_aplicables(self):
        """Retorna lista de días de la semana donde aplica esta asignación"""
        dias = []
        if self.aplica_lunes: dias.append('Lunes')
        if self.aplica_martes: dias.append('Martes')
        if self.aplica_miercoles: dias.append('Miércoles')
        if self.aplica_jueves: dias.append('Jueves')
        if self.aplica_viernes: dias.append('Viernes')
        if self.aplica_sabado: dias.append('Sábado')
        if self.aplica_domingo: dias.append('Domingo')
        return dias
    
    def aplica_en_fecha(self, fecha):
        """Verifica si esta asignación aplica en una fecha específica"""
        if not self.activo:
            return False
        
        # Verificar rango de fechas
        if fecha < self.fecha_inicio:
            return False
        if self.fecha_fin and fecha > self.fecha_fin:
            return False
        
        # Verificar día de la semana (0=Lunes, 6=Domingo en Python)
        dia_semana = fecha.weekday()
        dias_map = [
            self.aplica_lunes, self.aplica_martes, self.aplica_miercoles,
            self.aplica_jueves, self.aplica_viernes, self.aplica_sabado, self.aplica_domingo
        ]
        
        return dias_map[dia_semana]
