from rest_framework import serializers, status
from .models import OrderItems, Cart, CartItem, StoreOrder, OrderDeliveryConfirmation, StoreOrder
from mall.models import CustomUser, Store, Product
from mall.serializers import ProductSerializer
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging
from datetime import datetime


class OrderItemsSerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderItems
      fields = ['product', 'quantity', 'userorder', 'product_variant']
   
   def to_representation(self, instance):
      representation=super(OrderItemsSerializer, self).to_representation(instance)
      representation["product"]= [{"name": instance.product.name, "sku": instance.product.sku}]
      return representation


class OrderSerializer(serializers.ModelSerializer):
   buyer = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
   total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
   order_items = OrderItemsSerializer(many=True, read_only=True, source='items')
   created_at = serializers.SerializerMethodField()
   order_id = serializers.CharField(max_length=5, read_only=True)
   status = serializers.CharField(max_length=9, read_only=True)

   class Meta:
      model = StoreOrder
      fields = ['id', 'buyer', 'store', 'created_at', 'total_price', 'order_items', 'order_id', 'status']
      read_only_fields = ['order_items', 'order_id', 'status']
      
   def get_created_at(self, obj):
      return obj.created_at.strftime("%Y-%m-%d %H:%M:%S%p")

   def to_representation(self, instance):
      representation = super(OrderSerializer, self).to_representation(instance)
      representation['total_price'] = '{:,.2f}'.format(instance.total_price)
      order_items = OrderItemsSerializer(instance.items.all(), many=True).data
      representation['buyer'] = f"{instance.buyer.first_name} {instance.buyer.last_name}"
      representation['store'] = instance.store.name
      return representation


class CartItemSerializer(serializers.ModelSerializer):
   product = serializers.SerializerMethodField()
   
   class Meta:
      model = CartItem
      fields = ['id', 'product', 'product_variant', 'quantity', 'price']
      
   def get_product(self, obj):
      return {"id": obj.product.id, "name": obj.product.name, "images": [image.images.url for image in obj.product.images.all()] if obj.product.name else None} if obj.product.name else None



class CartSerializer(serializers.ModelSerializer):
   items = CartItemSerializer(many=True, read_only=True)
   user = serializers.SerializerMethodField()

   class Meta:
      model = Cart
      fields = ['id', 'user',  'store', 'created_at', 'items']

   def get_user(self, obj):
      return f"{obj.user.first_name} {obj.user.last_name}"


class OrderDeliverySerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderDeliveryConfirmation
      fields = ['id', 'userorder', 'code']