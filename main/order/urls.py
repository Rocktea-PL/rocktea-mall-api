from django.urls import path
from .views import AssignedOrders
# from .views import CreateOrder

urlpatterns = [
   # path('buy', CreateOrder.as_view(), name='make-order')
   path('my-orders/<str:rider>', AssignedOrders.as_view(), name='my_orders')
]
