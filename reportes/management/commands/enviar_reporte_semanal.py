"""
Management command para enviar reporte semanal de asistencias
"""
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from reportes.services.email_service import EmailReportService


class Command(BaseCommand):
    help = 'Envía el reporte semanal de asistencias por correo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha-inicio',
            type=str,
            help='Fecha de inicio del periodo (formato: YYYY-MM-DD). Por defecto: hace 7 días'
        )
        parser.add_argument(
            '--fecha-fin',
            type=str,
            help='Fecha fin del periodo (formato: YYYY-MM-DD). Por defecto: ayer'
        )

    def handle(self, *args, **options):
        # Determinar fechas del periodo
        if options['fecha_inicio'] and options['fecha_fin']:
            try:
                fecha_inicio = datetime.strptime(options['fecha_inicio'], '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(options['fecha_fin'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Formato de fecha inválido. Use YYYY-MM-DD')
                )
                return
        else:
            # Por defecto: semana actual (lunes de esta semana hasta hoy)
            hoy = timezone.now().date()
            # Calcular el lunes de la semana actual
            dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
            fecha_inicio = hoy - timedelta(days=dias_desde_lunes)  # Lunes de esta semana
            fecha_fin = hoy  # Hasta hoy

        self.stdout.write(
            self.style.WARNING(f'Generando reporte del {fecha_inicio} al {fecha_fin}...')
        )

        # Crear servicio y enviar reporte
        email_service = EmailReportService(fecha_inicio, fecha_fin)
        resultado = email_service.enviar_reporte_semanal()

        if resultado['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {resultado["message"]}')
            )
            if 'destinatarios' in resultado:
                self.stdout.write(
                    self.style.SUCCESS(f'Destinatarios: {", ".join(resultado["destinatarios"])}')
                )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ {resultado["message"]}')
            )
