"""
Vistas para la API de reportes
"""
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone

from reportes.models import ConfiguracionReporte, DestinatarioReporte, HistorialReporte
from reportes.serializers import (
    ConfiguracionReporteSerializer,
    DestinatarioReporteSerializer,
    HistorialReporteSerializer
)
from reportes.services.email_service import EmailReportService


class ConfiguracionReporteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar la configuración de reportes"""
    
    queryset = ConfiguracionReporte.objects.all()
    serializer_class = ConfiguracionReporteSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        # Solo debería haber una configuración, pero usamos queryset por compatibilidad
        return ConfiguracionReporte.objects.all()
    
    @action(detail=False, methods=['get'])
    def actual(self, request):
        """Obtiene la configuración actual (o la crea si no existe)"""
        config = ConfiguracionReporte.objects.first()
        if not config:
            config = ConfiguracionReporte.objects.create()
        serializer = self.get_serializer(config)
        return Response(serializer.data)


class DestinatarioReporteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar los destinatarios de reportes"""
    
    queryset = DestinatarioReporte.objects.all()
    serializer_class = DestinatarioReporteSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['activo']
    search_fields = ['email', 'nombre']
    ordering_fields = ['email', 'nombre', 'fecha_creacion']
    ordering = ['email']
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtiene solo los destinatarios activos"""
        destinatarios = self.queryset.filter(activo=True)
        serializer = self.get_serializer(destinatarios, many=True)
        return Response(serializer.data)


class HistorialReporteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar el historial de reportes (solo lectura)"""
    
    queryset = HistorialReporte.objects.all()
    serializer_class = HistorialReporteSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['estado', 'fecha_inicio', 'fecha_fin']
    ordering = ['-fecha_envio']
    
    @action(detail=False, methods=['post'])
    def enviar_reporte_manual(self, request):
        """
        Envía un reporte manual para un periodo específico
        
        Parámetros:
        - fecha_inicio (opcional): Fecha de inicio en formato YYYY-MM-DD
        - fecha_fin (opcional): Fecha fin en formato YYYY-MM-DD
        
        Si no se proporcionan fechas, usa la semana anterior
        """
        fecha_inicio_str = request.data.get('fecha_inicio')
        fecha_fin_str = request.data.get('fecha_fin')
        
        # Validar y parsear fechas
        if fecha_inicio_str and fecha_fin_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Por defecto: semana anterior (lunes a domingo)
            hoy = timezone.now().date()
            dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
            lunes_esta_semana = hoy - timedelta(days=dias_desde_lunes)
            fecha_fin = lunes_esta_semana - timedelta(days=1)  # Domingo semana pasada
            fecha_inicio = fecha_fin - timedelta(days=6)  # Lunes semana pasada
        
        # Validar que fecha_inicio < fecha_fin
        if fecha_inicio > fecha_fin:
            return Response(
                {'error': 'La fecha de inicio debe ser anterior a la fecha fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enviar reporte
        email_service = EmailReportService(fecha_inicio, fecha_fin)
        resultado = email_service.enviar_reporte_semanal()
        
        if resultado['success']:
            return Response({
                'mensaje': resultado['message'],
                'destinatarios': resultado.get('destinatarios', []),
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': resultado['message']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
