# Sistema de Turnos y Carga de Empleados

## Descripción General
Sistema completo para gestionar turnos rotativos y cargar empleados desde archivos Excel en el sistema de checador de Patio Esperanza.

## Turnos Disponibles

### Turno A - Matutino
- **Horario:** 7:00 AM - 3:00 PM
- **Duración:** 8 horas
- **Color:** Verde (#10B981)

### Turno B - Vespertino
- **Horario:** 3:00 PM - 11:00 PM
- **Duración:** 8 horas
- **Color:** Ámbar (#F59E0B)

### Turno C - Nocturno
- **Horario:** 11:00 PM - 7:00 AM
- **Duración:** 8 horas
- **Color:** Índigo (#6366F1)
- **Nota:** Este turno cruza medianoche

### Turno Fijo
- **Horario:** 8:00 AM - 6:00 PM
- **Duración:** 10 horas
- **Color:** Azul (#3B82F6)

## Carga de Empleados desde Excel

### Comando
```bash
python manage.py load_employees_from_excel PEsperanza.xlsx
```

### Opciones
- `--update`: Actualiza empleados existentes en lugar de omitirlos
- `--sheet NOMBRE`: Especifica el nombre de la hoja a leer (default: "Hoja1")

### Formato del Archivo Excel

El archivo debe contener los siguientes encabezados (el sistema reconoce variaciones):

| Campo | Alternativas Aceptadas | Requerido |
|-------|------------------------|-----------|
| codigo_empleado | codigo, código, id, employee_id | ✓ |
| nombre | nombres, name, first_name | ✓ |
| apellido | apellidos, last_name, surname | ✓ |
| email | correo, e-mail, mail | ✓ |
| departamento | depto, department, área, area | ✗ |
| puesto | cargo, position, job_title | ✗ |
| fecha_ingreso | fecha ingreso, hire_date | ✗ |
| horas_semana | horas, hours | ✗ |
| username | usuario, user | ✗ |

### Ejemplo de uso:

```bash
# Cargar empleados nuevos
python manage.py load_employees_from_excel /ruta/a/PEsperanza.xlsx

# Cargar y actualizar empleados existentes
python manage.py load_employees_from_excel PEsperanza.xlsx --update

# Especificar hoja diferente
python manage.py load_employees_from_excel PEsperanza.xlsx --sheet "Empleados"
```

### Notas sobre la carga:
- La contraseña temporal para todos los empleados nuevos es: `changeme123`
- Los empleados deben cambiar su contraseña en el primer inicio de sesión
- Si el username ya existe, se añade un número al final automáticamente
- Los empleados duplicados (mismo código) se omiten a menos que se use `--update`

## API de Turnos

### Endpoints Disponibles

#### 1. Gestión de Turnos
```
GET    /api/turnos/              - Lista todos los turnos
GET    /api/turnos/{id}/         - Detalle de un turno
POST   /api/turnos/              - Crear nuevo turno
PUT    /api/turnos/{id}/         - Actualizar turno
DELETE /api/turnos/{id}/         - Eliminar turno
```

**Filtros:**
- `?activo=true/false` - Filtrar por estado
- `?codigo=A` - Filtrar por código de turno

#### 2. Asignaciones de Turno
```
GET    /api/asignaciones/                    - Lista asignaciones
GET    /api/asignaciones/{id}/               - Detalle de asignación
POST   /api/asignaciones/                    - Crear asignación
PUT    /api/asignaciones/{id}/               - Actualizar asignación
DELETE /api/asignaciones/{id}/               - Eliminar asignación
```

**Filtros:**
- `?empleado={id}` - Asignaciones de un empleado
- `?turno={id}` - Asignaciones de un turno
- `?fecha=2026-01-21` - Asignaciones vigentes en una fecha
- `?activo=true/false` - Filtrar por estado

#### 3. Rol Semanal
```
GET /api/asignaciones/rol_semanal/
```

**Parámetros requeridos:**
- `fecha_inicio` (YYYY-MM-DD)
- `fecha_fin` (YYYY-MM-DD)

**Parámetros opcionales:**
- `departamento` - Filtrar por departamento

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/api/asignaciones/rol_semanal/?fecha_inicio=2026-01-20&fecha_fin=2026-01-26&departamento=Producción" \
  -H "Authorization: Bearer {token}"
```

#### 4. Empleados Disponibles
```
GET /api/asignaciones/empleados_disponibles/
```

Lista empleados sin turno asignado en una fecha específica.

**Parámetros:**
- `fecha` (YYYY-MM-DD) - Requerido
- `departamento` - Opcional

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/api/asignaciones/empleados_disponibles/?fecha=2026-01-21" \
  -H "Authorization: Bearer {token}"
```

#### 5. Asignación Masiva
```
POST /api/asignaciones/asignar_masivo/
```

Asigna un turno a múltiples empleados de una vez.

**Body:**
```json
{
  "empleados_ids": [1, 2, 3, 4],
  "turno_id": 1,
  "fecha_inicio": "2026-01-20",
  "fecha_fin": "2026-01-26",
  "dias": ["lunes", "martes", "miercoles", "jueves", "viernes"],
  "notas": "Asignación semana 3"
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/api/asignaciones/asignar_masivo/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "empleados_ids": [1, 2, 3],
    "turno_id": 1,
    "fecha_inicio": "2026-01-20",
    "fecha_fin": "2026-01-26",
    "dias": ["lunes", "martes", "miercoles", "jueves", "viernes"]
  }'
```

## Administración Django

Los modelos de Turno y AsignacionTurno están disponibles en el admin de Django:

```
http://localhost:8000/admin/turnos/
```

### Características del Admin:
- **Turnos:** Gestión completa de turnos con filtros por código y estado
- **Asignaciones:** Vista detallada con filtros por empleado, turno, fecha y departamento
- **Búsqueda:** Por código de empleado, nombre y notas
- **Jerarquía de fechas:** Navegación por fecha de inicio de asignación

## Modelos de Datos

### Turno
- `nombre`: Nombre descriptivo del turno
- `codigo`: Código único (A, B, C, FIJO)
- `hora_entrada`: Hora de inicio
- `hora_salida`: Hora de fin
- `cruza_medianoche`: Boolean para turnos nocturnos
- `descripcion`: Descripción adicional
- `color`: Color hexadecimal para UI
- `activo`: Estado del turno

### AsignacionTurno
- `empleado`: FK a Empleado
- `turno`: FK a Turno
- `fecha_inicio`: Fecha de inicio de asignación
- `fecha_fin`: Fecha de fin (nullable para indefinido)
- `aplica_lunes` a `aplica_domingo`: Días de la semana aplicables
- `notas`: Notas adicionales
- `activo`: Estado de la asignación

## Validaciones

### Turno
- La hora de salida debe ser posterior a la entrada (excepto si cruza medianoche)
- El código debe ser único

### AsignacionTurno
- La fecha de fin debe ser posterior a la fecha de inicio
- Debe seleccionarse al menos un día de la semana
- No puede haber solapamiento de asignaciones para el mismo empleado en los mismos días

## Ejemplos de Uso

### 1. Crear una asignación semanal
```python
from turnos.models import Turno, AsignacionTurno
from empleados.models import Empleado
from datetime import date

turno_a = Turno.objects.get(codigo='A')
empleado = Empleado.objects.get(codigo_empleado='EMP001')

asignacion = AsignacionTurno.objects.create(
    empleado=empleado,
    turno=turno_a,
    fecha_inicio=date(2026, 1, 20),
    fecha_fin=date(2026, 1, 26),
    aplica_lunes=True,
    aplica_martes=True,
    aplica_miercoles=True,
    aplica_jueves=True,
    aplica_viernes=True,
    aplica_sabado=False,
    aplica_domingo=False,
    notas='Primera semana turno A'
)
```

### 2. Obtener turno de un empleado en una fecha
```python
from datetime import date

fecha = date(2026, 1, 21)
empleado = Empleado.objects.get(codigo_empleado='EMP001')

asignacion = AsignacionTurno.objects.filter(
    empleado=empleado,
    activo=True,
    fecha_inicio__lte=fecha
).filter(
    Q(fecha_fin__gte=fecha) | Q(fecha_fin__isnull=True)
).first()

if asignacion and asignacion.aplica_en_fecha(fecha):
    print(f"Turno: {asignacion.turno.nombre}")
```

### 3. Listar empleados por turno
```python
turno_b = Turno.objects.get(codigo='B')
fecha = date.today()

asignaciones = AsignacionTurno.objects.filter(
    turno=turno_b,
    activo=True,
    fecha_inicio__lte=fecha
).filter(
    Q(fecha_fin__gte=fecha) | Q(fecha_fin__isnull=True)
)

for asig in asignaciones:
    if asig.aplica_en_fecha(fecha):
        print(f"{asig.empleado.nombre_completo} - {asig.turno.nombre}")
```

## Dashboard Frontend (Por Implementar)

El dashboard permitirá:
- Visualizar rol semanal en formato calendario
- Arrastrar y soltar empleados para asignar turnos
- Filtrar por departamento y semana
- Ver empleados disponibles
- Asignación masiva de turnos
- Exportar rol a PDF/Excel

## Mantenimiento

### Inicializar turnos predefinidos
Si necesitas recrear los turnos iniciales:
```bash
python manage.py init_turnos
```

### Verificar integridad de asignaciones
```python
from turnos.models import AsignacionTurno

# Verificar asignaciones con solapamiento
for empleado in Empleado.objects.filter(activo=True):
    asignaciones = AsignacionTurno.objects.filter(
        empleado=empleado,
        activo=True
    ).order_by('fecha_inicio')
    
    # Lógica de verificación de solapamiento
```

## Troubleshooting

### Error: "Ya existe una asignación activa"
Esto ocurre cuando intentas crear una asignación que solapa con otra existente. Verifica:
1. Las fechas de inicio y fin
2. Los días de la semana seleccionados
3. Asignaciones activas del empleado

### Los empleados no aparecen en el Excel
Verifica:
1. El formato de los encabezados del Excel
2. Que la columna de código de empleado no esté vacía
3. Los mensajes de error en la consola durante la carga

### El turno nocturno no calcula bien las horas
Asegúrate de que el campo `cruza_medianoche` esté marcado como `True` para turnos que cruzan medianoche.
