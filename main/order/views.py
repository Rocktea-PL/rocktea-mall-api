
from .models import (
   OrderItems, 
   Store, 
   CustomUser, 
   Cart, 
   CartItem, 
   StoreOrder, 
   OrderDeliveryConfirmation,
   AssignOrder,
   PaymentHistory
   )

from mall.models import (
   Product, 
   ProductVariant, 
   CustomUser, 
   StoreProductPricing
   )

from .serializers import (
   OrderItemsSerializer, 
   CartSerializer, 
   CartItemSerializer, 
   OrderSerializer, 
   OrderDeliverySerializer,
   AssignedOrderSerializer,
   PaymentHistorySerializers
   )

from django.http import Http404, JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers, status
import logging
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from workshop.processor import DomainNameHandler
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from mall.payments.verify_payment import verify_payment_paystack, initiate_payment
from django.views.decorators.csrf import csrf_exempt
# from workshop.decorators import store_domain_required


handler = DomainNameHandler()

def get_store_domain(request):
   return request.META.get("HTTP_ORIGIN", None)

@csrf_exempt
def paystack_webhook(request):
   if request.method == 'POST':
      payload = json.loads(request.body)
      event = payload.get('event')
      
      if event == 'charge.success':
         data = payload.get('data')
         transaction_id = data.get('reference')
         total_price = data.get('amount') / 100  # Paystack sends amount in kobo
         email = data.get('email')
         user_id = data.get('metadata').get('user_id')
         store_id = data.get('metadata').get('store_id')
         
         # Get user and cart
         user = get_object_or_404(User, id=user_id)
         try:
               cart = Cart.objects.get(user=user)
         except Cart.DoesNotExist:
               return JsonResponse({"error": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND)
         
         verified_store = get_object_or_404(Store, id=store_id)
         
         # Create order
         order_data = {
               'buyer': user.id,
               'store': cart.store.id,
               'total_price': total_price,
               'status': 'Completed',
         }
         order_serializer = OrderSerializer(data=order_data)
         if order_serializer.is_valid():
            order = order_serializer.save()
            for cart_item in cart.items.all():
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
                  return JsonResponse(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Clear the user's cart after a successful checkout
            cart.items.all().delete()
            
            # Update webhook status to success
            PaystackWebhook.objects.filter(reference=transaction_id).update(
               data=data,
               status='Success'
            )
            return JsonResponse(order_serializer.data, status=status.HTTP_201_CREATED)
         else:
            return JsonResponse(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      else:
         return JsonResponse({"error": "Unhandled event type"}, status=status.HTTP_400_BAD_REQUEST)
   return JsonResponse({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class OrderPagination(PageNumberPagination):
   page_size = 5
   page_size_query_param = 'page_size'
   max_page_size = 1000


class OrderItemsViewSet(ModelViewSet):
   queryset = OrderItems.objects.all()
   serializer_class = OrderItemsSerializer


class CartViewSet(viewsets.ViewSet):
   # authentication_classes = [TokenAuthentication]
   renderer_classes = [JSONRenderer,]
   permission_classes = [IsAuthenticated]

   def create(self, request):
      user = request.user
      store_domain = handler.process_request(store_domain=get_store_domain(request))
      
      verified_store = get_object_or_404(Store, id=store_domain)
      products = request.data.get('products', [])

      if not products:
         return Response({"error": "Products are required."}, status=status.HTTP_400_BAD_REQUEST)

      # Check if the user already has a cart
      cart = Cart.objects.filter(user=user, store=verified_store).first()
      if not cart:
         # Get the Store instance using the store_id

         # Create a new cart if the user doesn't have a cart
         cart = Cart.objects.create(user=user, store=verified_store)
         
      for product in products:
         product_id = product.get('id')
         quantity = int(product.get('quantity', 1))
         product_variant_id = product.get('variant')
         product_price = product.get('price')

         if not product_id or not product_variant_id or not product_price:
               return JsonResponse({"error": "Product ID is required"}, status=400)

         # Check if the same product variant is already in the cart
         existing_item = cart.items.filter(
               product_id=product_id, product_variant_id=product_variant_id).first()

         if existing_item:
               # If the product variant is already in the cart, update the quantity
               existing_item.quantity += quantity
               existing_item.price += Decimal(str(product_price))
               existing_item.save()
         else:
               # Otherwise, create a new CartItem for the product variant
               product_variant = get_object_or_404(
                  ProductVariant, id=product_variant_id)
               cart_item = CartItem.objects.create(
                  cart=cart, product_variant=product_variant, price=product_price, product_id=product_id, quantity=quantity)

      serializer = CartSerializer(cart)
      return Response(serializer.data, status=status.HTTP_201_CREATED)
      
      
   def list(self, request):
      user = request.user
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
   permission_classes = [IsAuthenticated]

class InitiatePayment(viewsets.ViewSet):
   permission_classes = [IsAuthenticated]

   def create(self, request):
      email = request.data.get("email")
      amount = request.data.get("amount")
      store_domain = get_store_domain(request)
      user_id = request.user.id

      if not email or not amount:
         return Response({"error": "Email and amount are required"}, status=status.HTTP_400_BAD_REQUEST)

      try:
         store_id = handler.process_request(store_domain=store_domain)
      except ValueError as e:
         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

      # Initiate payment
      payment_response = initiate_payment(email, amount, store_id, user_id)

      if payment_response.get('status') == True:
         payment_url = payment_response['data']
         return Response({"data": payment_url}, status=status.HTTP_201_CREATED)
      else:
         error_message = payment_response.get('message', 'Payment initialization failed')
         return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

# Checkout Cart and Delete Cart
class CheckOutCart(viewsets.ViewSet):
   renderer_classes = [JSONRenderer,]
   permission_classes = [IsAuthenticated]

   def create(self, request):
      # Collect Data
      user = request.user
      store_id = handler.process_request(store_domain=get_store_domain(request))
      total_price = request.data.get("total_price")
      transaction_id = request.data.get("transaction_id")

      # Validate that required fields are present
      if not (store_id and total_price):
         return JsonResponse({"error": "Missing required fields in the request"}, status=400)

      # Get Cart belonging to user
      try:
         cart = Cart.objects.get(user=user)
      except Cart.DoesNotExist:
         return Response({"detail": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND)

      verified_store = get_object_or_404(Store, id=store_id)

      payment_response = verify_payment_paystack(transaction_id)
      if payment_response.data['status'] != True:
               return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

      order_data = {
         'buyer': user.id,
         'store': cart.store.id,
         'total_price': total_price,
         'status': 'Completed',
      }
      order_serializer = OrderSerializer(data=order_data)

      if order_serializer.is_valid():
         order = order_serializer.save()
         total_profit = 0

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
                  # Calculate profit
                  # retail_price = self.get_store_pricing(cart_item.product.id, verified_store)
                  # wholesale_price = cart_item.product_variant.wholesale_price
                  # profit_per_item = retail_price - wholesale_price
                  # total_profit += profit_per_item * cart_item.quantity
               else:
                  # Handle the case where an order item cannot be created
                  logging.error("Order Item ERROR")
                  return Response(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
         
         # Update store's wallet
         # verified_store.balance += total_profit
         # verified_store.save()
         # CClear the user's cart after a successful checkout
         cart.items.all().delete()

         return Response(order_serializer.data, status=status.HTTP_201_CREATED)
      else:
         logging.error("Order ERROR")
         return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   def get_store_pricing(self, product_id, store):
      try:
         store_product = StoreProductPricing.objects.get(product_id=product_id, store=store)
      except StoreProductPricing.DoesNotExist:
         return 0  # Handle the case when pricing information is not available

      return store_product.retail_price

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


class CustomPagination(PageNumberPagination):
   page_size = 10  # Set the number of items per page
   page_size_query_param = 'page_size'
   max_page_size = 1000


class AllOrders(viewsets.ModelViewSet):
   serializer_class = OrderSerializer
   pagination_class = CustomPagination

   def get_queryset(self):
      queryset = StoreOrder.objects.all().select_related("buyer", "store").order_by("-created_at")
      return queryset


class OrderDeliverView(viewsets.ModelViewSet):
   queryset = OrderDeliveryConfirmation.objects.all()
   serializer_class = OrderDeliverySerializer
   pagination_class = OrderPagination


class AssignedOrders(generics.ListAPIView):
   serializer_class = AssignedOrderSerializer
   pagination_class = CustomPagination

   def list(self, request, **kwargs):
      rider_id = kwargs.get("rider")  # Replace with the actual rider's ID

      # Assuming you have an instance of the CustomUser model for the given rider_id
      rider_user = CustomUser.objects.get(id=rider_id)

      # Query AssignOrder to get all orders associated with the rider
      assigned_orders = AssignOrder.objects.filter(rider=rider_user)

      # Now, you can access the related StoreOrder instances
      all_orders_for_rider = StoreOrder.objects.filter(
         assignorder__in=assigned_orders).order_by('-created_at')

      serializer = self.get_serializer(all_orders_for_rider, many=True)
      return Response({"orders": serializer.data}, status=status.HTTP_200_OK)


class PaymentHistoryView(viewsets.ModelViewSet):
   queryset = PaymentHistory.objects.select_related('store', 'order')
   serializer_class = PaymentHistorySerializers
   permission_classes = [IsAuthenticated]
   
   def get_queryset(self):
      store_id = handler.process_request(store_domain=get_store_domain(self.request))
      
      verified_store = get_object_or_404(Store, id=store_id)
      
      try:
         queryset = PaymentHistory.objects.filter(store=verified_store).order_by("payment_date")
         return queryset
      except PaymentHistory.DoesNotExist:
         return PaymentHistory.objects.none()
      