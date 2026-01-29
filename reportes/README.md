# Sistema de Reportes Semanales

Sistema automático de envío de reportes de asistencia por correo electrónico con Django APScheduler.

## Características

- ✅ Envío automático semanal de reportes
- ✅ Reporte en formato Excel con dos hojas:
  - **Hoja 1 - Concentrado**: Resumen por empleado (días trabajados, faltas, retardos, horas totales)
  - **Hoja 2 - Detalle**: Registro detallado de cada asistencia
- ✅ Correo HTML con:
  - Top 5 empleados con más retardos
  - Lista de empleados con faltas
- ✅ Configuración flexible del horario de envío
- ✅ Múltiples destinatarios
- ✅ Historial de envíos
- ✅ API para gestión y envío manual

## Instalación

### 1. Dependencias

Ya están instaladas en `requirements.txt`:
```bash
django-apscheduler==0.7.0
openpyxl==3.1.5
```

### 2. Configuración de Email

Asegúrate de tener configuradas las variables de entorno en `.env`:

```env
# Configuración de Email (requerido para envío de reportes)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=tu_api_key_de_sendgrid
DEFAULT_FROM_EMAIL=Sistema de Checador <notificaciones@patiolaesperanza.com.mx>
```

### 3. Migraciones

```bash
python manage.py migrate reportes
python manage.py migrate django_apscheduler
```

## Configuración Inicial

### Opción 1: Desde el Admin de Django

1. Ir a `/admin/reportes/configuracionreporte/`
2. Configurar:
   - **Activo**: ✓ (activar envío automático)
   - **Día de envío**: Lunes (o el día que prefieras)
   - **Hora de envío**: 08:00:00
   - **Asunto del correo**: Reporte Semanal de Asistencias

3. Agregar destinatarios en `/admin/reportes/destinatarioreporte/`:
   - Email
   - Nombre (opcional)
   - Activo: ✓

### Opción 2: Desde la API

```bash
# Crear configuración
POST /api/reportes/configuracion/
{
  "activo": true,
  "dia_envio": 1,  # 1=Lunes, 2=Martes, ..., 7=Domingo
  "hora_envio": "08:00:00",
  "asunto_correo": "Reporte Semanal de Asistencias"
}

# Agregar destinatarios
POST /api/reportes/destinatarios/
{
  "email": "gerencia@patiolaesperanza.com.mx",
  "nombre": "Gerencia",
  "activo": true
}
```

## Uso

### Envío Automático

El sistema envía automáticamente el reporte según la configuración:
- **Día**: El día de la semana configurado
- **Hora**: La hora configurada
- **Periodo**: Semana anterior (Lunes a Domingo)

El scheduler se inicia automáticamente cuando arranca Django.

### Envío Manual

#### Desde la línea de comandos:

```bash
# Enviar reporte de la semana pasada (por defecto)
python manage.py enviar_reporte_semanal

# Enviar reporte de un periodo específico
python manage.py enviar_reporte_semanal --fecha-inicio=2026-01-20 --fecha-fin=2026-01-26
```

#### Desde la API:

```bash
# Reporte de la semana pasada
POST /api/reportes/historial/enviar_reporte_manual/
{}

# Reporte de periodo específico
POST /api/reportes/historial/enviar_reporte_manual/
{
  "fecha_inicio": "2026-01-20",
  "fecha_fin": "2026-01-26"
}
```

## API Endpoints

### Configuración
- `GET /api/reportes/configuracion/` - Listar configuraciones
- `GET /api/reportes/configuracion/actual/` - Obtener configuración actual
- `POST /api/reportes/configuracion/` - Crear configuración
- `PUT /api/reportes/configuracion/{id}/` - Actualizar configuración
- `PATCH /api/reportes/configuracion/{id}/` - Actualizar parcialmente

### Destinatarios
- `GET /api/reportes/destinatarios/` - Listar destinatarios
- `GET /api/reportes/destinatarios/activos/` - Listar solo activos
- `POST /api/reportes/destinatarios/` - Crear destinatario
- `PUT /api/reportes/destinatarios/{id}/` - Actualizar destinatario
- `DELETE /api/reportes/destinatarios/{id}/` - Eliminar destinatario

