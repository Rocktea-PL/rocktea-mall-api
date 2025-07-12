from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminProductViewSet,
    bulk_update_stock,
    approve_products
)

# Create router for admin product management
admin_router = DefaultRouter()
admin_router.register(r'', AdminProductViewSet, basename='admin-products')

urlpatterns = [
    # Include admin router
    path('', include(admin_router.urls)),

    path('<str:identifier>/', AdminProductViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='admin-product-detail'),
    
    # Bulk operations
    path('bulk-update-stock/', bulk_update_stock, name='bulk-update-stock'),
    path('approve/', approve_products, name='approve-products'),
]