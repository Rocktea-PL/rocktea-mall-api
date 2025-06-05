from django_filters import rest_framework as filters
from django.db.models import Q
from mall.models import Product

class ProductFilter(filters.FilterSet):
    category_name = filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    brand_name = filters.CharFilter(field_name='brand__name', lookup_expr='icontains')
    amount = filters.NumberFilter(field_name='filter_by_amount')
    stock_status = filters.CharFilter(method='filter_by_stock_status')
    
    class Meta:
        model = Product
        fields = {
            'name': ['icontains'],
            'sku': ['icontains'],
            'quantity': ['exact', 'gte', 'lte'],
            'upload_status': ['exact'],
            'is_available': ['exact'],
        }

    def filter_by_stock_status(self, queryset, name, value):
        """Custom filter for stock status"""
        if value == 'out_of_stock':
            return queryset.filter(quantity=0)
        elif value == 'low_stock':
            return queryset.filter(quantity__lte=10, quantity__gt=0)
        elif value == 'in_stock':
            return queryset.filter(quantity__gt=10)
        return queryset

    def filter_by_amount(self, queryset, name, value):
        """Custom filter for wholesale price"""
        # Handle products without variants
        return queryset.filter(
            Q(product_variants__wholesale_price=value) |
            Q(product_variants__isnull=True, _wholesale_price_fallback=value)
        ).distinct()