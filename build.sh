#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing system dependencies..."

# Install system dependencies for OpenCV and dlib
apt-get update
apt-get install -y \
    build-essential \
    cmake \
    g++ \
    gfortran \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglib2.0-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libjpeg-dev \
    libpng-dev

echo "System dependencies installed successfully"

# Set compilation flags for dlib
export CC=gcc
export CXX=g++
export MAKEFLAGS="-j$(nproc)"

echo "Installing Python dependencies..."

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install numpy first (required by other packages)
pip install "numpy<2.0"

# Install dlib with specific options
echo "Installing dlib..."
pip install --no-cache-dir dlib==19.24.2

# Install remaining dependencies
echo "Installing remaining dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Build completed successfully!"
