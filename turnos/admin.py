from django.contrib import admin
from django import forms
from .models import Turno, AsignacionTurno, RolMensual


class TurnoAdminForm(forms.ModelForm):
    """Form personalizado para Turno con datalist para códigos sugeridos"""
    
    codigo_sugerido = forms.ChoiceField(
        choices=[('', '--- Seleccionar o escribir uno nuevo ---')] + Turno.TIPO_TURNO,
        required=False,
        label='Códigos Sugeridos',
        help_text='Seleccione un código predefinido o escriba uno personalizado abajo'
    )
    
    class Meta:
        model = Turno
        fields = '__all__'
        widgets = {
            'codigo': forms.TextInput(attrs={
                'placeholder': 'Ingrese código personalizado o use el selector de arriba',
                'style': 'text-transform: uppercase;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando, pre-seleccionar el código si coincide con uno predefinido
        if self.instance and self.instance.pk:
            for codigo, _ in Turno.TIPO_TURNO:
                if self.instance.codigo == codigo:
                    self.fields['codigo_sugerido'].initial = codigo
                    break
    
    def clean(self):
        cleaned_data = super().clean()
        codigo_sugerido = cleaned_data.get('codigo_sugerido')
        codigo = cleaned_data.get('codigo')
        
        # Si se seleccionó un código sugerido y no se escribió uno personalizado, usar el sugerido
        if codigo_sugerido and not codigo:
            cleaned_data['codigo'] = codigo_sugerido
        # Si se escribió un código personalizado, convertirlo a mayúsculas
        elif codigo:
            cleaned_data['codigo'] = codigo.upper()
        
        return cleaned_data


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    form = TurnoAdminForm
    list_display = ['codigo', 'nombre', 'hora_entrada', 'hora_salida', 'cruza_medianoche', 'activo']
    list_filter = ['activo', 'cruza_medianoche']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['codigo']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo_sugerido', 'codigo', 'descripcion', 'color')
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
