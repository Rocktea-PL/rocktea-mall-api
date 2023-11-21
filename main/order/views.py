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

      # Calculate total price
      # total_price = self.create_order_items(None, products, store)

      # Create Order
      order = self.create_order(customer_id, collect, store, total_price)

      # Create Order Items
      self.create_order_items(order, products, store)
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

   def create_order(self, customer_id, collect, store, total_price):
      order_data = {
         'buyer': customer_id,
         'status': "Pending",
         'shipping_address': collect["shipping_address"],
         'store': store.id,
         'total_price': total_price
      }

      order_serializer = OrderSerializer(data=order_data)

      if order_serializer.is_valid():
         order = order_serializer.save()
         return order
      else:
         logging.error("Order not valid")
         print(order_serializer.errors)
         raise serializers.ValidationError("Invalid order data")


   def create_order_items(self, order, products, store):
      total_price = Decimal('0.00')
      for product_data in products:
         product = self.get_product(product_data["product"])
         wholesale_price = self.get_wholesale_price(product_data["product"], product_data["variant"])
         retail_price = self.get_retail_price(store, product_data["variant"])

         price = None  # Initialize price outside the if block

         if retail_price:
               price = wholesale_price + retail_price

         if price is not None:
               item_total_price = Decimal(price) * Decimal(product_data["quantity"])
               total_price += item_total_price

               OrderItems.objects.create(
                  order=order,
                  product=product,
                  quantity=product_data["quantity"],
               )
               # Increment the sales count of the associated product
               product.sales_count += product_data['quantity']
               product.save()
         else:
               # Handle the case where the price is not available for the product
               logging.error("Price not available for product with id: {}".format(product.id))

      # Set the total_price attribute of the order before saving
      order.total_price = total_price
      order.save()

      return total_price

   def get_product(self, product_sn):
      return get_object_or_404(Product, id=product_sn)


   def get_wholesale_price(self, product_id, variant_id):
      try:
         variant = ProductVariant.objects.get(product=product_id, id=variant_id)
         logging.info(variant.wholesale_price)
         return variant.wholesale_price
      except ProductVariant.DoesNotExist:
         logging.error("No Product Variant")
         return None


   def get_retail_price(self, store, variant_id):
      try:
         store_variant = StoreProductVariant.objects.get(store=store, product_variant=variant_id)
         return store_variant.retail_price
      except StoreProductVariant.DoesNotExist:
         logging.error("No Store Variant")
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