"""
Health check views for monitoring
"""
from django.http import JsonResponse
from django.utils import timezone

def health_check(request):
    """Minimal health check endpoint"""
    try:
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'rocktea-mall-api',
            'version': '1.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)