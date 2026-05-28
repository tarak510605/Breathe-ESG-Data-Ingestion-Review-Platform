FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || true

# Run migrations and server
CMD ["sh", "-c", "python manage.py migrate && gunicorn breathe.wsgi:application --bind 0.0.0.0:8000"]
