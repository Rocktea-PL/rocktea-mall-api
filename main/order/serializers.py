from rest_framework import serializers
from .models import Order, OrderItems
from mall.models import CustomUser, Store, Product
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

   
# WORKING VERSION (ONLY ONE ORDER ITEM)
class OrderItemsSerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderItems
      fields = ('id', 'order', 'product', 'quantity', 'price', 'total_price')
      
   def to_representation(self, instance):
      representation = super(OrderItemsSerializer, self).to_representation(instance)
      representation['order'] = {"id": instance.order.id, "buyer":f"{ instance.order.buyer.first_name} { instance.order.buyer.last_name}"}
      representation['product']=[{"id": product.id, "name":product.name, "SKU": product.sku} for product in instance.product.all()]
      return representation


class OrderSerializer(serializers.ModelSerializer):
   order_items = OrderItemsSerializer(many=True, read_only=True)

   class Meta:
      model = Order
      fields = ('id', 'buyer', 'store', 'status', 'shipping_address', 'created_at', 'updated_at', 'order_items')
      
   # def validate_buyer(self, value):
   #    if value:
   #       return get_object_or_404(CustomUser, id=value)
      
   def get_buyer(self, obj):
      return f"{obj.buyer.first_name} {obj.buyer.last_name}"
   
   # def create(self, validated_data):
   #    # Try to get the "buyer" from the validated_data
   #    buyer = validated_data.get("buyer")
   #    verified_buyer = self.get_buyer(buyer)
      
   #    order = Order.objects.create(buyer=verified_buyer, **validated_data)
   #    return order
   
   # def get_buyer(self, buyer_id):
   #    try:
   #       return get_object_or_404(CustomUser, id=buyer_id)
   #    except Exception as e:
   #       logging.exception("Error")