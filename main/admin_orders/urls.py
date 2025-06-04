from django.urls import path, re_path
from .views import AdminOrderViewSet, AdminTransactionViewSet

urlpatterns = [

    # Orders list (GET /)
    path('', AdminOrderViewSet.as_view({'get': 'list'})),
    path('transactions/', AdminTransactionViewSet.as_view({'get': 'list'})),
    
    # Individual order retrieval (GET /<identifier>/)
    path('<str:identifier>/', AdminOrderViewSet.as_view({'get': 'retrieve'})),
]