### Historial
- `GET /api/reportes/historial/` - Listar historial de envíos
- `POST /api/reportes/historial/enviar_reporte_manual/` - Enviar reporte manual

## Estructura del Reporte

### Email HTML

El correo incluye:
1. **Top 5 Empleados con más Retardos**
   - Tabla con código, nombre y cantidad de retardos
   - Resaltado en amarillo

2. **Empleados con Faltas**
   - Lista de empleados que faltaron
   - Número de faltas por empleado
   - Resaltado en rojo

3. **Archivo Excel adjunto**

### Archivo Excel

#### Hoja 1: Concentrado
| Código | Nombre | Días Trabajados | Faltas | Retardos | Horas Totales |
|--------|--------|-----------------|--------|----------|---------------|
| EMP001 | Juan   | 5               | 2      | 3        | 40.5          |

- Los empleados en el top 5 de retardos se resaltan en amarillo

#### Hoja 2: Detalle de Registros
| Código | Nombre | Fecha | Entrada | Salida | Horas | Retardo | Notas |
|--------|--------|-------|---------|--------|-------|---------|-------|
| EMP001 | Juan   | 20/01 | 08:15   | 17:00  | 8.75  | Sí      | -     |

- Los retardos se resaltan en amarillo

## Desactivar Envíos Automáticos

Desde el Admin:
1. Ir a `/admin/reportes/configuracionreporte/`
2. Desmarcar **Activo**
3. Guardar

O desde la API:
```bash
PATCH /api/reportes/configuracion/{id}/
{
  "activo": false
}
```

## Consultar Historial

```bash
# Desde la API
GET /api/reportes/historial/

# Desde el Admin
/admin/reportes/historialreporte/
```

El historial muestra:
- Fecha de envío
- Periodo del reporte
- Destinatarios
- Estado (enviado/error)
- Mensaje de error (si aplica)
- Número de empleados en el reporte

## Troubleshooting

### El reporte no se envía automáticamente

1. Verificar que la configuración esté activa:
   ```python
   from reportes.models import ConfiguracionReporte
   config = ConfiguracionReporte.objects.first()
   print(f"Activo: {config.activo}, Día: {config.dia_envio}, Hora: {config.hora_envio}")
   ```

2. Verificar que hay destinatarios activos:
   ```python
   from reportes.models import DestinatarioReporte
   print(DestinatarioReporte.objects.filter(activo=True).count())
   ```

3. Revisar los logs del servidor para errores del scheduler

### Error al enviar el correo

1. Verificar configuración de email en `.env`
2. Probar envío con el management command:
   ```bash
   python manage.py enviar_reporte_semanal
   ```
3. Revisar el historial para ver el mensaje de error específico

### No hay datos en el reporte

Verificar que hay registros de asistencia en el periodo:
```python
from registros.models import RegistroAsistencia
from datetime import date, timedelta

hoy = date.today()
hace_semana = hoy - timedelta(days=7)
print(RegistroAsistencia.objects.filter(fecha__gte=hace_semana).count())
```

## Producción en DigitalOcean App Platform

El sistema funciona automáticamente en App Platform. El scheduler se inicia cuando arranca gunicorn.

### Consideraciones:
- El scheduler funciona mientras el dyno esté activo
- Si el dyno se reinicia, el scheduler se reinicia automáticamente
- Los jobs programados se mantienen en la base de datos (tabla `django_apscheduler_djangojob`)

### Verificación en producción:
```bash
# Ver logs del servidor
doctl apps logs <app-id>
```

Buscar en los logs:
- `✓ Scheduler configurado: Reporte cada [Día] a las [Hora]`
- `✓ Scheduler de reportes iniciado correctamente`

## Notas

- El cálculo de faltas es simplificado: cuenta los días del periodo sin registro
- En un sistema real, deberías considerar:
  - Días laborables vs. no laborables
  - Vacaciones
  - Permisos
  - Días de descanso programados

- El top de retardos solo incluye empleados que tuvieron retardos en el periodo
- La hoja de concentrado muestra todos los empleados con al menos un registro en el periodo
