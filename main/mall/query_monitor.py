"""
Query monitoring middleware and utilities
"""
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class QueryCountMiddleware:
    """Monitor database query count per request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        queries_before = len(connection.queries)
        
        response = self.get_response(request)
        
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        
        # Log excessive queries
        if query_count > 10:
            logger.warning(f"High query count for {request.path}: {query_count} queries")
        
        # Add query count to response headers in debug mode
        if settings.DEBUG:
            response['X-Query-Count'] = str(query_count)
            response['X-Total-Queries'] = str(queries_after)
        
        return response

# Add this to your view to check queries manually
def debug_queries():
    """Print all queries executed"""
    if settings.DEBUG:
        for query in connection.queries:
            print(f"Query: {query['sql']}")
            print(f"Time: {query['time']}s")
            print("---")
        print(f"Total queries: {len(connection.queries)}")