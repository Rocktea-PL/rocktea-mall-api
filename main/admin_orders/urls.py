from django.urls import path, re_path
from rest_framework.routers import DefaultRouter
from .views import AdminOrderViewSet

router = DefaultRouter()
router.register(r'', AdminOrderViewSet, basename='admin-orders')

urlpatterns = [
    path('<str:identifier>/', AdminOrderViewSet.as_view({'get': 'retrieve'})),
    *router.urls
]