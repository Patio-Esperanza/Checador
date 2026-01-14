# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema de Control de Asistencias (Attendance Control System) with facial recognition. Built with Django 6.0 and Django REST Framework, using face_recognition/OpenCV for biometric authentication.

## Development Commands

```bash
# Activate virtual environment
source .venvChecadorLoginco/bin/activate

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run tests for specific app
python manage.py test authentication
python manage.py test empleados
python manage.py test horarios
python manage.py test registros

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic
```

## Architecture

### Django Apps

- **checador/** - Main project configuration (settings.py, urls.py, views.py for web dashboard)
- **authentication/** - JWT authentication via djangorestframework-simplejwt (register, login, logout, password change)
- **empleados/** - Employee management with facial embedding storage
- **horarios/** - Work schedule management (per-employee, per-day schedules with tolerance settings)
- **registros/** - Attendance records with facial recognition service

### Core Models

- `Empleado` - Links to Django User, stores face encoding in `embedding_rostro` (BinaryField, pickled numpy array)
- `Horario` - Employee schedules with day-of-week, entry/exit times, and tolerance minutes
- `RegistroAsistencia` - Daily attendance records with entry/exit times, facial recognition confidence, and GPS coordinates

### Facial Recognition Flow

The `FacialRecognitionService` in `registros/services/facial_recognition.py`:
1. Loads images from uploaded files or paths
2. Validates image quality (brightness, blur, size)
3. Extracts face encodings using face_recognition library
4. Compares encodings against stored employee embeddings (tolerance: 0.6)
5. Returns matched employee with confidence percentage

Key parameters: `FACE_TOLERANCE=0.6`, `MIN_FACE_SIZE=(50,50)`, `MAX_FACES_ALLOWED=1`

### API Structure

All APIs are under `/api/`:
- `/api/auth/` - Authentication endpoints (JWT tokens)
- `/api/empleados/` - Employee CRUD + `/registrar-rostro/` endpoint
- `/api/horarios/` - Schedule CRUD + `/bulk-create/`
- `/api/registros/` - Attendance CRUD + `/marcar_entrada/` and `/marcar_salida/` (AllowAny for facial recognition)

### Web Views

Non-API views in `checador/views.py`:
- `/login/`, `/register/`, `/logout/` - Session-based auth
- `/dashboard/` - Admin dashboard
- `/empleados/`, `/registros/` - Staff views
- `/` and `/facial/` - Facial recognition check-in page

### Storage

Configurable storage backends:
- Local: Uses WhiteNoise for static files, local filesystem for media
- DigitalOcean Spaces: Set `USE_SPACES=True` in environment, uses S3-compatible storage via django-storages

Media files stored in:
- `rostros/` - Employee face photos
- `asistencias/` - Check-in photos

### Environment Variables

Key settings loaded from environment:
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DATABASE_URL` - Used in production (supports PostgreSQL and MySQL with SSL)
- `JWT_ACCESS_TOKEN_LIFETIME`, `JWT_REFRESH_TOKEN_LIFETIME` (in minutes)
- `USE_SPACES`, `DO_SPACES_*` - DigitalOcean Spaces configuration

### Timezone

Configured for Mexico City (`America/Mexico_City`), language `es-mx`.
