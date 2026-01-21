from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TurnoViewSet, AsignacionTurnoViewSet

router = DefaultRouter()
router.register(r'turnos', TurnoViewSet, basename='turno')
router.register(r'asignaciones', AsignacionTurnoViewSet, basename='asignacion-turno')

urlpatterns = [
    path('', include(router.urls)),
]
