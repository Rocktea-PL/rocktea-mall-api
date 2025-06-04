from django_filters import rest_framework as filters
from mall.models import CustomUser

class DropshipperFilter(filters.FilterSet):
    total_products = filters.NumberFilter(method='filter_total_products')
    total_products_available = filters.NumberFilter(method='filter_total_products_available')
    total_products_sold = filters.NumberFilter(method='filter_total_products_sold')
    total_revenue = filters.NumberFilter(method='filter_total_revenue')
    is_active_user = filters.BooleanFilter(method='filter_is_active_user')
    
    class Meta:
        model = CustomUser
        fields = {
            'email': ['exact', 'contains'],
            'first_name': ['exact', 'contains'],
            'last_name': ['exact', 'contains'],
            'is_active': ['exact'],
            'is_verified': ['exact'],
            'date_joined': ['exact', 'gte', 'lte'],
            'last_login': ['exact', 'gte', 'lte'],
            'owners__name': ['exact', 'contains'],
        }

    def filter_total_products(self, queryset, name, value):
        return queryset.filter(total_products=value)

    def filter_total_products_available(self, queryset, name, value):
        return queryset.filter(total_products_available=value)

    def filter_total_products_sold(self, queryset, name, value):
        return queryset.filter(total_products_sold=value)

    def filter_total_revenue(self, queryset, name, value):
        return queryset.filter(total_revenue=value)

    def filter_is_active_user(self, queryset, name, value):
        return queryset.filter(is_active_user=value)