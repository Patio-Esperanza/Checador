# 📊 Guía Rápida - Sistema de Reportes Semanales

## ✅ ¿Qué se implementó?

Sistema completo de envío automático de reportes semanales por correo electrónico con:

- **Reporte en Excel** con 2 hojas (concentrado + detalle)
- **Correo HTML** con top 5 retardos y empleados con faltas
- **Envío automático** programable por día y hora
- **API REST** para administración completa
- **Compatible con DigitalOcean App Platform**

## 🚀 Configuración Inicial (3 pasos)

### 1. En DigitalOcean - Variables de Entorno

Ya están configuradas, solo verifica:
```
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<tu-api-key>
DEFAULT_FROM_EMAIL=Sistema de Checador <notificaciones@patiolaesperanza.com.mx>
SECRET_KEY=<tu-secret-key>
```

### 2. Configurar Horario de Envío

**Opción A: Admin de Django** (recomendado)
1. Ir a: `https://tu-app.ondigitalocean.app/admin/reportes/configuracionreporte/`
2. Crear/Editar configuración:
   - ✅ **Activo**: Marcar
   - **Día de envío**: `1` (Lunes) o el día que prefieras
   - **Hora de envío**: `08:00:00`
   - **Asunto**: `Reporte Semanal de Asistencias`
3. Guardar

**Días de la semana:**
- 1 = Lunes
- 2 = Martes
- 3 = Miércoles
- 4 = Jueves
- 5 = Viernes
- 6 = Sábado
- 7 = Domingo

### 3. Agregar Destinatarios

**Opción A: Admin de Django**
1. Ir a: `https://tu-app.ondigitalocean.app/admin/reportes/destinatarioreporte/`
2. Clic en "Agregar destinatario de reporte"
3. Llenar:
   - **Email**: `gerencia@patiolaesperanza.com.mx`
   - **Nombre**: `Gerencia` (opcional)
   - ✅ **Activo**: Marcar
4. Guardar
5. Repetir para cada destinatario

**Opción B: API**
```bash
curl -X POST https://tu-app.ondigitalocean.app/api/reportes/destinatarios/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gerencia@patiolaesperanza.com.mx",
    "nombre": "Gerencia",
    "activo": true
  }'
```

## 📧 Contenido del Reporte

### Email HTML
- **Top 5 empleados con más retardos** (resaltados en amarillo)
- **Lista de empleados con faltas** (resaltados en rojo)
- **Archivo Excel adjunto**

### Excel (2 hojas)

**Hoja 1 - Concentrado:**
| Código | Nombre | Días Trabajados | Faltas | Retardos | Horas Totales |
|--------|--------|-----------------|--------|----------|---------------|
| EMP001 | Juan Pérez | 5 | 2 | 3 | 40.5 |

**Hoja 2 - Detalle:**
| Código | Nombre | Fecha | Entrada | Salida | Horas | Retardo | Notas |
|--------|--------|-------|---------|--------|-------|---------|-------|
| EMP001 | Juan Pérez | 20/01/26 | 08:15 | 17:00 | 8.75 | Sí | - |

## 🔄 Funcionamiento Automático

- El sistema se ejecuta **automáticamente** cada semana
- Envía el reporte de la **semana anterior** (Lunes a Domingo)
- Se ejecuta el día y hora configurados
- No requiere intervención manual

## 🎯 Envío Manual (cuando lo necesites)

### Desde el Servidor

**SSH a tu servidor o desde App Platform Console:**
```bash
# Reporte de la semana pasada
python manage.py enviar_reporte_semanal

# Reporte de periodo específico
python manage.py enviar_reporte_semanal \
  --fecha-inicio=2026-01-20 \
  --fecha-fin=2026-01-26
```

### Desde la API

```bash
# Reporte de la semana actual (Lunes hasta hoy)
curl -X POST https://tu-app.ondigitalocean.app/api/reportes/historial/enviar_reporte_manual/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'

# Reporte de periodo específico
curl -X POST https://tu-app.ondigitalocean.app/api/reportes/historial/enviar_reporte_manual/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha_inicio": "2026-01-20",
    "fecha_fin": "2026-01-26"
  }'
```

## 📊 Ver Historial de Envíos

**Admin:**
`https://tu-app.ondigitalocean.app/admin/reportes/historialreporte/`

**API:**
```bash
curl https://tu-app.ondigitalocean.app/api/reportes/historial/ \
  -H "Authorization: Bearer <token>"
```

## 🛠️ API Endpoints Disponibles

Base URL: `https://tu-app.ondigitalocean.app/api/reportes/`

### Configuración
- `GET /configuracion/` - Listar
- `GET /configuracion/actual/` - Ver actual
- `PUT /configuracion/{id}/` - Actualizar
- `PATCH /configuracion/{id}/` - Actualizar parcialmente

### Destinatarios
- `GET /destinatarios/` - Listar todos
- `GET /destinatarios/activos/` - Listar solo activos
- `POST /destinatarios/` - Crear nuevo
- `PUT /destinatarios/{id}/` - Actualizar
- `DELETE /destinatarios/{id}/` - Eliminar

### Historial
- `GET /historial/` - Ver historial de envíos
- `POST /historial/enviar_reporte_manual/` - Enviar ahora

## ⚙️ Activar/Desactivar Envíos

### Desactivar temporalmente

**Admin:**
1. Ir a configuración
2. Desmarcar ✅ **Activo**
3. Guardar

**API:**
```bash
curl -X PATCH https://tu-app.ondigitalocean.app/api/reportes/configuracion/1/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"activo": false}'
```

### Reactivar

Marcar ✅ **Activo** o enviar `"activo": true` en la API

## 🔍 Verificación en Producción

### Ver logs en DigitalOcean

```bash
doctl apps logs <app-id> --type run
```

Buscar en los logs:
- `✓ Scheduler configurado: Reporte cada Lunes a las 08:00:00`
- `✓ Scheduler de reportes iniciado correctamente`
- `[fecha] Ejecutando job de reporte semanal...`
- `✓ Reporte enviado exitosamente a X destinatarios`

## ❓ Troubleshooting

### No llegan los correos

1. **Verificar configuración email** en variables de entorno
2. **Verificar destinatarios activos:**
   - Admin: `/admin/reportes/destinatarioreporte/`
   - Deben tener ✅ **Activo** marcado
3. **Verificar SendGrid:**
   - API Key válida
   - Sender verificado

### El scheduler no funciona

1. **Verificar que la configuración esté activa:**
   - Admin: `/admin/reportes/configuracionreporte/`
   - ✅ **Activo** debe estar marcado
2. **Ver logs del servidor**
3. **Reiniciar la app** en DigitalOcean

### Enviar reporte de prueba

```bash
# Desde el servidor
python manage.py enviar_reporte_semanal
```

Esto te dirá inmediatamente si hay algún problema.

## 📚 Documentación Completa

Ver `reportes/README.md` para documentación técnica detallada.

## 🎉 ¡Listo!

El sistema ya está funcionando. Solo necesitas:
1. ✅ Configurar el horario (Paso 2)
2. ✅ Agregar destinatarios (Paso 3)
3. ✅ Verificar que llegue el primer reporte

---

**Soporte:** Revisar logs en DigitalOcean o ejecutar comando manual para debugging.
