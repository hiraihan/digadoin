FROM python:3.10-slim

WORKDIR /code

# Install system dependencies for xhtml2pdf / pycairo
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .
