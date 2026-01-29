"""
Serializers para la API de reportes
"""
from rest_framework import serializers
from reportes.models import ConfiguracionReporte, DestinatarioReporte, HistorialReporte


class ConfiguracionReporteSerializer(serializers.ModelSerializer):
    """Serializer para la configuración de reportes"""
    
    dia_envio_display = serializers.CharField(source='get_dia_envio_display', read_only=True)
    
    class Meta:
        model = ConfiguracionReporte
        fields = [
            'id',
            'activo',
            'dia_envio',
            'dia_envio_display',
            'hora_envio',
            'asunto_correo',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class DestinatarioReporteSerializer(serializers.ModelSerializer):
    """Serializer para los destinatarios de reportes"""
    
    class Meta:
        model = DestinatarioReporte
        fields = [
            'id',
            'email',
            'nombre',
            'activo',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class HistorialReporteSerializer(serializers.ModelSerializer):
    """Serializer para el historial de reportes"""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = HistorialReporte
        fields = [
            'id',
            'fecha_envio',
            'fecha_inicio',
            'fecha_fin',
            'destinatarios',
            'estado',
            'estado_display',
            'mensaje_error',
            'numero_empleados'
        ]
        read_only_fields = '__all__'
