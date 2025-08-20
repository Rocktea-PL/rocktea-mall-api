from rest_framework import serializers, status
from .models import (
   OrderItems, 
   Cart, 
   CartItem, 
   StoreOrder, 
   OrderDeliveryConfirmation, 
   StoreOrder, 
   AssignOrder,
   PaymentHistory,
   WithdrawalRecord
   )
from mall.models import (
   CustomUser, 
   Store, 
   Product,
   ProductVariant,
   StoreProductPricing
   )
from mall.serializers import ProductSerializer
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging
from datetime import datetime
from django.core.cache import cache


class OrderItemsSerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderItems
      fields = ['product', 'quantity', 'userorder', 'product_variant']
   
   def to_representation(self, instance):
      representation=super(OrderItemsSerializer, self).to_representation(instance)
      store_id = instance.userorder.store.id 
      pricing = StoreProductPricing.objects.get(product=instance.product, store=store_id) 
      retail_price = pricing.retail_price
      representation["product"]= [
         {
            "id": instance.product.id, 
            "name": instance.product.name, 
            "sku": instance.product.sku, 
            "size": instance.product_variant.size, 
            "color": instance.product_variant.colors, 
            "images": [image.images.url for image in instance.product.images.all()],
            "price": retail_price,
            "store": store_id
         }
      ]
      return representation

class AssignedOrderSerializer(serializers.ModelSerializer):
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
      cache_key = f"Order_Key_{instance.id}"
      cached_data = cache.get(cache_key)
      
      if cached_data is not None:
         return cached_data
      
      representation = super(AssignedOrderSerializer, self).to_representation(instance)
      representation['total_price'] = '{:,.2f}'.format(instance.total_price)
      order_items = OrderItemsSerializer(instance.items.all(), many=True).data
      representation['buyer'] = {"name": f"{instance.buyer.first_name} {instance.buyer.last_name}", "contact": str(getattr(instance.buyer, 'contact', None))}
      representation['store'] = instance.store.name
      
      cache.set(cache_key, representation, timeout=60 * 3)
      return representation

class OrderSerializer(serializers.ModelSerializer):
   buyer = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
   total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
   order_items = OrderItemsSerializer(many=True, read_only=True, source='items')
   created_at = serializers.SerializerMethodField()
   order_id = serializers.CharField(max_length=5, read_only=True)
   status = serializers.CharField(max_length=9) # , read_only=True
   delivery_code = serializers.CharField(max_length=5, read_only=True)

   # Logistics
   rider_assigned = serializers.CharField(max_length=32, read_only=True)

   class Meta:
      model = StoreOrder
      fields = ['id', 'buyer', 'store', 'created_at', 'total_price', 'order_items', 'order_id', 'delivery_code', 'rider_assigned', 'status', 'tracking_id', 'tracking_url', 'tracking_status', 'shipping_fee', 'delivery_location']
      read_only_fields = ['order_items', 'order_id'] # , 'status'

   def get_created_at(self, obj):
      return obj.created_at.strftime("%Y-%m-%d %H:%M:%S%p")
   
   # def create(self)

   def to_representation(self, instance):
      cache_key = f"order_id {instance.id}"
      cached_data = cache.get(cache_key)
      
      if cached_data is not None:
         return cached_data
      
      representation = super(OrderSerializer, self).to_representation(instance)
      representation['total_price'] = '{:,.2f}'.format(instance.total_price)
      order_items = OrderItemsSerializer(instance.items.all(), many=True).data
      representation['buyer'] = {"name": f"{instance.buyer.first_name} {instance.buyer.last_name}", "contact": str(getattr(instance.buyer, 'contact', None))}
      representation['store'] = instance.store.name
      representation['rider_assigned'] = self.get_assigned_rider(instance.id)
      representation['tracking_id'] = instance.tracking_id
      representation['tracking_url'] = instance.tracking_url
      representation['tracking_status'] = instance.tracking_status
      cache.set(cache_key, representation, timeout=60*2)
      
      return representation


   def get_assigned_rider(self, storeorder_id):
      try:
         storeorders = AssignOrder.objects.filter(order=storeorder_id)
      except AssignOrder.DoesNotExist:
         return None

      if storeorders.exists():
         # Choose the first assigned rider or implement your own logic
         return {"full_name": f"{storeorders.first().rider.first_name} {storeorders.first().rider.last_name}",
               "profile_image": storeorders.first().rider.profile_image.url}
      else:
         return None

class CartItemSerializer(serializers.ModelSerializer):
   product = serializers.SerializerMethodField()
   formatted_price = serializers.SerializerMethodField()
   
   class Meta:
      model = CartItem
      fields = ['id', 'product', 'product_variant', 'quantity', 'price', 'formatted_price']
      
   def get_product(self, obj):
      if obj.product:
         return {
            "id": obj.product.id, 
            "name": obj.product.name, 
            "images": [image.images.url for image in obj.product.images.all()]
         }
      return None
   
   def get_formatted_price(self, obj):
      return f"{float(obj.price):.2f}" if obj.price else "0.00"

class CartSerializer(serializers.ModelSerializer):
   items = CartItemSerializer(many=True, read_only=True)
   user = serializers.SerializerMethodField()
   total_price = serializers.SerializerMethodField()
   items_count = serializers.SerializerMethodField()

   class Meta:
      model = Cart
      fields = ['id', 'user', 'store', 'created_at', 'items', 'total_price', 'items_count']

   def get_user(self, obj):
      return f"{obj.user.first_name} {obj.user.last_name}"
   
   def get_total_price(self, obj):
      return f"{float(obj.price):.2f}" if obj.price else "0.00"
   
   def get_items_count(self, obj):
      return obj.items.count()

   def validate_items(self, value):
      if not value:
         raise serializers.ValidationError("Items cannot be empty.")
      for item in value:
         if 'product_variant' not in item or 'quantity' not in item or 'price' not in item:
               raise serializers.ValidationError("Each item must include 'product_variant', 'quantity', and 'price'.")
      return value

   def create(self, validated_data):
      items_data = validated_data.pop('items')
      cart = Cart.objects.create(**validated_data)
      for item_data in items_data:
         CartItem.objects.create(cart=cart, **item_data)
      return cart

class OrderDeliverySerializer(serializers.ModelSerializer):
   class Meta:
      model = OrderDeliveryConfirmation
      fields = ['id', 'userorder', 'code']
      
class AssignOrderSerializer(serializers.ModelSerializer):
   class Meta:
      model = AssignOrder
      fields = ['id', 'order', 'rider']

   # def validate(self, data):
   #    orders = data.get('order')
   #    rider = data.get('rider')

      # return data
   def create(self, validated_data):
      orders_data = validated_data.pop('order')
      assign_order = AssignOrder.objects.create(**validated_data)

      for order in orders_data:
         assign_order.order.add(order)

      return assign_order
   
   def to_representation(self, instance):
      representation = super(AssignOrderSerializer, self).to_representation(instance)

      # Retrieve the rider information
      rider_info = {
         "name": f"{instance.rider.first_name} {instance.rider.last_name}",
         "profile_image": instance.rider.profile_image.url,
         "email": instance.rider.email
      }
      representation['rider'] = rider_info

      # Retrieve the order information
      order_info = [{"id": order.id, "owner": f"{order.buyer.first_name} {order.buyer.last_name}", "from": order.store.name} for order in instance.order.all()]
      representation['order'] = order_info

      return representation

class PaymentHistorySerializers(serializers.ModelSerializer):
   class Meta:
      model = PaymentHistory
      fields = ["store", "order", "amount", "payment_date"]
      
   def to_representation(self, instance):
      representation = super(PaymentHistorySerializers, self).to_representation(instance)
      
      representation['order'] = {
         "status": instance.order.status, 
         "buyer": f"{instance.order.buyer.first_name} {instance.order.buyer.last_name}",
         "reference": instance.order.id
      }
      
      representation['payment_date'] = instance.payment_date.strftime("%Y-%m-%d")
      return representation

class WithdrawalRecordSerializer(serializers.ModelSerializer):
   class Meta:
      model = WithdrawalRecord
      fields = ['id', 'amount', 'status', 'created_at', 'processed_at', 'transfer_code']
      read_only_fields = ['id', 'created_at', 'processed_at', 'transfer_code']
   
   def to_representation(self, instance):
      representation = super().to_representation(instance)
      representation['created_at'] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")
      if instance.processed_at:
         representation['processed_at'] = instance.processed_at.strftime("%Y-%m-%d %H:%M:%S")
      return representation