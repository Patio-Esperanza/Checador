from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Turno, AsignacionTurno
from .serializers import (
    TurnoSerializer, 
    AsignacionTurnoSerializer,
    AsignacionTurnoCreateSerializer,
    RolSemanalSerializer
)
from empleados.models import Empleado


class TurnoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de turnos"""
    
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Turno.objects.all()
        
        # Filtro por activos
        activo = self.request.query_params.get('activo', None)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        # Filtro por código
        codigo = self.request.query_params.get('codigo', None)
        if codigo:
            queryset = queryset.filter(codigo=codigo)
        
        return queryset.order_by('codigo')


class AsignacionTurnoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asignaciones de turno"""
    
    queryset = AsignacionTurno.objects.select_related('empleado', 'turno').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AsignacionTurnoCreateSerializer
        return AsignacionTurnoSerializer
    
    def get_queryset(self):
        queryset = AsignacionTurno.objects.select_related(
            'empleado', 'empleado__user', 'turno'
        ).all()
        
        # Filtro por empleado
        empleado_id = self.request.query_params.get('empleado', None)
        if empleado_id:
            queryset = queryset.filter(empleado_id=empleado_id)
        
        # Filtro por turno
        turno_id = self.request.query_params.get('turno', None)
        if turno_id:
            queryset = queryset.filter(turno_id=turno_id)
        
        # Filtro por fecha
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    fecha_inicio__lte=fecha_obj
                ).filter(
                    Q(fecha_fin__gte=fecha_obj) | Q(fecha_fin__isnull=True)
                )
            except ValueError:
                pass
        
        # Filtro por activos
        activo = self.request.query_params.get('activo', None)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        return queryset.order_by('-fecha_inicio', 'empleado__codigo_empleado')
    
    @action(detail=False, methods=['get'])
    def rol_semanal(self, request):
        """
        Endpoint para obtener el rol de turnos semanal
        Parámetros: fecha_inicio, fecha_fin, departamento (opcional)
        """
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        departamento = request.query_params.get('departamento')
        
        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'Debe proporcionar fecha_inicio y fecha_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener asignaciones en el rango de fechas
        asignaciones = AsignacionTurno.objects.select_related(
            'empleado', 'empleado__user', 'turno'
        ).filter(
            activo=True,
            fecha_inicio__lte=fecha_fin_obj
        ).filter(
            Q(fecha_fin__gte=fecha_inicio_obj) | Q(fecha_fin__isnull=True)
        )
        
        # Filtrar por departamento si se proporciona
        if departamento:
            asignaciones = asignaciones.filter(empleado__departamento=departamento)
        
        # Construir el rol semanal
        rol = []
        current_date = fecha_inicio_obj
        
        while current_date <= fecha_fin_obj:
            dia_data = {
                'fecha': current_date.strftime('%Y-%m-%d'),
                'dia_semana': current_date.strftime('%A'),
                'turnos': {}
            }
            
            # Obtener asignaciones que aplican en esta fecha
            for asignacion in asignaciones:
                if asignacion.aplica_en_fecha(current_date):
                    turno_codigo = asignacion.turno.codigo
                    
                    if turno_codigo not in dia_data['turnos']:
                        dia_data['turnos'][turno_codigo] = {
                            'turno': TurnoSerializer(asignacion.turno).data,
                            'empleados': []
                        }
                    
                    dia_data['turnos'][turno_codigo]['empleados'].append({
                        'id': asignacion.empleado.id,
                        'codigo_empleado': asignacion.empleado.codigo_empleado,
                        'nombre_completo': asignacion.empleado.nombre_completo,
                        'departamento': asignacion.empleado.departamento,
                        'puesto': asignacion.empleado.puesto
                    })
            
            rol.append(dia_data)
            current_date += timedelta(days=1)
        
        return Response({
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'departamento': departamento,
            'rol': rol
        })
    
    @action(detail=False, methods=['get'])
    def empleados_disponibles(self, request):
        """
        Endpoint para obtener empleados sin turno asignado en una fecha específica
        Parámetros: fecha (YYYY-MM-DD), departamento (opcional)
        """
        fecha = request.query_params.get('fecha')
        departamento = request.query_params.get('departamento')
        
        if not fecha:
            return Response(
                {'error': 'Debe proporcionar una fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener todos los empleados activos
        empleados = Empleado.objects.filter(activo=True)
        
        if departamento:
            empleados = empleados.filter(departamento=departamento)
        
        # Filtrar empleados que no tienen asignación en la fecha
        empleados_disponibles = []
        
        for empleado in empleados:
            tiene_asignacion = AsignacionTurno.objects.filter(
                empleado=empleado,
                activo=True,
                fecha_inicio__lte=fecha_obj
            ).filter(
                Q(fecha_fin__gte=fecha_obj) | Q(fecha_fin__isnull=True)
            ).exists()
            
            if not tiene_asignacion:
                empleados_disponibles.append({
                    'id': empleado.id,
                    'codigo_empleado': empleado.codigo_empleado,
                    'nombre_completo': empleado.nombre_completo,
                    'departamento': empleado.departamento,
                    'puesto': empleado.puesto
                })
        
        return Response({
            'fecha': fecha,
            'departamento': departamento,
            'total': len(empleados_disponibles),
            'empleados': empleados_disponibles
        })
    
    @action(detail=False, methods=['post'])
    def asignar_masivo(self, request):
        """
        Endpoint para asignar un turno a múltiples empleados
        Body: {
            "empleados_ids": [1, 2, 3],
            "turno_id": 1,
            "fecha_inicio": "2026-01-20",
            "fecha_fin": "2026-01-26",  // opcional
            "dias": ["lunes", "martes", ...],  // opcional, por defecto L-V
            "notas": ""  // opcional
        }
        """
        empleados_ids = request.data.get('empleados_ids', [])
        turno_id = request.data.get('turno_id')
        fecha_inicio = request.data.get('fecha_inicio')
        fecha_fin = request.data.get('fecha_fin')
        dias = request.data.get('dias', ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'])
        notas = request.data.get('notas', '')
        
        if not empleados_ids or not turno_id or not fecha_inicio:
            return Response(
                {'error': 'Debe proporcionar empleados_ids, turno_id y fecha_inicio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            turno = Turno.objects.get(id=turno_id, activo=True)
        except Turno.DoesNotExist:
            return Response(
                {'error': 'Turno no encontrado o inactivo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mapear días de la semana
        dias_map = {
            'lunes': 'aplica_lunes',
            'martes': 'aplica_martes',
            'miercoles': 'aplica_miercoles',
            'jueves': 'aplica_jueves',
            'viernes': 'aplica_viernes',
            'sabado': 'aplica_sabado',
            'domingo': 'aplica_domingo'
        }
        
        asignaciones_creadas = []
        errores = []
        
        for empleado_id in empleados_ids:
            try:
                empleado = Empleado.objects.get(id=empleado_id, activo=True)
                
                # Preparar datos de asignación
                asignacion_data = {
                    'empleado': empleado,
                    'turno': turno,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'notas': notas,
                    'activo': True
                }
                
                # Configurar días
                for dia_key in dias_map.values():
                    asignacion_data[dia_key] = False
                
                for dia in dias:
                    dia_lower = dia.lower()
                    if dia_lower in dias_map:
                        asignacion_data[dias_map[dia_lower]] = True
                
                # Crear asignación
                asignacion = AsignacionTurno(**asignacion_data)
                asignacion.full_clean()  # Validar
                asignacion.save()
                
                asignaciones_creadas.append(AsignacionTurnoSerializer(asignacion).data)
                
            except Empleado.DoesNotExist:
                errores.append(f'Empleado con ID {empleado_id} no encontrado')
            except Exception as e:
                errores.append(f'Error al asignar empleado {empleado_id}: {str(e)}')
        
        return Response({
            'exitosas': len(asignaciones_creadas),
            'errores': len(errores),
            'asignaciones': asignaciones_creadas,
            'detalles_errores': errores
        }, status=status.HTTP_201_CREATED if asignaciones_creadas else status.HTTP_400_BAD_REQUEST)
