from rest_framework import serializers
from .models import OrderItems, Cart, CartItem, StoreOrder
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
      fields = ['product', 'quantity']
   
   def to_representation(self, instance):
      representation=super(OrderItemsSerializer, self).to_representation(instance)
      representation["product"]= [{"name": instance.product.name, "sku": instance.product.sku}]
      return representation


# class OrderSerializer(serializers.ModelSerializer):
#    items = OrderItemsSerializer(many=True)

#    class Meta:
#       model = Order
#       fields = ['id', 'user', 'store', 'created_at', 'total_price', 'items']
   
#    def to_representation(self, instance):
#       representation['total_amount'] = '{:,.2f}'.format(instance.total_price)
#       return representation


class OrderSerializer(serializers.ModelSerializer):
   buyer = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
   total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
   order_items = OrderItemsSerializer(many=True, read_only=True)
   created_at = serializers.SerializerMethodField()

   class Meta:
      model = StoreOrder
      fields = ['id', 'buyer', 'store', 'created_at', 'total_price', 'order_items']
      
   def get_created_at(self, obj):
      return obj.created_at.strftime("%Y-%m-%d %H:%M:%S%p")

   def to_representation(self, instance):
      representation = super(OrderSerializer, self).to_representation(instance)

      # Format the 'total_price' field with commas as thousands separator
      # representation['buyer'] = f"{instance.user.first_name} {instance.user.last_name}"
      representation['total_price'] = '{:,.2f}'.format(instance.total_price)
      return representation


class CartItemSerializer(serializers.ModelSerializer):
   product = serializers.SerializerMethodField()
   
   class Meta:
      model = CartItem
      fields = ['id', 'product', 'product_variant', 'quantity']
      
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