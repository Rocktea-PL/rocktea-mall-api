# from order.models import Order, OrderItems
from order.serializers import OrderSerializer
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from order.models import StoreOrder


class MyOrders(generics.ListAPIView):
   serializer_class = OrderSerializer
   def get_queryset(self):
      user = self.request.user
      try:
         order = StoreOrder.objects.filter(buyer=user).count()
      except StoreOrder.DoesNotExist:
         return None
      return order