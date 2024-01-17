from django.http import Http404, JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import OrderItems, Store, CustomUser, Cart, CartItem, StoreOrder
from mall.models import Product, ProductVariant, CustomUser, StoreProductPricing
from .serializers import OrderItemsSerializer, CartSerializer, CartItemSerializer, OrderSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers, status
import logging
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets

class OrderItemsViewSet(ModelViewSet):
   queryset = OrderItems.objects.all()
   serializer_class = OrderItemsSerializer

      
      
class CartViewSet(viewsets.ViewSet):
   # authentication_classes = [TokenAuthentication]
   renderer_classes = [JSONRenderer,]

   def create(self, request):
      user = request.user
      # store_id = request.data.get("store")
      products = request.data.get('products', [])

      # Check if the user already has a cart
      cart = Cart.objects.filter(user=user).first()
      if not cart:
         # Get the Store instance using the store_id
         store = request.user.associated_domain

         # Create a new cart if the user doesn't have a cart
         cart = Cart.objects.create(user=user, store=store)
      for product in products:
         product_id = product.get('id')
         quantity = product.get('quantity', 1)
         product_variant_id = product.get('variant')
         product_price = product.get('price')

         if product_id is None:
               return JsonResponse({"error": "Product ID is required"}, status=400)

         # Check if the same product variant is already in the cart
         existing_item = cart.items.filter(
               product_id=product_id, product_variant_id=product_variant_id).first()

         if existing_item:
               # If the product variant is already in the cart, update the quantity
               existing_item.quantity += quantity
               existing_item.price = product_price
               existing_item.save()
         else:
               # Otherwise, create a new CartItem for the product variant
               product_variant = get_object_or_404(
                  ProductVariant, id=product_variant_id)
               cart_item = CartItem.objects.create(
                  cart=cart, product_variant=product_variant, price=product_price, product_id=product_id, quantity=quantity)

      serializer = CartSerializer(cart)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
   
   # def calc_product_price(self, product, store, variant):
   #    # Get Product
   #    product = get_object_or_404(Product, id=product)
      
   #    # Get Product Variant for that product
      
      
   def list(self, request):
      user = self.request.user.id
      queryset = Cart.objects.filter(user=user).select_related("user", "store")
      serializer = CartSerializer(queryset, many=True)
      return Response(serializer.data) 

   def delete(self, request):
      cart_id = self.request.query_params.get("id")
      try:
         # Get the specific cart instance based on the provided ID
         cart = get_object_or_404(Cart, id=cart_id)
         # Delete the cart instance
         cart.delete()
         return Response({"detail": "Cart deleted successfully"})
      except Cart.DoesNotExist:
         logging.error("Incorrect Cart ID")
         raise serializers.ValidationError("Cart Does Not Exist")


class CartItemModifyView(viewsets.ModelViewSet):
   queryset = CartItem.objects.all()
   serializer_class = CartItemSerializer


# Checkout Cart and Delete Cart
class CheckOutCart(viewsets.ViewSet):
   renderer_classes = [JSONRenderer,]
   def create(self, request):
      # Collect Data
      user = request.user
      store_id = request.data.get("store")
      total_price = request.data.get("total_price")

      # Validate that required fields are present
      if not (store_id and total_price):
         return JsonResponse({"error": "Missing required fields in the request"}, status=400)

      # Get Cart belonging to user
      try:
         cart = Cart.objects.get(user=user)
      except Cart.DoesNotExist:
         return Response({"detail": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND)

      verified_store = get_object_or_404(Store, id=store_id)

      order_data = {
         'buyer': user.id,
         'store': cart.store.id,
         'total_price': total_price,
         'status': 'Pending',
      }
      order_serializer = OrderSerializer(data=order_data)

      if order_serializer.is_valid():
         order = order_serializer.save()

         for cart_item in cart.items.all():
            # print(cart_item)
               order_item_data = {
                  'userorder': order.id,
                  'product': cart_item.product.id,
                  'product_variant': cart_item.product_variant.id,
                  'quantity': cart_item.quantity
               }

               order_item_serializer = OrderItemsSerializer(data=order_item_data)

               if order_item_serializer.is_valid():
                  order_item_serializer.save()
               else:
                  # Handle the case where an order item cannot be created
                  logging.error("Order Item ERROR")
                  return Response(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

         # Clear the user's cart after a successful checkout
         cart.items.all().delete()

         return Response(order_serializer.data, status=status.HTTP_201_CREATED)
      else:
         logging.error("Order ERROR")
         return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   # Move cart items to order items
   def list(self, request):
      # Collect Data
      user = request.user.id

      # Get user's orders
      orders = StoreOrder.objects.filter(buyer=user)

      # Serialize the order items from all orders
      order_items = OrderItems.objects.filter(userorder__in=orders)
      order_items_serializer = OrderItemsSerializer(order_items, many=True)

      return Response(order_items_serializer.data, status=status.HTTP_200_OK)


class ViewOrders(viewsets.ViewSet):
   def list(self, request):
      user = self.request.user.id
      queryset = StoreOrder.objects.filter(buyer=user).select_related("buyer", "store")
      serializer = OrderSerializer(queryset, many=True)
      return Response(serializer.data)
