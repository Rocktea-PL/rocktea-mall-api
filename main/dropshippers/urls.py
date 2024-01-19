from .views import MyProducts
from django.urls import path
# from .dashboard_datas.order_data import MyOrders

urlpatterns = [
   path('products', MyProducts.as_view(), name='my-products'),
   # path('my-orders', MyOrders.as_view(), name='my-order')
]
