FROM python:3.12-slim-bookworm

# Force rebuild - update this value to trigger new build
ARG BUILD_VERSION=20260217-v2

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    gfortran \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libjpeg-dev \
    libpng-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install setuptools FIRST (required for pkg_resources)
RUN pip install --no-cache-dir --upgrade pip setuptools>=70.0.0 wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies (setuptools must be installed before face_recognition)
RUN pip install --no-cache-dir setuptools>=70.0.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create media directory
RUN mkdir -p media/rostros media/asistencias

# Expose port
EXPOSE 8080

# Run migrations and start server
CMD python manage.py migrate --noinput && \
    gunicorn checador.wsgi:application --bind 0.0.0.0:8080 --workers 2 --timeout 120
