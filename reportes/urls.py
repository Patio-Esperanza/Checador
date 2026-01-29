"""
URLs para la API de reportes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from reportes.views import (
    ConfiguracionReporteViewSet,
    DestinatarioReporteViewSet,
    HistorialReporteViewSet
)

router = DefaultRouter()
router.register(r'configuracion', ConfiguracionReporteViewSet, basename='configuracion-reporte')
router.register(r'destinatarios', DestinatarioReporteViewSet, basename='destinatario-reporte')
router.register(r'historial', HistorialReporteViewSet, basename='historial-reporte')

urlpatterns = [
    path('', include(router.urls)),
]
