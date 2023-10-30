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
      fields = ['id', 'buyer', 'store', 'shipping_address']
      read_only_fields = ['id', 'created_at']
      
      
      
class OrderItemSerializer(serializers.ModelSerializer):
   order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

   class Meta:
      model = OrderItems
      fields = "__all__"
   
   def create(self, validated_data):
      # Extract order details
      buyer = validated_data['buyer']
      store = validated_data['store']
      shipping_address = validated_data['shipping_address']

      # Create the order
      order = Order.objects.create(
         buyer=buyer,
         store=store,
         shipping_address=shipping_address
      )

      # Extract product details
      products_data = validated_data.get('product', [])
      quantity = validated_data['quantity']

      # Create order items
      for product_data in products_data:
         product = product_data['product']  # Assuming product is a ForeignKey in OrderItems
         OrderItems.objects.create(
               order=order,
               product=product,
               quantity=quantity,
               total_price=validated_data['total_price']
         )

      return order