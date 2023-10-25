from django.http import Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItems, Store, CustomUser
from mall.models import Price, Product
from .serializers import OrderSerializer, OrderItemSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
import logging
from decimal import Decimal

class CreateOrder(APIView):
   def post(self, request, *args, **kwargs):
      try:
         # request reusability
         collect=request.data
         
         # Collect buyer info from server
         buyer = request.user.id
         verified_buyer = self.get_buyer(buyer)
         
         # Collect Store ID
         store = collect.get('store')
         verified_store = self.get_store(store)
         
         # Process Order
         order = self.make_order(verified_buyer, verified_store, collect)
         
         # Process Order Items
         product = collect.get('product', [])
         order_items = self.process_order_items(order, product)
         return Response({"order": OrderSerializer(order).data, "orderitems": OrderItemSerializer(order_items, many=True).data})
      
      except Exception as e:
         logging.exception("An unexpected error occured")
         return Response({"message": "An Unexpected Error Occured"}, status=500)
   
   def get_store(self, store_id):
      return get_object_or_404(Store, id=store_id)
   
   def get_buyer(self, buyer_id):
      return get_object_or_404(CustomUser, id=buyer_id)
   
   def get_product(self, product_id):
      # for pids in product_id:
      return get_object_or_404(Product, id=pids)
   
   def get_product_price(self, product_id, size_id):
      try:
         price = Price.objects.get(product=product_id, size=size_id)
      except Price.DoesNotExist:
         raise serializers.ValidationError({"message": "Price Does Not Exist"})
      return price.price
   
   def process_order_items(self, order, products):
      for product_data in products:
         product_id = product_data.get('product')
         quantity = product_data.get('quantity')

         # You may need to adjust this depending on your data structure
         product = get_object_or_404(Product, id=product_id)

         # Get the corresponding Price for the Product and Size (if applicable)
         price = self.get_product_price(product, product_data.get('size'))

         # Calculate the total price for the OrderItems
         total_price = price * quantity

         OrderItems.objects.create(order=order, product=product, quantity=quantity, total_price=total_price)

      # return order_items

   def make_order(self, buyer, store, collect):
      order_data = {
         "buyer": buyer.id,
         "store": store.id,
         "shipping_address": collect["shipping_address"]
      }
      with transaction.atomic():
         order = OrderSerializer(data=order_data)
         if order.is_valid():
               order.save()
               return order.instance
         else:
               logging.error("Order validation failed. Errors: %s", order.errors)
               raise serializers.ValidationError(order.errors)


   
   #  def create_order_items(self, order, products):
   #       for product_data in products:
#          product_id = product_data.get('product')
#          quantity = product_data.get('quantity')

#          # You may need to adjust this depending on your data structure
#          product = get_object_or_404(Product, id=product_id)

#          # Get the corresponding Price for the Product and Size (if applicable)
#          price = self.get_product_price(product, product_data.get('size'))

#          # Calculate the total price for the OrderItems
#          total_price = price * quantity

#          OrderItems.objects.create(order=order, product=product, quantity=quantity, total_price=total_price)
         
      

# class CreateOrder(APIView):
#    def post(self, request, *args, **kwargs):
#       try:
#             # Make request.data reusable
#             collect = request.data
#             buyer = request.user.id

#             # collect store & buyer id
#             store = self.get_store(collect.get('store'))
#             buyer = self.get_buyer(buyer)
#             # Create Order and OrderItems
#             order = self.create_order(buyer, store, collect)
#             products = collect.get('products', [])
#             self.create_order_items(order, products)
#             return Response(OrderSerializer(order).data)

#       except Http404 as e:
#             return Response({"detail": str(e)}, status=404)

#       except Exception as e:
#             # Log the exception for further investigation
#             logging.exception("An unexpected error occurred.")
#             return Response({"detail": "An unexpected error occurred."}, status=500)

#    def get_store(self, store):
#       return get_object_or_404(Store, id=store)

#    def get_buyer(self, buyer):
#       return get_object_or_404(CustomUser, is_consumer=True, id=buyer)

#    def create_order(self, buyer, store, collect):
#       order_data = {
#          'buyer': buyer.id,
#          'store': store.id,
#          'shipping_address': collect.get('shipping_address'),
#       }

#       with transaction.atomic():
#          order_serializer = OrderSerializer(data=order_data)
#          if order_serializer.is_valid(raise_exception=True):
#             order_serializer.save()
#             return order_serializer.instance
#          else:
#             order_serializer.errors
#             print(order_serializer)

#    def create_order_items(self, order, products):
#       for product_data in products:
#          product_id = product_data.get('product')
#          quantity = product_data.get('quantity')

#          # You may need to adjust this depending on your data structure
#          product = get_object_or_404(Product, id=product_id)

#          # Get the corresponding Price for the Product and Size (if applicable)
#          price = self.get_product_price(product, product_data.get('size'))

#          # Calculate the total price for the OrderItems
#          total_price = price * quantity

#          OrderItems.objects.create(order=order, product=product, quantity=quantity, total_price=total_price)

#    def get_product_price(self, product, size):
#       try:
#          # Assuming you have a Size model and a ForeignKey in the Price model
#          if size:
#                price = Price.objects.get(product=product, size=size).price
#          else:
#                # If there is no size specified, get the default price
#                price = Price.objects.get(product=product, size=None).price

#          return price if price is not None else Decimal('0.0')  # Default to 0 if price is None

#       except Price.DoesNotExist:
#          # Handle the case where the price is not found
#          raise serializers.ValidationError(f"Price not found for product {product.name} and size {size}")
