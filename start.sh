#!/bin/bash
# Startup script for RockTea Mall API

echo "🚀 Starting RockTea Mall API..."

# Navigate to main directory
cd main

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python manage.py shell -c "
from mall.models import CustomUser
if not CustomUser.objects.filter(is_superuser=True).exists():
    CustomUser.objects.create_superuser('admin', 'admin@yourockteamall.com', 'admin123')
    print('Superuser created: admin/admin123')
"

# Start the application
echo "🌟 Starting Django application..."
if [ "$ENV" = "production" ]; then
    gunicorn setup.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
else
    python manage.py runserver 0.0.0.0:${PORT:-8000}
fi