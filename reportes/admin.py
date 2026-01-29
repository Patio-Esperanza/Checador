"""
Configuración del admin para reportes
"""
from django.contrib import admin
from reportes.models import ConfiguracionReporte, DestinatarioReporte, HistorialReporte


@admin.register(ConfiguracionReporte)
class ConfiguracionReporteAdmin(admin.ModelAdmin):
    """Admin para la configuración de reportes"""
    
    list_display = ['id', 'activo', 'dia_envio_display', 'hora_envio', 'asunto_correo']
    list_filter = ['activo', 'dia_envio']
    search_fields = ['asunto_correo']
    
    fieldsets = (
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Programación', {
            'fields': ('dia_envio', 'hora_envio')
        }),
        ('Configuración de Email', {
            'fields': ('asunto_correo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def dia_envio_display(self, obj):
        return obj.get_dia_envio_display()
    dia_envio_display.short_description = 'Día de Envío'
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False


@admin.register(DestinatarioReporte)
class DestinatarioReporteAdmin(admin.ModelAdmin):
    """Admin para los destinatarios de reportes"""
    
    list_display = ['email', 'nombre', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['email', 'nombre']
    ordering = ['email']
    
    fieldsets = (
        ('Información del Destinatario', {
            'fields': ('email', 'nombre')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(HistorialReporte)
class HistorialReporteAdmin(admin.ModelAdmin):
    """Admin para el historial de reportes"""
    
    list_display = ['id', 'fecha_envio', 'fecha_inicio', 'fecha_fin', 'estado', 'numero_empleados']
    list_filter = ['estado', 'fecha_envio', 'fecha_inicio']
    search_fields = ['destinatarios']
    ordering = ['-fecha_envio']
    date_hierarchy = 'fecha_envio'
    
    fieldsets = (
        ('Periodo del Reporte', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Información de Envío', {
            'fields': ('fecha_envio', 'destinatarios', 'numero_empleados')
        }),
        ('Resultado', {
            'fields': ('estado', 'mensaje_error')
        }),
    )
    
    readonly_fields = ['fecha_envio', 'fecha_inicio', 'fecha_fin', 'destinatarios', 'estado', 'mensaje_error', 'numero_empleados']
    
    def has_add_permission(self, request):
        # No permitir crear registros manualmente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permitir eliminar solo para limpiar historial antiguo
        return request.user.is_superuser
