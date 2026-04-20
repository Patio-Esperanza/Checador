"""
Servicio para detectar y notificar ausencias de empleados
que no han registrado entrada después de 30 min de su horario.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMessage

from empleados.models import Empleado
from registros.models import RegistroAsistencia
from reportes.models import DestinatarioReporte

MEXICO_TZ = ZoneInfo('America/Mexico_City')


def _obtener_entrada_esperada(empleado, fecha):
    """
    Retorna (hora_entrada, es_descanso) para el empleado en la fecha dada,
    siguiendo la misma prioridad que RegistroAsistencia._obtener_turno_del_dia.
    Retorna None si el empleado no tiene horario asignado para ese día.
    """
    from django.db.models import Q
    from turnos.models import RolMensual, AsignacionTurno

    dia_semana = fecha.isoweekday()

    # 1. RolMensual (override diario)
    try:
        rol = RolMensual.objects.select_related('turno').get(
            empleado=empleado,
            fecha=fecha,
        )
        if rol.es_descanso:
            return (None, True)
        if rol.turno:
            return (rol.turno.hora_entrada, False)
        return None
    except RolMensual.DoesNotExist:
        pass

    # 2. Horario por día de semana
    try:
        horario = empleado.horarios.get(dia_semana=dia_semana, activo=True)
        return (horario.hora_entrada, False)
    except Exception:
        pass

    # 3. AsignacionTurno
    asignaciones = AsignacionTurno.objects.filter(
        empleado=empleado,
        activo=True,
        fecha_inicio__lte=fecha,
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha)
    ).select_related('turno')

    for asignacion in asignaciones:
        if asignacion.aplica_en_fecha(fecha):
            return (asignacion.turno.hora_entrada, False)

    return None


class AusenciasAlertService:

    @staticmethod
    def obtener_ausentes(ahora_mexico):
        """
        Retorna empleados cuya hora_entrada_esperada + 30 min cayó en la ventana
        (ahora - 60min, ahora - 30min] y no han registrado entrada hoy.
        """
        hoy = ahora_mexico.date()
        ahora_dt = datetime.combine(hoy, ahora_mexico.time())
        ventana_inicio = ahora_dt - timedelta(minutes=60)
        ventana_fin = ahora_dt - timedelta(minutes=30)

        empleados_activos = Empleado.objects.filter(activo=True).prefetch_related('horarios')

        ausentes = []
        for empleado in empleados_activos:
            info = _obtener_entrada_esperada(empleado, hoy)
            if not info:
                continue
            hora_entrada, es_descanso = info
            if es_descanso or hora_entrada is None:
                continue

            entrada_dt = datetime.combine(hoy, hora_entrada)
            if not (ventana_inicio < entrada_dt <= ventana_fin):
                continue

            tiene_entrada = RegistroAsistencia.objects.filter(
                empleado=empleado,
                fecha=hoy,
                hora_entrada__isnull=False,
            ).exists()

            if not tiene_entrada:
                ausentes.append({
                    'empleado': empleado,
                    'hora_esperada': hora_entrada,
                })

        return ausentes

    @staticmethod
    def enviar_alerta(ausentes, ahora_mexico):
        """Envía email de alerta a todos los destinatarios activos."""
        destinatarios = list(
            DestinatarioReporte.objects.filter(activo=True).values_list('email', flat=True)
        )
        if not destinatarios:
            return {'success': False, 'message': 'Sin destinatarios configurados'}

        hoy = ahora_mexico.date()
        ahora_str = ahora_mexico.strftime('%H:%M')

        filas = ''.join(
            f'<tr>'
            f'<td style="padding:10px 14px;border-bottom:1px solid #e5e7eb">{a["empleado"].codigo_empleado}</td>'
            f'<td style="padding:10px 14px;border-bottom:1px solid #e5e7eb">{a["empleado"].nombre_completo}</td>'
            f'<td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;color:#DC2626;font-weight:bold">'
            f'{a["hora_esperada"].strftime("%H:%M")}</td>'
            f'</tr>'
            for a in ausentes
        )

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f3f4f6">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding:24px">
      <table width="600" cellpadding="0" cellspacing="0"
             style="margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;
                    box-shadow:0 1px 3px rgba(0,0,0,.12)">
        <!-- Header -->
        <tr>
          <td style="background:#DC2626;padding:20px 24px">
            <h1 style="margin:0;color:#fff;font-size:18px">
              &#9888; Alerta de Ausencias
            </h1>
            <p style="margin:6px 0 0;color:#fecaca;font-size:13px">
              {hoy.strftime('%A %d/%m/%Y').capitalize()} &mdash; Verificación a las {ahora_str} hrs
            </p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:24px">
            <p style="margin:0 0 16px;color:#374151">
              Los siguientes <strong>{len(ausentes)} empleado(s)</strong> no han registrado
              entrada 30 minutos después de su hora programada:
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #e5e7eb;border-radius:6px;overflow:hidden">
              <thead>
                <tr style="background:#f9fafb">
                  <th style="padding:10px 14px;text-align:left;font-size:12px;
                             color:#6b7280;text-transform:uppercase;letter-spacing:.05em">
                    Código
                  </th>
                  <th style="padding:10px 14px;text-align:left;font-size:12px;
                             color:#6b7280;text-transform:uppercase;letter-spacing:.05em">
                    Nombre
                  </th>
                  <th style="padding:10px 14px;text-align:left;font-size:12px;
                             color:#6b7280;text-transform:uppercase;letter-spacing:.05em">
                    Hora Esperada
                  </th>
                </tr>
              </thead>
              <tbody>{filas}</tbody>
            </table>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:14px 24px;
                     font-size:11px;color:#9ca3af;border-top:1px solid #e5e7eb">
            Sistema de Checador de Asistencias &mdash; Patio La Esperanza
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

        try:
            msg = EmailMessage(
                subject=(
                    f'[AUSENCIAS] {len(ausentes)} empleado(s) sin entrada '
                    f'— {hoy.strftime("%d/%m/%Y")} {ahora_str}'
                ),
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=destinatarios,
            )
            msg.content_subtype = 'html'
            msg.send(fail_silently=False)
            return {
                'success': True,
                'message': f'Alerta enviada a {len(destinatarios)} destinatario(s): {len(ausentes)} ausente(s)',
            }
        except Exception as exc:
            return {'success': False, 'message': str(exc)}
