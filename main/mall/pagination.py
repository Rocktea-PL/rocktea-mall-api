from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict

class OptimizedPageNumberPagination(PageNumberPagination):
    """Optimized pagination with configurable page sizes"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('results', data)
        ]))

class LargeDatasetPagination(PageNumberPagination):
    """Pagination optimized for large datasets"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
class SmallDatasetPagination(PageNumberPagination):
    """Pagination for smaller datasets"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class CursorPagination(LimitOffsetPagination):
    """Cursor-based pagination for better performance on large datasets"""
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('limit', self.limit),
            ('offset', self.offset),
            ('results', data)
        ]))