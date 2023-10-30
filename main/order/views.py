from django.http import Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItems, Store, CustomUser
from mall.models import Product
from .serializers import OrderSerializer, OrderItemSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
import logging
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist



class MakeOrder(ModelViewSet):
   queryset = Order.objects.select_related('buyer', 'store')
   serializer_class = OrderSerializer

class OrderItemsView(ModelViewSet):
   queryset = OrderItems.objects.select_related('order', 'product')
   serializer_class = OrderItemSerializer



class CreateOrder(APIView):
   def post(self, request):
      # Extract data from request
      collect = request.data
      customer_id = request.user.id

      # Verify Customer Exists
      customer = self.get_customer_or_raise(customer_id)

      # Collect Products
      products = collect["products"]
      total_price = Decimal('0.00')

      # Get the affiliate based on the referral code
      # affiliate_referral_code = collect.get("affiliate_referral_code")
      # affiliate = self.get_affiliate(affiliate_referral_code)

      # Create Order
      order = self.create_order(customer, collect)

      # Create Order Items
      total_price = self.create_order_items(order, products)

      # Set total price of the order
      order.instance.total_price = total_price
      order.instance.save()

      # Deduct 3% for affiliates and add it to their earnings
      # self.process_affiliate(affiliate, total_price)

      return Response({"message": "Order created successfully"}, status=status.HTTP_201_CREATED)

   def get_customer_or_raise(self, customer_id):
      try:
         return CustomUser.objects.get(id=customer_id, is_consumer=True)
      except CustomUser.DoesNotExist:
         raise ObjectDoesNotExist("User does not exist")

   def create_order(self, customer, collect,):
      order_data = {
         'buyer': customer.id,
         'status': "Pending",
         'shipping_address': collect["shipping_address"],
         'store': collect['store'],
      }
      # print(store)
      order = OrderSerializer(data=order_data)
      if order.is_valid():
         order.save()
         return order
      else:
         print(order.errors)
         raise serializers.ValidationError("Invalid order data")

   def create_order_items(self, order, products):
      total_price = Decimal('0.00')
      for product_data in products:
         product = self._get_product(product_data["product"])
         price = Decimal(str(product_data['price']))  # Convert to Decimal
         item_total_price = price * Decimal(str(product_data["quantity"]))  # Convert to Decimal
         total_price += item_total_price

         OrderItems.objects.create(
               order=order.instance,
               product=product,  # Use the product instance
               quantity=product_data["quantity"],
         )
      return total_price
   
   def _get_product(self, product_id):
      try:
         product = Product.objects.get(id=product_id)
         return product  # Return the entire Product instance
      except Product.DoesNotExist:
         logging.error(f"Product with ID '{product_id}' does not exist.")
         raise ObjectDoesNotExist("Product does not exist")