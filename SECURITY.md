# Guía de Seguridad y Variables de Entorno

## ⚠️ IMPORTANTE: Nunca subir claves al repositorio

Este proyecto utiliza variables de entorno para **proteger información sensible**. NUNCA subas el archivo `.env` a git.

## Variables Requeridas

### Desarrollo Local
Para desarrollo local, copia `.env.example` a `.env` y configura:

```bash
cp .env.example .env
```

Luego edita `.env` con tus valores locales.

### Producción
En producción, **todas** estas variables deben estar configuradas en el servidor:

#### Django Core
- `SECRET_KEY` - **OBLIGATORIO**: Clave secreta de Django (genera una nueva para producción)
- `DEBUG` - Debe ser `False` en producción
- `ALLOWED_HOSTS` - Dominios permitidos (separados por coma)

#### Base de Datos
Opción 1: Variables individuales
- `DB_ENGINE` - Motor de base de datos (ej: `django.db.backends.mysql`)
- `DB_NAME` - Nombre de la base de datos
- `DB_USER` - Usuario de la base de datos
- `DB_PASSWORD` - **SENSIBLE**: Contraseña de la base de datos
- `DB_HOST` - Host de la base de datos
- `DB_PORT` - Puerto de la base de datos

Opción 2: URL única
- `DATABASE_URL` - **SENSIBLE**: URL completa de conexión (sobrescribe variables individuales)

#### JWT
- `JWT_ACCESS_TOKEN_LIFETIME` - Tiempo de vida del access token en minutos (default: 60)
- `JWT_REFRESH_TOKEN_LIFETIME` - Tiempo de vida del refresh token en minutos (default: 1440)

#### CORS y CSRF
- `CORS_ALLOWED_ORIGINS` - Orígenes permitidos para CORS (separados por coma)
- `CSRF_TRUSTED_ORIGINS` - Orígenes confiables para CSRF (separados por coma)

#### Email
- `EMAIL_BACKEND` - Backend de email (default: smtp)
- `EMAIL_HOST` - Host SMTP
- `EMAIL_PORT` - Puerto SMTP
- `EMAIL_USE_TLS` - Usar TLS (True/False)
- `EMAIL_HOST_USER` - Usuario SMTP
- `EMAIL_HOST_PASSWORD` - **SENSIBLE**: Contraseña/API key SMTP
- `DEFAULT_FROM_EMAIL` - Email remitente por defecto

#### DigitalOcean Spaces (Opcional)
- `USE_SPACES` - Habilitar Spaces (True/False)
- `DO_SPACES_ACCESS_KEY` - **SENSIBLE**: Access key de Spaces
- `DO_SPACES_SECRET_KEY` - **SENSIBLE**: Secret key de Spaces
- `DO_SPACES_BUCKET_NAME` - Nombre del bucket
- `DO_SPACES_ENDPOINT_URL` - URL del endpoint
- `DO_SPACES_REGION` - Región de Spaces
- `DO_SPACES_CDN_ENDPOINT` - CDN endpoint (opcional)

## Generar SECRET_KEY

Para generar una nueva `SECRET_KEY` segura en producción:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

O desde la terminal:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Checklist de Seguridad Pre-Deploy

Antes de hacer deploy a producción, verifica:

- [ ] `.env` NO está en el repositorio (verificar `.gitignore`)
- [ ] `SECRET_KEY` es única y diferente al valor de desarrollo
- [ ] `DEBUG=False` en producción
- [ ] `ALLOWED_HOSTS` contiene solo los dominios de producción
- [ ] Todas las contraseñas y API keys son diferentes a las de desarrollo
- [ ] `CSRF_TRUSTED_ORIGINS` incluye el dominio de producción con HTTPS
- [ ] `CORS_ALLOWED_ORIGINS` solo incluye orígenes autorizados
- [ ] Certificado SSL configurado (HTTPS)
- [ ] Variables de base de datos apuntan a la BD de producción
- [ ] EMAIL_HOST_PASSWORD configurado si se usa email

## Configuración en DigitalOcean App Platform

En el panel de DigitalOcean:
1. Ve a tu app > Settings > App-Level Environment Variables
2. Agrega cada variable como "Encrypted" (especialmente las sensibles)
3. Las variables `DIGITALOCEAN_APP_DOMAIN` y `DATABASE_URL` se configuran automáticamente

## Variables Auto-detectadas

Estas variables se detectan automáticamente en producción:
- `DIGITALOCEAN_APP_DOMAIN` - Dominio de la app en DigitalOcean
- `RENDER_EXTERNAL_HOSTNAME` - Hostname en Render
- `DATABASE_URL` - URL de base de datos (si el proveedor la establece)

## Buenas Prácticas

1. **Nunca hardcodear claves** en el código
2. **Rotar secretos regularmente** (especialmente después de un incidente)
3. **Usar valores diferentes** entre desarrollo y producción
4. **Limitar acceso** al archivo `.env` y variables de entorno en producción
5. **Documentar cambios** cuando agregues nuevas variables
6. **Validar valores** al iniciar la aplicación

## Troubleshooting

### Error: "SECRET_KEY must be set"
Solución: Agrega `SECRET_KEY` a tu archivo `.env` o variables de entorno

### Error: CORS/CSRF
Solución: Verifica que `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` incluyan tu dominio

### Error de Base de Datos
Solución: Verifica que todas las variables `DB_*` estén configuradas correctamente

## Contacto de Seguridad

Si encuentras un problema de seguridad, **NO lo reportes públicamente**. Contacta al equipo de desarrollo directamente.
