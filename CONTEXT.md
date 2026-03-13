# Contexto del Proyecto: ChecadorEsperanza

> Generado automáticamente el 2026-03-13

## Descripción General

Sistema de Control de Asistencias con reconocimiento facial. Construido con **Django 6.0** y **Django REST Framework**, usa `face_recognition` y OpenCV para autenticación biométrica. Configurado para zona horaria `America/Mexico_City`, idioma `es-mx`.

---

## Stack Tecnológico

| Categoría | Tecnologías |
|---|---|
| Framework | Django 6.0, DRF 3.16.1 |
| Auth | djangorestframework-simplejwt 5.5.1 |
| Base de datos | SQLite (dev), PostgreSQL / MySQL (prod) |
| Almacenamiento | WhiteNoise (local), DigitalOcean Spaces S3 (prod) |
| Reconocimiento facial | face_recognition 1.3.0, OpenCV 4.10.0, dlib |
| Científico | NumPy 2.2.6, Pillow 12.0.0, scipy 1.16.3 |
| Reportes | openpyxl 3.1.5, reportlab 4.4.7 |
| Scheduler | django-apscheduler 0.7.0 |
| Producción | Gunicorn 23.0.0 |

> **Nota:** `setuptools` fijado en `<81` para mantener `pkg_resources` (requerido por face_recognition).

---

## Estructura del Proyecto

```
ChecadorEsperanza/
├── checador/            # Configuración principal (settings, urls, views web)
├── authentication/      # JWT auth (login, register, logout, password change)
├── empleados/           # Gestión de empleados + registro facial
├── horarios/            # Horarios por empleado/día de semana
├── registros/           # Registros de asistencia + servicio facial
├── turnos/              # Definición de turnos + asignaciones + rol mensual
├── reportes/            # Generación de reportes Excel + envío por email
├── templates/           # HTML templates (dashboard, facial, auth, etc.)
├── static/              # CSS, JS, imágenes
├── media/               # Fotos de empleados y capturas de asistencia
├── requirements.txt
├── Dockerfile
├── Procfile
├── app.yaml             # DigitalOcean App Platform
└── build.sh
```

---

## Modelos Principales

### `Empleado` (`empleados/models.py`)
- `codigo_empleado` – ID único del empleado
- `foto_rostro` – Imagen (ImageField → `rostros/`)
- `embedding_rostro` – Encoding facial (BinaryField, numpy array pickleado, 128 dimensiones)
- `departamento`, `puesto`, `horas_semana`, `fecha_ingreso`, `activo`
- `set_face_encoding(arr)` / `get_face_encoding()` – serialización pickle
- `tiene_rostro_registrado` – property bool
- OneToOne con Django `User`

### `Horario` (`horarios/models.py`)
- FK → Empleado, FK opcional → Turno
- `dia_semana` (1=Lunes…7=Domingo)
- `hora_entrada`, `hora_salida`, `tolerancia_minutos` (default 10)
- Unique constraint: `(empleado, dia_semana)`

### `Turno` (`turnos/models.py`)
- `codigo` único (ej: "A", "B", "C")
- `hora_entrada`, `hora_salida`, `cruza_medianoche` (bool)
- `color` (hex), `activo`

### `AsignacionTurno` (`turnos/models.py`)
- FK → Empleado, FK → Turno (PROTECT)
- `fecha_inicio`, `fecha_fin` (opcional = indefinido)
- Flags por día: `aplica_lunes` … `aplica_domingo`
- Validación: no se permiten traslapes en mismos días

### `RolMensual` (`turnos/models.py`)
- FK → Empleado, FK opcional → Turno
- `fecha` (DateField) – Unique `(empleado, fecha)`
- `es_descanso` (bool), `notas`
- `obtener_rol_mes(year, month)` – classmethod devuelve dict del mes

### `RegistroAsistencia` (`registros/models.py`)
- FK → Empleado
- `fecha`, `hora_entrada`, `hora_salida`
- `foto_registro` → `asistencias/`
- `reconocimiento_facial` (bool), `confianza_reconocimiento` (float 0-100)
- `latitud`, `longitud` (Decimal, opcional)
- `retardo` (bool, calculado automáticamente), `justificado` (override admin)
- `horas_trabajadas` (float, calculado en save)
- Unique: `(empleado, fecha)`

### Modelos de Reportes (`reportes/models.py`)
- `ConfiguracionReporte` – config global (día/hora de envío, asunto)
- `DestinatarioReporte` – lista de emails receptores
- `HistorialReporte` – auditoría de reportes enviados

---

## Servicio de Reconocimiento Facial

**Archivo:** `registros/services/facial_recognition.py`
**Clase:** `FacialRecognitionService` (métodos estáticos)

### Constantes
```python
FACE_TOLERANCE = 0.6        # Distancia máxima (menor = más estricto)
MIN_FACE_SIZE   = (50, 50)  # Tamaño mínimo de rostro en píxeles
MAX_FACES_ALLOWED = 1       # Solo se permite 1 rostro por imagen
```

### Flujo de reconocimiento
1. `load_image_from_file()` – carga desde UploadedFile o ruta, convierte a RGB numpy
2. `validate_image_quality()` – valida brillo (30-225), enfoque (Laplacian ≥ 100), tamaño mínimo
3. `extract_face_encoding()` – detecta exactamente 1 rostro, extrae encoding 128-D
4. `recognize_employee()` – compara contra todos los empleados activos con rostro registrado
5. `compare_faces()` – distancia euclidiana → confianza `(1 - dist) * 100`

---

## API Endpoints

Base: `/api/`

