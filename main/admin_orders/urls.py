from django.urls import path, re_path
from rest_framework.routers import DefaultRouter
from .views import AdminOrderViewSet, AdminTransactionViewSet

# Create router for transactions only
router = DefaultRouter()
router.register(r'', AdminOrderViewSet, basename='admin-orders')
router.register(r'transactions', AdminTransactionViewSet, basename='admin-transactions')

urlpatterns = [
    # Transactions routes (must come before the catch-all pattern)
    *router.urls,

    # Orders list (GET /)
    # path('', AdminOrderViewSet.as_view({'get': 'list'})),
    
    # Individual order retrieval (GET /<identifier>/)
    path('<str:identifier>/', AdminOrderViewSet.as_view({'get': 'retrieve'})),
]