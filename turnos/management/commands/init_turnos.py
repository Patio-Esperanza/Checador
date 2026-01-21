from django.core.management.base import BaseCommand
from turnos.models import Turno
from datetime import time


class Command(BaseCommand):
    help = 'Inicializa los turnos predefinidos (A, B, C y Fijo)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando turnos iniciales...'))
        
        turnos_data = [
            {
                'codigo': 'A',
                'nombre': 'Turno A - Matutino',
                'hora_entrada': time(7, 0),
                'hora_salida': time(15, 0),  # 3PM
                'cruza_medianoche': False,
                'descripcion': 'Turno matutino de 7:00 AM a 3:00 PM',
                'color': '#10B981',  # Verde
            },
            {
                'codigo': 'B',
                'nombre': 'Turno B - Vespertino',
                'hora_entrada': time(15, 0),  # 3PM
                'hora_salida': time(23, 0),  # 11PM
                'cruza_medianoche': False,
                'descripcion': 'Turno vespertino de 3:00 PM a 11:00 PM',
                'color': '#F59E0B',  # Ámbar
            },
            {
                'codigo': 'C',
                'nombre': 'Turno C - Nocturno',
                'hora_entrada': time(23, 0),  # 11PM
                'hora_salida': time(7, 0),  # 7AM
                'cruza_medianoche': True,
                'descripcion': 'Turno nocturno de 11:00 PM a 7:00 AM',
                'color': '#6366F1',  # Índigo
            },
            {
                'codigo': 'FIJO',
                'nombre': 'Turno Fijo',
                'hora_entrada': time(8, 0),  # 8AM
                'hora_salida': time(18, 0),  # 6PM
                'cruza_medianoche': False,
                'descripcion': 'Turno fijo de 8:00 AM a 6:00 PM',
                'color': '#3B82F6',  # Azul
            },
        ]
        
        created = 0
        updated = 0
        
        for turno_data in turnos_data:
            turno, created_flag = Turno.objects.update_or_create(
                codigo=turno_data['codigo'],
                defaults={
                    'nombre': turno_data['nombre'],
                    'hora_entrada': turno_data['hora_entrada'],
                    'hora_salida': turno_data['hora_salida'],
                    'cruza_medianoche': turno_data['cruza_medianoche'],
                    'descripcion': turno_data['descripcion'],
                    'color': turno_data['color'],
                    'activo': True,
                }
            )
            
            if created_flag:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {turno.nombre}')
                )
            else:
                updated += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Actualizado: {turno.nombre}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Completado! Turnos creados: {created}, actualizados: {updated}'
            )
        )
