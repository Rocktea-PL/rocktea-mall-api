FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=setup.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY main/requirements_optimized.txt .
RUN pip install --no-cache-dir -r requirements_optimized.txt

# Copy project
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Collect static files
RUN cd main && python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["./start.sh"]