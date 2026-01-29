"""
Servicio para enviar reportes por correo electrónico
"""
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from reportes.models import DestinatarioReporte, ConfiguracionReporte, HistorialReporte
from reportes.services.excel_service import ExcelReportService


class EmailReportService:
    """Servicio para enviar reportes de asistencia por correo"""

    def __init__(self, fecha_inicio, fecha_fin):
        """
        Inicializa el servicio

        Args:
            fecha_inicio: Fecha de inicio del periodo
            fecha_fin: Fecha fin del periodo
        """
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.excel_service = ExcelReportService(fecha_inicio, fecha_fin)

    def enviar_reporte_semanal(self):
        """
        Envía el reporte semanal a todos los destinatarios activos

        Returns:
            dict: Resultado del envío con estado y mensaje
        """
        try:
            # Obtener destinatarios activos
            destinatarios = DestinatarioReporte.objects.filter(activo=True)
            if not destinatarios.exists():
                return {
                    'success': False,
                    'message': 'No hay destinatarios activos configurados'
                }

            # Obtener configuración
            config = ConfiguracionReporte.objects.first()
            if not config or not config.activo:
                return {
                    'success': False,
                    'message': 'El envío de reportes está desactivado'
                }

            # Generar archivo Excel
            excel_file = self.excel_service.generar_reporte_completo()

            # Obtener datos para el correo
            top_retardos = self.excel_service.obtener_top_retardos(5)
            empleados_faltas = self.excel_service.obtener_empleados_con_faltas()

            # Preparar contexto para el template
            context = {
                'fecha_inicio': self.fecha_inicio,
                'fecha_fin': self.fecha_fin,
                'top_retardos': top_retardos,
                'empleados_faltas': empleados_faltas[:10],  # Máximo 10 para no saturar
                'total_faltas': len(empleados_faltas)
            }

            # Generar cuerpo del correo
            html_message = self._generar_html_correo(context)
            plain_message = self._generar_texto_correo(context)

            # Preparar lista de destinatarios
            destinatarios_emails = [d.email for d in destinatarios]

            # Crear y enviar correo
            email = EmailMessage(
                subject=config.asunto_correo,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=destinatarios_emails
            )

            # Agregar versión HTML
            email.content_subtype = 'html'
            email.body = html_message

            # Adjuntar archivo Excel
            filename = f'reporte_asistencias_{self.fecha_inicio.strftime("%Y%m%d")}_{self.fecha_fin.strftime("%Y%m%d")}.xlsx'
            email.attach(filename, excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            # Enviar
            email.send(fail_silently=False)

            # Registrar en historial
            self._registrar_historial(
                destinatarios_emails,
                'enviado',
                len(top_retardos) + len(empleados_faltas)
            )

            return {
                'success': True,
                'message': f'Reporte enviado exitosamente a {len(destinatarios_emails)} destinatarios',
                'destinatarios': destinatarios_emails
            }

        except Exception as e:
            # Registrar error en historial
            self._registrar_historial(
                [],
                'error',
                0,
                str(e)
            )
            return {
                'success': False,
                'message': f'Error al enviar reporte: {str(e)}'
            }

    def _generar_html_correo(self, context):
        """Genera el HTML del correo usando un template"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #4472C4; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #4472C4; border-bottom: 2px solid #4472C4; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ background-color: #4472C4; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .top-retardos {{ background-color: #FFF3CD; }}
        .faltas {{ background-color: #F8D7DA; }}
        .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte Semanal de Asistencias Patio La Esperanza</h1>
        <p>Periodo: {fecha_inicio} al {fecha_fin}</p>
    </div>

    <div class="content">
        <div class="section">
            <h2>🕐 Top 5 - Empleados con más Retardos</h2>
            {top_retardos_html}
        </div>

        <div class="section">
            <h2>❌ Empleados con Faltas</h2>
            {faltas_html}
        </div>

        <div class="section">
            <p><strong>📎 Adjunto:</strong> Archivo Excel con el reporte completo incluyendo:</p>
            <ul>
                <li><strong>Hoja 1 - Concentrado:</strong> Resumen por empleado (días trabajados, faltas, retardos, horas totales)</li>
                <li><strong>Hoja 2 - Detalle:</strong> Registro detallado de cada asistencia</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <p>Este es un reporte automático generado por el Sistema de Checador de Asistencias</p>
        <p>Patio La Esperanza</p>
    </div>
</body>
</html>
        """

        # Generar tabla de top retardos
        if context['top_retardos']:
            top_retardos_html = '<table class="top-retardos">'
            top_retardos_html += '<tr><th>Posición</th><th>Código</th><th>Nombre</th><th>Retardos</th></tr>'
            for idx, emp in enumerate(context['top_retardos'], 1):
                top_retardos_html += f'<tr><td>{idx}</td><td>{emp["codigo"]}</td><td>{emp["nombre"]}</td><td>{emp["retardos"]}</td></tr>'
            top_retardos_html += '</table>'
        else:
            top_retardos_html = '<p>No hay empleados con retardos en este periodo.</p>'

        # Generar tabla de faltas
        if context['empleados_faltas']:
            faltas_html = '<table class="faltas">'
            faltas_html += '<tr><th>Código</th><th>Nombre</th><th>Faltas</th></tr>'
            for emp in context['empleados_faltas']:
                faltas_html += f'<tr><td>{emp["codigo"]}</td><td>{emp["nombre"]}</td><td>{emp["faltas"]}</td></tr>'
            if context['total_faltas'] > 10:
                faltas_html += f'<tr><td colspan="3"><em>... y {context["total_faltas"] - 10} empleados más (ver Excel adjunto)</em></td></tr>'
            faltas_html += '</table>'
        else:
            faltas_html = '<p>No hay empleados con faltas en este periodo.</p>'

        return html_template.format(
            fecha_inicio=context['fecha_inicio'].strftime('%d/%m/%Y'),
            fecha_fin=context['fecha_fin'].strftime('%d/%m/%Y'),
            top_retardos_html=top_retardos_html,
            faltas_html=faltas_html
        )

    def _generar_texto_correo(self, context):
        """Genera la versión texto plano del correo"""
        texto = f"""
REPORTE SEMANAL DE ASISTENCIAS
Periodo: {context['fecha_inicio'].strftime('%d/%m/%Y')} al {context['fecha_fin'].strftime('%d/%m/%Y')}

TOP 5 - EMPLEADOS CON MÁS RETARDOS
{'='*50}
"""
        if context['top_retardos']:
            for idx, emp in enumerate(context['top_retardos'], 1):
                texto += f"{idx}. {emp['codigo']} - {emp['nombre']}: {emp['retardos']} retardos\n"
        else:
            texto += "No hay empleados con retardos en este periodo.\n"

        texto += f"\n\nEMPLEADOS CON FALTAS\n{'='*50}\n"
        if context['empleados_faltas']:
            for emp in context['empleados_faltas']:
                texto += f"- {emp['codigo']} - {emp['nombre']}: {emp['faltas']} faltas\n"
            if context['total_faltas'] > 10:
                texto += f"\n... y {context['total_faltas'] - 10} empleados más (ver Excel adjunto)\n"
        else:
            texto += "No hay empleados con faltas en este periodo.\n"

        texto += """
\nARCHIVO ADJUNTO
{'='*50}
Se adjunta archivo Excel con el reporte completo incluyendo:
- Hoja 1 - Concentrado: Resumen por empleado
- Hoja 2 - Detalle: Registro detallado de cada asistencia

---
Este es un reporte automático del Sistema de Checador de Asistencias
Patio La Esperanza
"""
        return texto

    def _registrar_historial(self, destinatarios, estado, num_empleados, mensaje_error=''):
        """Registra el envío en el historial"""
        try:
            HistorialReporte.objects.create(
                fecha_inicio=self.fecha_inicio,
                fecha_fin=self.fecha_fin,
                destinatarios=', '.join(destinatarios) if destinatarios else '',
                estado=estado,
                mensaje_error=mensaje_error,
                numero_empleados=num_empleados
            )
        except Exception as e:
            # Si falla el registro del historial, no queremos que afecte el proceso principal
            print(f"Error al registrar historial: {e}")
