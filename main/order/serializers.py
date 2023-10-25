from rest_framework import serializers
from .models import Order, OrderItems
from mall.models import CustomUser, Store
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class OrderSerializer(serializers.ModelSerializer):
   class Meta:
      model = Order
      fields = ['buyer', 'store', 'shipping_address']
      read_only_fields = ['id', 'created_at']
      
   # def validate_store(self, value):
   #    if store:
   #       store = get_object_or_404(Store, id=value)
   #       return store
   
   # def validate_buyer(self, value):
   #    return get_object_or_404(CustomUser, id=value)
      
class OrderItemSerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderItems
      fields = "__all__"