from .views import MyProducts
from django.urls import path

urlpatterns = [
   path('products', MyProducts.as_view(), name='my-products')
]
