from django.http import Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItems, Store, CustomUser, Cart, CartItem
from mall.models import Product, ProductVariant, StoreProductVariant, CustomUser
from .serializers import OrderSerializer, OrderItemsSerializer, CartSerializer, CartItemSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
import logging
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets


class CreateOrder(APIView):
   def post(self, request):
      # Extract data from request
      collect = request.data
      customer_id = self.request.query_params.get("buyer")

      # Verify Customer Exists
      customer = self.get_customer_or_raise(customer_id)
      if customer is None:
         return Response({"error": "Customer does not exist"}, status=status.HTTP_400_BAD_REQUEST)

      # Collect Products
      products = collect["products"]
      total_price = Decimal('0.00')

      # Get the affiliate based on the referral code
      store_id = collect.get("store")
      store = self.get_store(store_id)

      # Create Order
      order = self.create_order(customer_id, collect, store)

      # Create Order Items
      total_price = self.create_order_items(order, products)
      order.save()

      return Response({"message": "Order created successfully"}, status=status.HTTP_201_CREATED)

   def get_store(self, store_id):
      return get_object_or_404(Store, id=store_id)

   def get_customer_or_raise(self, customer_id):
      try:
         return CustomUser.objects.get(id=customer_id)
      except CustomUser.DoesNotExist:
         logging.exception("An Unexpected Error Occurred")
         return None

   def create_order(self, customer_id, collect, store):
      order_data = {
         'buyer': customer_id,
         'status': "Pending",
         'shipping_address': collect["shipping_address"],
         'store': store.id,
      }

      order_serializer = OrderSerializer(data=order_data)

      if order_serializer.is_valid():
         order = order_serializer.save()
         return order
      else:
         logging.error("An Error Occurred")
         print(order_serializer.errors)
         raise serializers.ValidationError("Invalid order data")

   def create_order_items(self, order, products):
      total_price = Decimal('0.00')
      for product_data in products:
         product = self.get_product(product_data["product"])
         price = self.get_product_price(product.id)

         if price is not None:
            item_total_price = Decimal(
                price) * Decimal(product_data["quantity"])
            total_price += item_total_price

            OrderItems.objects.create(
               order=order,
               product=product,
               quantity=product_data["quantity"],
            )
         else:
            # Handle the case where the price is not available for the product
            logging.error(
               "Price not available for product with id: {}".format(product.id))
         return total_price

   def get_product(self, product_sn):
      return get_object_or_404(Product, id=product_sn)
   

   def get_product_price(self, product_id, size):
      try:
         variant = ProductVariant.objects.get(product=product_id)
         return variant.wholesale_price
      except ProductVariant.DoesNotExist:
         logging.error("An Unexpected Error Occurred")
         return None


class OrderItemsViewSet(ModelViewSet):
   queryset = OrderItems.objects.all()
   serializer_class = OrderItemsSerializer


class OrderViewSet(ModelViewSet):
   queryset = Order.objects.all().select_related('buyer', 'store')
   serializer_class = OrderSerializer
   
   def get_queryset(self):
      store = self.request.query_params.get("store")
      if store:
         return Order.objects.filter(store=store).select_related('buyer', 'store')
      return Order.objects.all().select_related('buyer', 'store')
      
      
class CartViewSet(viewsets.ViewSet):
   def create(self, request):
      user = request.user
      products = request.data.get('products', [])
      
      # Check if the user already has a cart
      cart = Cart.objects.filter(user=user).first()
      
      if not cart:
         # Create a new cart if the user doesn't have one
         cart = Cart.objects.create(user=user)
      
      for product in products:
         product_id = product.get('id')
         quantity = product.get('quantity', 1)
         
         # Create a CartItem for each product and associate it with the cart
         cart_item = CartItem.objects.create(cart=cart, product_id=product_id, quantity=quantity)
         
      serializer = CartSerializer(cart)
      return Response(serializer.data)
   
   
class ViewOrders(ViewSet):
   def list(self, request):
      user = self.request.user.id
      queryset = Order.objects.filter(buyer=user).select_related("buyer", "store")
      serializer = OrderSerializer(queryset, many=True)
      return Response(serializer.data)