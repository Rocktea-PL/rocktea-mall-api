from .views import MyProducts, DropshipperAdminViewSet
from django.urls import path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'admin/dropshippers', DropshipperAdminViewSet, basename='admin-dropshippers')


urlpatterns = [
   path('products', MyProducts.as_view(), name='my-products'),
   path('admin/dropshippers/<uuid:id>/delete-all', 
         DropshipperAdminViewSet.as_view({'delete': 'destroy'}),
         name='admin-dropshipper-delete'),
] + router.urls
