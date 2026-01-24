from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, date
from calendar import monthrange
import json
from empleados.models import Empleado
from registros.models import RegistroAsistencia
from turnos.models import Turno, RolMensual


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            
            # Redirigir a la página solicitada o al dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'auth/login.html')


def register_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        codigo_empleado = request.POST.get('codigo_empleado')
        departamento = request.POST.get('departamento')
        puesto = request.POST.get('puesto')
        
        # Validaciones
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'auth/register.html')
        
        if Empleado.objects.filter(codigo_empleado=codigo_empleado).exists():
            messages.error(request, 'El código de empleado ya está en uso.')
            return render(request, 'auth/register.html')
        
        try:
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Crear empleado
            empleado = Empleado.objects.create(
                user=user,
                codigo_empleado=codigo_empleado,
                departamento=departamento,
                puesto=puesto or ''
            )
            
            messages.success(request, '¡Registro exitoso! Ahora registra tu rostro para completar tu perfil.')
            
            # Iniciar sesión automáticamente
            login(request, user)
            
            # Redirigir al registro de rostro
            return redirect('empleados:register_face', empleado_id=empleado.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
    
    return render(request, 'auth/register.html')


def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard principal"""
    context = {
        'today': timezone.now().date(),
    }
    
    # Obtener empleado del usuario actual
    try:
        empleado = request.user.empleado
        context['empleado'] = empleado
        
        # Obtener registro de hoy
        hoy = timezone.now().date()
        registro_hoy = RegistroAsistencia.objects.filter(
            empleado=empleado,
            fecha=hoy
        ).first()
        context['registro_hoy'] = registro_hoy
        
        # Estadísticas del mes actual
        primer_dia_mes = hoy.replace(day=1)
        registros_mes = RegistroAsistencia.objects.filter(
            empleado=empleado,
            fecha__gte=primer_dia_mes,
            fecha__lte=hoy
        )
        
        context['dias_trabajados'] = registros_mes.filter(hora_entrada__isnull=False).count()
        context['retardos_mes'] = registros_mes.filter(retardo=True).count()
        context['horas_totales'] = sum([r.horas_trabajadas for r in registros_mes])
        
        # Últimos 7 registros
        context['ultimos_registros'] = RegistroAsistencia.objects.filter(
            empleado=empleado
        ).order_by('-fecha')[:7]
        
    except Empleado.DoesNotExist:
        context['empleado'] = None
        messages.warning(request, 'No tienes un perfil de empleado asociado.')
    
    # Estadísticas para staff
    if request.user.is_staff:
        hoy = timezone.now().date()
        context['total_empleados'] = Empleado.objects.filter(activo=True).count()
        context['registros_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy).count()
        context['empleados_sin_rostro'] = Empleado.objects.filter(
            activo=True,
            embedding_rostro__isnull=True
        ).count()
    
    return render(request, 'dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def empleados_lista_view(request):
    """Lista de empleados (solo para staff)"""
    search = request.GET.get('search', '')
    departamento = request.GET.get('departamento', '')
    
    empleados = Empleado.objects.select_related('user').filter(activo=True)
    
    if search:
        empleados = empleados.filter(
            Q(codigo_empleado__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    if departamento:
        empleados = empleados.filter(departamento__icontains=departamento)
    
    # Obtener lista de departamentos para el filtro
    departamentos = Empleado.objects.filter(activo=True).values_list('departamento', flat=True).distinct()
    
    context = {
        'empleados': empleados.order_by('codigo_empleado'),
        'departamentos': departamentos,
        'search': search,
        'departamento_selected': departamento,
    }
    
    return render(request, 'empleados/lista.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def registros_lista_view(request):
    """Lista de registros de asistencia (solo para staff)"""
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    empleado_id = request.GET.get('empleado', '')
    
    # Por defecto, mostrar registros del mes actual
    if not fecha_inicio:
        fecha_inicio = timezone.now().date().replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    registros = RegistroAsistencia.objects.select_related('empleado__user').filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    )
    
    if empleado_id:
        registros = registros.filter(empleado_id=empleado_id)
    
    # Estadísticas
    stats = {
        'total_registros': registros.count(),
        'retardos': registros.filter(retardo=True).count(),
        'horas_totales': sum([r.horas_trabajadas for r in registros]),
        'registros_completos': registros.filter(hora_entrada__isnull=False, hora_salida__isnull=False).count(),
    }
    
    empleados = Empleado.objects.filter(activo=True).order_by('codigo_empleado')
    
    context = {
        'registros': registros.order_by('-fecha', '-hora_entrada'),
        'empleados': empleados,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'empleado_selected': empleado_id,
        'stats': stats,
    }
    
    return render(request, 'registros/lista.html', context)


@login_required
def marcar_asistencia_view(request):
    """Vista para marcar asistencia (redirige a facial recognition)"""
    return redirect('facial_recognition')


@login_required
@user_passes_test(lambda u: u.is_staff)
def rol_mensual_view(request):
    """Vista para asignar turnos tipo Excel (rol mensual)"""
    # Obtener mes y año de los parámetros o usar el actual
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    # Validar rango de año
    if year < 2020 or year > 2030:
        year = timezone.now().year
    if month < 1 or month > 12:
        month = timezone.now().month

    # Obtener información del mes
    _, ultimo_dia = monthrange(year, month)
    dias_mes = list(range(1, ultimo_dia + 1))

    # Crear lista de fechas con información del día de la semana
    dias_info = []
    dias_semana_cortos = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
    for dia in dias_mes:
        fecha = date(year, month, dia)
        dias_info.append({
            'dia': dia,
            'dia_semana': dias_semana_cortos[fecha.weekday()],
            'es_fin_semana': fecha.weekday() >= 5
        })

    # Obtener empleados activos
    empleados = Empleado.objects.filter(activo=True).select_related('user').order_by('codigo_empleado')

    # Obtener roles del mes
    roles_mes = RolMensual.obtener_rol_mes(year, month)

    # Obtener turnos disponibles
    turnos = Turno.objects.filter(activo=True).order_by('codigo')

    # Preparar datos para el template
    empleados_data = []
    for empleado in empleados:
        roles_empleado = roles_mes.get(empleado.id, {})
        dias_empleado = []
        for dia in dias_mes:
            rol = roles_empleado.get(dia)
            if rol:
                dias_empleado.append({
                    'dia': dia,
                    'turno_id': rol.turno_id if rol.turno else None,
                    'turno_codigo': rol.turno.codigo if rol.turno else None,
                    'turno_color': rol.turno.color if rol.turno else None,
                    'es_descanso': rol.es_descanso,
                    'notas': rol.notas
                })
            else:
                dias_empleado.append({
                    'dia': dia,
                    'turno_id': None,
                    'turno_codigo': None,
                    'turno_color': None,
                    'es_descanso': False,
                    'notas': ''
                })
        empleados_data.append({
            'empleado': empleado,
            'dias': dias_empleado
        })

    # Nombres de meses en español
    meses = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    context = {
        'year': year,
        'month': month,
        'nombre_mes': meses[month - 1],
        'dias_info': dias_info,
        'empleados_data': empleados_data,
        'turnos': turnos,
        'meses': [(i + 1, meses[i]) for i in range(12)],
        'years': list(range(2020, 2031)),
    }

    return render(request, 'turnos/rol_mensual.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def guardar_rol_view(request):
    """API para guardar una asignación de rol"""
    try:
        data = json.loads(request.body)
        empleado_id = data.get('empleado_id')
        fecha_str = data.get('fecha')
        turno_id = data.get('turno_id')
        es_descanso = data.get('es_descanso', False)

        # Validar datos
        if not empleado_id or not fecha_str:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        empleado = Empleado.objects.get(id=empleado_id)

        # Obtener turno si se especificó
        turno = None
        if turno_id and not es_descanso:
            turno = Turno.objects.get(id=turno_id)

        # Crear o actualizar el rol
        rol, created = RolMensual.objects.update_or_create(
            empleado=empleado,
            fecha=fecha,
            defaults={
                'turno': turno,
                'es_descanso': es_descanso,
                'creado_por': request.user
            }
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'turno_codigo': turno.codigo if turno else None,
            'turno_color': turno.color if turno else None,
            'es_descanso': es_descanso
        })

    except Empleado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Empleado no encontrado'}, status=404)
    except Turno.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Turno no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def eliminar_rol_view(request):
    """API para eliminar una asignación de rol"""
    try:
        data = json.loads(request.body)
        empleado_id = data.get('empleado_id')
        fecha_str = data.get('fecha')

        if not empleado_id or not fecha_str:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        deleted, _ = RolMensual.objects.filter(
            empleado_id=empleado_id,
            fecha=fecha
        ).delete()

        return JsonResponse({'success': True, 'deleted': deleted > 0})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
