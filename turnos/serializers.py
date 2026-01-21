from rest_framework import serializers
from .models import Turno, AsignacionTurno
from empleados.serializers import EmpleadoListSerializer


class TurnoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Turno"""
    
    horas_duracion = serializers.ReadOnlyField()
    
    class Meta:
        model = Turno
        fields = [
            'id', 'nombre', 'codigo', 'hora_entrada', 'hora_salida',
            'cruza_medianoche', 'descripcion', 'color', 'activo',
            'horas_duracion', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class AsignacionTurnoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo AsignacionTurno"""
    
    empleado_detalle = EmpleadoListSerializer(source='empleado', read_only=True)
    turno_detalle = TurnoSerializer(source='turno', read_only=True)
    dias_aplicables = serializers.ReadOnlyField()
    
    class Meta:
        model = AsignacionTurno
        fields = [
            'id', 'empleado', 'empleado_detalle', 'turno', 'turno_detalle',
            'fecha_inicio', 'fecha_fin',
            'aplica_lunes', 'aplica_martes', 'aplica_miercoles',
            'aplica_jueves', 'aplica_viernes', 'aplica_sabado', 'aplica_domingo',
            'dias_aplicables', 'notas', 'activo',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def validate(self, data):
        """Validación personalizada"""
        # Validar fechas
        if data.get('fecha_fin') and data.get('fecha_inicio'):
            if data['fecha_fin'] < data['fecha_inicio']:
                raise serializers.ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar que al menos un día esté seleccionado
        dias = [
            data.get('aplica_lunes', True),
            data.get('aplica_martes', True),
            data.get('aplica_miercoles', True),
            data.get('aplica_jueves', True),
            data.get('aplica_viernes', True),
            data.get('aplica_sabado', False),
            data.get('aplica_domingo', False)
        ]
        if not any(dias):
            raise serializers.ValidationError(
                'Debe seleccionar al menos un día de la semana.'
            )
        
        return data


class AsignacionTurnoCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear asignaciones de turno"""
    
    class Meta:
        model = AsignacionTurno
        fields = [
            'empleado', 'turno', 'fecha_inicio', 'fecha_fin',
            'aplica_lunes', 'aplica_martes', 'aplica_miercoles',
            'aplica_jueves', 'aplica_viernes', 'aplica_sabado', 'aplica_domingo',
            'notas', 'activo'
        ]


class RolSemanalSerializer(serializers.Serializer):
    """Serializer para vista de rol semanal"""
    
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    empleado_id = serializers.IntegerField(required=False)
    turno_codigo = serializers.CharField(required=False, max_length=10)
    departamento = serializers.CharField(required=False, max_length=100)
