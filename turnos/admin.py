from django.contrib import admin
from .models import Turno, AsignacionTurno, RolMensual


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'hora_entrada', 'hora_salida', 'cruza_medianoche', 'activo']
    list_filter = ['activo', 'codigo', 'cruza_medianoche']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['codigo']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion', 'color')
        }),
        ('Horario', {
            'fields': ('hora_entrada', 'hora_salida', 'cruza_medianoche')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


@admin.register(AsignacionTurno)
class AsignacionTurnoAdmin(admin.ModelAdmin):
    list_display = [
        'empleado', 'turno', 'fecha_inicio', 'fecha_fin', 
        'get_dias_display', 'activo'
    ]
    list_filter = ['activo', 'turno', 'fecha_inicio', 'empleado__departamento']
    search_fields = [
        'empleado__codigo_empleado', 
        'empleado__user__first_name', 
        'empleado__user__last_name',
        'notas'
    ]
    ordering = ['-fecha_inicio', 'empleado__codigo_empleado']
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Asignación', {
            'fields': ('empleado', 'turno')
        }),
        ('Período', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Días Aplicables', {
            'fields': (
                'aplica_lunes', 'aplica_martes', 'aplica_miercoles',
                'aplica_jueves', 'aplica_viernes', 'aplica_sabado', 'aplica_domingo'
            ),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('notas', 'activo')
        }),
    )
    
    def get_dias_display(self, obj):
        dias = obj.dias_aplicables
        if len(dias) == 7:
            return 'Todos'
        elif len(dias) == 5 and 'Sábado' not in dias and 'Domingo' not in dias:
            return 'L-V'
        else:
            return ', '.join([d[:3] for d in dias])
    get_dias_display.short_description = 'Días'


@admin.register(RolMensual)
class RolMensualAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'fecha', 'turno', 'es_descanso', 'creado_por', 'fecha_actualizacion']
    list_filter = ['es_descanso', 'turno', 'fecha', 'empleado__departamento']
    search_fields = [
        'empleado__codigo_empleado',
        'empleado__user__first_name',
        'empleado__user__last_name',
        'notas'
    ]
    ordering = ['-fecha', 'empleado__codigo_empleado']
    date_hierarchy = 'fecha'
    raw_id_fields = ['empleado']

    fieldsets = (
        ('Asignación', {
            'fields': ('empleado', 'fecha', 'turno', 'es_descanso')
        }),
        ('Información Adicional', {
            'fields': ('notas', 'creado_por')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
