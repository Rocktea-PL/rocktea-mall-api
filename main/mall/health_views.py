"""
Health check views for monitoring
"""
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """Basic health check endpoint"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test Redis connection
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check') == 'ok'
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'ok',
            'cache': 'ok' if cache_status else 'error',
            'version': '1.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)