### Auth (`/api/auth/`)
| Método | URL | Descripción |
|---|---|---|
| POST | `/login/` | Obtener tokens JWT |
| POST | `/token/refresh/` | Renovar access token |
| POST | `/register/` | Registrar usuario + empleado |
| POST | `/logout/` | Invalidar refresh token |
| GET/PUT | `/profile/` | Ver/actualizar perfil |
| POST | `/change-password/` | Cambiar contraseña |

### Empleados (`/api/empleados/`)
- CRUD estándar + filtros: `activo`, `departamento`, `search`
- `POST /{id}/registrar-rostro/` – registrar encoding facial (requiere foto, auth)
- `POST /{id}/eliminar-rostro/` – eliminar rostro registrado

### Horarios (`/api/horarios/`)
- CRUD + filtros: `empleado`, `dia_semana`, `activo`
- `POST /bulk-create/` – crear múltiples horarios para un empleado

### Registros (`/api/registros/`) — **AllowAny para marcar**
- CRUD + filtros: `empleado`, `fecha`, `fecha_inicio`, `fecha_fin`
- `POST /marcar_entrada/` – captura facial + GPS opcional
- `POST /marcar_salida/` – captura facial + GPS opcional

### Turnos y Asignaciones
- `/api/turnos/` – CRUD de definiciones de turno
- `/api/asignaciones/` – CRUD + `rol_semanal/`, `empleados_disponibles/`, `asignar_masivo/`

### Reportes (`/api/reportes/`)
- `configuracion/` – GET/PUT configuración general
- `destinatarios/` – CRUD de emails receptores
- `historial/` – solo lectura
- `POST historial/enviar_reporte_manual/` – envío manual por rango de fechas

---

## Vistas Web (Session-based)

| URL | Vista | Acceso |
|---|---|---|
| `/` o `/facial/` | Reconocimiento facial | Público |
| `/login/` | Login | Público |
| `/register/` | Registro | Público |
| `/dashboard/` | Dashboard empleado | Autenticado |
| `/empleados/` | Lista de empleados | Staff |
| `/registros/` | Lista de asistencias | Staff |
| `/marcar-asistencia/` | Check-in web | Staff |
| `/rol-mensual/` | Rol mensual | Staff |

---

## Prioridad de Horarios (para calcular retardo)

```
RolMensual (override diario)
    ↓ si no existe
Horario (día de semana)
    ↓ si no existe
AsignacionTurno (rango de fechas)
```

---

## Configuración de Entorno

### Variables clave (`.env` o entorno)
```
SECRET_KEY
DEBUG
ALLOWED_HOSTS           # separadas por coma
DATABASE_URL            # prod: postgres:// o mysql://
USE_SPACES              # true para DigitalOcean Spaces
DO_SPACES_ACCESS_KEY
DO_SPACES_SECRET_KEY
DO_SPACES_BUCKET_NAME
DO_SPACES_ENDPOINT_URL
DO_SPACES_REGION_NAME
DO_SPACES_CDN_ENDPOINT
JWT_ACCESS_TOKEN_LIFETIME   # minutos (default 60)
JWT_REFRESH_TOKEN_LIFETIME  # minutos (default 1440)
CORS_ALLOWED_ORIGINS        # separadas por coma
CSRF_TRUSTED_ORIGINS
EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
```

### Base de datos
- **Dev:** SQLite3 (automático)
- **Prod PostgreSQL:** `sslmode=require`, `CONN_MAX_AGE=600`
- **Prod MySQL:** `ssl-mode=REQUIRED`, `utf8mb4`

### Almacenamiento de archivos
- **Local:** `media/checador/rostros/` y `media/checador/asistencias/`
- **DigitalOcean Spaces:** S3Boto3, CDN configurable

---

## Templates Principales

| Archivo | Descripción |
|---|---|
| `facial_recognition.html` | Página pública de marcado de asistencia facial |
| `dashboard.html` | Panel principal del empleado |
| `auth/login.html` | Login session-based |
| `auth/register.html` | Registro |
| `register_face.html` | UI de registro facial (requiere auth) |
| `empleados/lista.html` | Lista de empleados |
| `registros/lista.html` | Lista de asistencias |
| `turnos/rol_mensual.html` | Rol mensual interactivo |

---

## Notas de Despliegue

- **DigitalOcean App Platform:** `app.yaml`, detecta `DIGITALOCEAN_APP_DOMAIN`
- **Render.com:** detecta variable `RENDER`
- **Docker:** `Dockerfile` multi-stage optimizado para dlib/face_recognition
- **Procfile:** compatible Heroku
- **Aptfile:** dependencias del sistema (cmake, libdlib-dev, etc.)
- `SECURE_SSL_REDIRECT` desactivado → usa `X-Forwarded-Proto` detrás del proxy

---

## Observaciones y Puntos de Atención

| # | Observación | Impacto |
|---|---|---|
| 1 | Encodings faciales serializados con `pickle` (BinaryField) | Riesgo de incompatibilidad entre versiones de NumPy |
| 2 | `FACE_TOLERANCE = 0.6` es permisivo para uso de seguridad | Considerar 0.5 para mayor precisión |
| 3 | Endpoint `/marcar_entrada/` sin rate limiting (AllowAny) | Vulnerable a DoS / fuerza bruta |
| 4 | Email falla silenciosamente si `EMAIL_HOST_PASSWORD` no está configurado | Reportes no se envían sin error visible |
| 5 | Eliminar empleado no borra fotos huérfanas en disco/Spaces | Acumulación de archivos |
| 6 | Soporte de turnos nocturnos (cruza medianoche) con lógica especial en `_obtener_turno_del_dia()` | Área de alta complejidad |
