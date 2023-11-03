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
   
   def create(self, validated_data):
      order_items = super().create(validated_data)

      # Deduct the quantity bought from the quantity available for each product
      for product in order_items.product.all():
         product.quantity -= order_items.quantity
         product.save()
      return order_items

class OrderSerializer(serializers.ModelSerializer):
   order_items = OrderItemsSerializer(many=True, read_only=True)

   class Meta:
      model = Order
      fields = ('id', 'buyer', 'store', 'status', 'shipping_address', 'created_at', 'updated_at', 'order_items')
      
   def get_buyer(self, obj):
      return f"{obj.buyer.first_name} {obj.buyer.last_name}"