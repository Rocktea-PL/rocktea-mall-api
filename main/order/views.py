from order.classes.order_processor import OrderProcessor
from order.classes.webhook_processor import WebhookProcessor
from order.classes.cache_helpers import CacheHelper
from .models import (
   OrderItems, 
   Store, 
   Cart, 
   CartItem, 
   StoreOrder, 
   OrderDeliveryConfirmation,
   AssignOrder,
   PaymentHistory,
   PaystackWebhook
   )

from mall.models import (
   Notification,
   Product, 
   ProductVariant, 
   CustomUser, 
   StoreProductPricing,
   Wallet
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
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from mall.payments.verify_payment import (
   verify_payment_paystack, 
   initiate_payment, 
   get_bank_list_paystack, 
   get_account_name_paystack,
   get_receipient_code_transfer_paystack,
   initiate_transfer_paystack,
   otp_transfer_paystack
)
from django.views.decorators.csrf import csrf_exempt
import json
from .shipbubble_service import ShipbubbleService
from rest_framework.decorators import action
from django.core.cache import cache
from urllib.parse import urlparse
from .classes.services import PaystackService
from django.utils.decorators import method_decorator
from .pagination import CustomPagination

import hmac
import hashlib
from django.conf import settings
# from workshop.decorators import store_domain_required

# Get an instance of a logger
logger = logging.getLogger(__name__)

secret = settings.TEST_SECRET_KEY
handler = DomainNameHandler()

def get_store_domain(request):
   return request.META.get("HTTP_ORIGIN", None)

""" @csrf_exempt
def paystack_webhook(request):
   if request.method == 'POST':
      payload = request.body
      sig_header = request.headers.get('x-paystack-signature')
      body = None
      event = None

      if not sig_header:
         logger.error("Missing signature header")
         return JsonResponse({"error": "Missing signature header"}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
         hash = hmac.new(secret.encode('utf-8'), payload, digestmod=hashlib.sha512).hexdigest()
         if hash == sig_header:
            body_unicode   = payload.decode('utf-8')
            body           = json.loads(body_unicode)
            event          = body['event']
         else:
            raise Exception("Invalid signature")
      except ValueError as e:
         logger.error(f"Failed to decode JSON payload: {e}")
         return JsonResponse({"error": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)
      except KeyError as e:
         logger.error(f"Missing key in payload: {e}")
         return JsonResponse({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
      except Exception as e:
         logger.error(f"Signature verification failed: {e}")
         return JsonResponse({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
      
      if event == 'charge.success':
         data           = body["data"]
         transaction_id = data.get('reference')
         total_price    = data.get('amount') / 100 
         email          = data.get('email')
         metadata       = data.get('metadata', {})

         logger.debug(f"Metadata from webhook: {metadata}")

         paystack_webhook = PaystackWebhook.objects.filter(reference=transaction_id).first()
         if not paystack_webhook:
            return JsonResponse({"error": "Transaction reference not found"}, status=status.HTTP_404_NOT_FOUND)
         
         purpose = metadata.get('purpose')
         logger.info(f"Paystack Webhook Received: Event: {event}, Purpose: {purpose}, Reference: {transaction_id}")
         if purpose == 'order':
            user_id = metadata.get('user_id')
            if not user_id:
               return JsonResponse({"error": "User ID not found in metadata"}, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(CustomUser, id=user_id)
            try:
               cart = Cart.objects.get(user=user)
            except Cart.DoesNotExist:
               CacheHelper.clear_user_cache(user_id)
               return JsonResponse({"error": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND)

            verified_store = get_object_or_404(Store, id=cart.store.id)
            logger.info(f"Verified Store: {verified_store}")

            order_data = {
               'buyer':       user.id,
               'store':       cart.store.id,
               'total_price': total_price,
               'status':      'Completed',
            }
            logger.info(f"Order Data: {order_data}")
            order_serializer = OrderSerializer(data=order_data)
            if order_serializer.is_valid():
               order = order_serializer.save()

               # Process cart items
               for cart_item in cart.items.all():
                  # Increment sales_count for the product
                  product = cart_item.product
                  product.sales_count += cart_item.quantity
                  product.save()

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
                     CacheHelper.clear_user_cache(user_id)
                     return JsonResponse(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

               cart.items.all().delete()

               # PaystackWebhook.objects.filter(reference=transaction_id).update(
               #    data=data,
               #    store_id=order_data['store'],
               #    status='Success',
               #    order=order  # Associate the order with the webhook
               # )

               paystack_webhook.store_id = order_data['store']
               paystack_webhook.data = data
               paystack_webhook.status = 'Success'
               paystack_webhook.order = order
               paystack_webhook.save()

               shipment_feedback = cache.get(f'shipment_{user_id}')
               logger.info(f"Shipment details from cache: {shipment_feedback}")

               if shipment_feedback:
                  try:
                     shipment_data = json.loads(shipment_feedback)
                     order.tracking_id = shipment_data['data']['order_id']
                     order.tracking_url = shipment_data['data']['tracking_url']
                     order.tracking_status = shipment_data['data']['status']
                     order.delivery_location = shipment_data['data']['ship_to']['address']
                     order.shipping_fee = shipment_data['data']['payment']['shipping_fee']
                     order.save()
                     cache.delete(f'shipment_{user_id}')
                  except json.JSONDecodeError as e:
                     logger.error(f"Failed to decode shipment feedback from cache: {e}")
                     CacheHelper.clear_user_cache(user_id)
                     return JsonResponse({"error": "Invalid shipment feedback format"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

               return JsonResponse(order_serializer.data, status=status.HTTP_201_CREATED)
            else:
               CacheHelper.clear_user_cache(user_id)
               return JsonResponse(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
         else:
            logger.info("Processing dropshipping payment")
            # Handle store payment
            user = get_object_or_404(CustomUser, email=email)
            store = get_object_or_404(Store, owner=user)
            
            store.has_made_payment = True
            store.save()
            paystack_webhook.data = data
            paystack_webhook.status = 'Success'
            paystack_webhook.store_id = store.id
            paystack_webhook.save()

            logger.info(f"Dropshipping payment processed successfully for store {store.name} (ID: {store.id})")
            
            return JsonResponse({"message": "Store payment processed successfully"}, status=status.HTTP_200_OK)
      else:
         logger.warning(f"Unhandled payment purpose: {purpose}")
         return JsonResponse({"error": "Unhandled event type"}, status=status.HTTP_400_BAD_REQUEST)
   return JsonResponse({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED) """

@csrf_exempt
def paystack_webhook(request):
   if request.method == 'POST':
      payload = request.body
      sig_header = request.headers.get('x-paystack-signature')
      body = None
      event = None

      if not sig_header:
         logger.error("Missing signature header")
         return JsonResponse({"error": "Missing signature header"}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
         hash = hmac.new(secret.encode('utf-8'), payload, digestmod=hashlib.sha512).hexdigest()
         if hash == sig_header:
               body_unicode = payload.decode('utf-8')
               body = json.loads(body_unicode)
               event = body['event']
         else:
               raise Exception("Invalid signature")
      except ValueError as e:
         logger.error(f"Failed to decode JSON payload: {e}")
         return JsonResponse({"error": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)
      except KeyError as e:
         logger.error(f"Missing key in payload: {e}")
         return JsonResponse({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
      except Exception as e:
         logger.error(f"Signature verification failed: {e}")
         return JsonResponse({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

      if event == 'charge.success':
         data = body["data"]
         transaction_id = data.get('reference')
         total_price = data.get('amount') / 100 
         email = data.get('email')
         metadata = data.get('metadata', {})
         purpose = metadata.get('purpose')

         # Log the incoming webhook data for debugging
         logger.info(f"Data: {data}")
         logger.info(f"Processing webhook for purpose: {purpose}")
         logger.info(f"Transaction ID: {transaction_id}")
         logger.info(f"Email: {email}")
         logger.info(f"Metadata: {metadata}")

         try:
               paystack_webhook = PaystackWebhook.objects.get(reference=transaction_id)
         except PaystackWebhook.DoesNotExist:
               logger.error(f"Transaction reference not found: {transaction_id}")
               return JsonResponse({"error": "Transaction reference not found"}, status=status.HTTP_404_NOT_FOUND)
         
         if purpose == 'order':
               return handle_order_payment(data, paystack_webhook, total_price, metadata)
         elif purpose == 'dropshipping_payment':
               return handle_dropshipping_payment(data, paystack_webhook, email)
         else:
               logger.error(f"Unknown payment purpose: {purpose}")
               return JsonResponse({"error": "Unknown payment purpose"}, status=status.HTTP_400_BAD_REQUEST)
      else:
         logger.warning(f"Unhandled event type: {event}")
         return JsonResponse({"error": "Unhandled event type"}, status=status.HTTP_400_BAD_REQUEST)
   return JsonResponse({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

def handle_order_payment(data, paystack_webhook, total_price, metadata):
   """Handle order payment processing"""
   user_id = metadata.get('user_id')
   if not user_id:
      logger.error("User ID not found in metadata for order payment")
      return JsonResponse({"error": "User ID not found in metadata"}, status=status.HTTP_400_BAD_REQUEST)

   try:
      user = CustomUser.objects.get(id=user_id)
      cart = Cart.objects.get(user=user)
      verified_store = Store.objects.get(id=cart.store.id)
      
      logger.info(f"Processing order for user: {user.email}, store: {verified_store.name}")

      order_data = {
         'buyer': user.id,
         'store': cart.store.id,
         'total_price': total_price,
         'status': 'Completed',
      }
      
      order_serializer = OrderSerializer(data=order_data)
      if not order_serializer.is_valid():
         CacheHelper.clear_user_cache(user_id)
         logger.error(f"Order validation failed: {order_serializer.errors}")
         return JsonResponse(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
      order = order_serializer.save()

      # Process cart items
      for cart_item in cart.items.all():
         product = cart_item.product
         product.sales_count += cart_item.quantity
         product.save()

         order_item_data = {
               'userorder': order.id,
               'product': cart_item.product.id,
               'product_variant': cart_item.product_variant.id,
               'quantity': cart_item.quantity
         }
         
         order_item_serializer = OrderItemsSerializer(data=order_item_data)
         if not order_item_serializer.is_valid():
               CacheHelper.clear_user_cache(user_id)
               logger.error(f"Order item validation failed: {order_item_serializer.errors}")
               return JsonResponse(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
         order_item_serializer.save()

      cart.items.all().delete()

      # Update webhook record
      paystack_webhook.store_id = order_data['store']
      paystack_webhook.data = data
      paystack_webhook.status = 'Success'
      paystack_webhook.order = order
      paystack_webhook.save()

      # Process shipment if available
      process_shipment_details(user_id, order)

      return JsonResponse(order_serializer.data, status=status.HTTP_201_CREATED)

   except Exception as e:
      logger.error(f"Error processing order payment: {str(e)}", exc_info=True)
      CacheHelper.clear_user_cache(user_id)
      return JsonResponse({"error": "Error processing order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def handle_dropshipping_payment(data, paystack_webhook, email):
   """Handle dropshipping payment processing"""
   try:
      logger.info(f"Processing dropshipping payment for email: {email}")
      
      user = CustomUser.objects.get(email=email)
      store = Store.objects.get(owner=user)
      
      logger.info(f"Found store: {store.name} for user: {user.email}")

      store.has_made_payment = True
      store.completed = True
      store.save()
      
      paystack_webhook.data = data
      paystack_webhook.status = 'Success'
      paystack_webhook.store_id = store.id
      paystack_webhook.save()
      
      logger.info("Dropshipping payment processed successfully")
      return JsonResponse({
         "message": "Dropshipping payment processed successfully",
         "store_id": store.id,
         "store_name": store.name
      }, status=status.HTTP_200_OK)
      
   except CustomUser.DoesNotExist:
      logger.error(f"User not found with email: {email}")
      return JsonResponse({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
   except Store.DoesNotExist:
      logger.error(f"Store not found for user: {email}")
      return JsonResponse({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
   except Exception as e:
      logger.error(f"Error processing dropshipping payment: {str(e)}", exc_info=True)
      return JsonResponse({"error": "Error processing dropshipping payment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def process_shipment_details(user_id, order):
   """Process shipment details from cache if available"""
   shipment_feedback = cache.get(f'shipment_{user_id}')
   if shipment_feedback:
      try:
         shipment_data = json.loads(shipment_feedback)
         order.tracking_id = shipment_data['data']['order_id']
         order.tracking_url = shipment_data['data']['tracking_url']
         order.tracking_status = shipment_data['data']['status']
         order.delivery_location = shipment_data['data']['ship_to']['address']
         order.shipping_fee = shipment_data['data']['payment']['shipping_fee']
         order.save()
         cache.delete(f'shipment_{user_id}')
         logger.info(f"Shipment details processed for order: {order.id}")
      except json.JSONDecodeError as e:
         logger.error(f"Failed to decode shipment feedback from cache: {e}")
      except KeyError as e:
         logger.error(f"Missing key in shipment data: {e}")


""" @csrf_exempt
def paystack_webhooks(request):
   "Handle Paystack webhook requests."
   try:
      if request.method != 'POST':
         return JsonResponse(
               {"error": "Invalid request method"},
               status=status.HTTP_405_METHOD_NOT_ALLOWED
         )

      signature = request.headers.get('x-paystack-signature')
      if not signature:
         logger.error("Missing Paystack signature header")
         return JsonResponse(
               {"error": "Missing signature header"},
               status=status.HTTP_400_BAD_REQUEST
         )

      # Initialize webhook processor
      processor = WebhookProcessor(request.body, signature, secret)
      
      if not processor.verify_signature():
         logger.error("Invalid Paystack signature")
         return JsonResponse(
               {"error": "Invalid signature"},
               status=status.HTTP_400_BAD_REQUEST
         )

      if not processor.parse_payload():
         logger.error("Failed to parse Paystack payload")
         return JsonResponse(
               {"error": "Invalid payload"},
               status=status.HTTP_400_BAD_REQUEST
         )

      if processor.event == 'charge.success':
         data = processor.body["data"]
         metadata = data.get('metadata', {})
         
         if metadata.get('purpose') == 'order':
               logger.info(f"Processing order payment for reference: {data.get('reference')}")
               order_processor = OrderProcessor(data, metadata, data.get('reference'))
               return order_processor.process_order()
         else:
               # Handle store payment
               logger.info(f"Processing store payment for reference: {data.get('reference')}")
               email = data.get('email')
               if not email:
                  return JsonResponse(
                     {"error": "Email not found in payload"},
                     status=status.HTTP_400_BAD_REQUEST
                  )

               try:
                  user = get_object_or_404(CustomUser, email=email)
                  store = get_object_or_404(Store, owner=user)
                  
                  with transaction.atomic():
                     store.has_made_payment = True
                     store.save()
                     
                     paystack_webhook = PaystackWebhook.objects.filter(
                           reference=data.get('reference')
                     ).first()
                     if paystack_webhook:
                           paystack_webhook.data = data
                           paystack_webhook.status = 'Success'
                           paystack_webhook.store_id = store.id
                           paystack_webhook.save()
                     
                  return JsonResponse(
                     {"message": "Store payment processed successfully"},
                     status=status.HTTP_200_OK
                  )
               except Exception as e:
                  logger.error(f"Store payment processing failed: {e}")
                  return JsonResponse(
                     {"error": "Failed to process store payment"},
                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
                  )
      
      logger.warning(f"Unhandled Paystack event type: {processor.event}")
      return JsonResponse(
         {"error": "Unhandled event type"},
         status=status.HTTP_400_BAD_REQUEST
      )
   except Exception as e:
      logger.error(f"Unexpected error in paystack webhook: {e}")
      return JsonResponse(
         {"error": "Internal server error"},
         status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
 """
class InitiatePayment(viewsets.ViewSet):
    
   def get_permissions(self):
      """Dynamically set permissions based on the purpose."""
      if self.request.data.get("purpose", "order") == "order":
         return [IsAuthenticated()]
      return [AllowAny()]

   def create(self, request):
      email = request.data.get("email")
      purpose = request.data.get("purpose", "order")
      user_id = request.user.id if request.user.is_authenticated else None

      logger.info(f"Initiating payment request with data: {request.data}")

      if not email:
         return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

      base_url = None  # Default to None unless needed
      referer = request.META.get('HTTP_REFERER')

      if purpose == "order":
         amount = request.data.get("amount")
         if not amount:
            return Response({"error": "Amount is required for order payments"}, status=status.HTTP_400_BAD_REQUEST)
         try:
            amount = float(amount)
         except ValueError:
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)

         if referer and 'swagger' not in referer.lower():
            parsed_referer = urlparse(referer)
            base_url = f"{parsed_referer.scheme}://{parsed_referer.hostname}/order_success"
         else:
            base_url = "https://rocktea-users.vercel.app/order_success"  # Default fallback
      else:
         if referer and 'swagger' not in referer.lower():
            parsed_referer = urlparse(referer)
            base_url = f"{parsed_referer.scheme}://{parsed_referer.hostname}/domain_creation"
         else:
            base_url = "https://rocktea-dropshippers.vercel.app/domain_creation"  # Default fallback
         amount = 150000  # Fixed price for dropshipper payments

      # Initiate payment
      payment_response = initiate_payment(email, amount, user_id, purpose, base_url)

      if payment_response.get("status") is True:
         payment_url = payment_response["data"]
         return Response({"data": payment_url}, status=status.HTTP_201_CREATED)
      else:
         error_message = payment_response.get("message", "Payment initialization failed")
         return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
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
      # cart = Cart.objects.filter(user=user, store=verified_store).first()
      # cart, created = Cart.objects.get_or_create(user=user, store=verified_store)
      # Get or create the cart using get_or_create instead of filter/create
      cart, created = Cart.objects.get_or_create(
         user=user,
         store=verified_store,
         defaults={'price': Decimal('0.00')}  # Add any default values here
      )
         
      for product in products:
         product_id                 = product.get('id')
         quantity                   = int(product.get('quantity', 1))
         product_variant_id         = product.get('variant')
         product_price              = product.get('price')
         product_price_from_retail  = StoreProductPricing.objects.filter(store=verified_store, product=product)

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
         logger.error("Incorrect Cart ID")
         raise serializers.ValidationError("Cart Does Not Exist")

class CartItemModifyView(viewsets.ModelViewSet):
   queryset = CartItem.objects.all()
   serializer_class = CartItemSerializer
   permission_classes = [IsAuthenticated]

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
                  logger.error("Order Item ERROR")
                  return Response(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
         
         # Update store's wallet
         # verified_store.balance += total_profit
         # verified_store.save()
         # CClear the user's cart after a successful checkout
         cart.items.all().delete()

         return Response(order_serializer.data, status=status.HTTP_201_CREATED)
      else:
         logger.error("Order ERROR")
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
   
   @action(detail=False, methods=['get'], url_path='by-reference')
   def get_order_by_reference(self, request):
      """
      Retrieve a single order using the reference ID.
      URL: /api/orders/by-reference/?reference=<reference_id>
      """
      reference = request.query_params.get('reference')

      if not reference:
         return Response([])  # Return empty list if no reference provided

      try:
         # Get the webhook and related order in a single query
         webhook = PaystackWebhook.objects.select_related('order').get(reference=reference)
         
         if not webhook.order:
               return Response([])  # Return empty list if no order found

         # Check if the order belongs to the requesting user
         if webhook.order.buyer.id != request.user.id:
               return Response([])  # Return empty list if user doesn't have permission

         # Get the specific order with all necessary related fields
         order = StoreOrder.objects.select_related(
               "buyer",
               "store"
         ).get(id=webhook.order.id)

         serializer = OrderSerializer(order)
         return Response([serializer.data])  # Return list with single order

      except (PaystackWebhook.DoesNotExist, StoreOrder.DoesNotExist):
         return Response([])  # Return empty list if no webhook or order found


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

class ShipbubbleViewSet(viewsets.ViewSet):
   permission_classes = [IsAuthenticated]

   def create(self, request): 
      shipment_data = request.data 
      shipbubble_service = ShipbubbleService() 
      user = request.user
      store_id = handler.process_request(store_domain=get_store_domain(request))

      # Get Cart belonging to user 
      try: 
         cart = Cart.objects.get(user=user, store_id=store_id) 
      except Cart.DoesNotExist: 
         return Response({"detail": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND) 
      
      # Prepare package items from cart 
      package_items = [] 
      cart_items = CartItem.objects.filter(cart=cart) 
      
      if not cart_items: 
         return JsonResponse({"error": "No items in the cart"}, status=400) 

      for cart_item in cart_items:

         try: 
            pricing = StoreProductPricing.objects.get(product=cart_item.product, store=store_id) 
            retail_price = float(pricing.retail_price) 
         except StoreProductPricing.DoesNotExist: 
            return JsonResponse({"error": f"Pricing not found for product {cart_item.product.name}"}, status=400)
         
         # Ensure description is not None 
         description = cart_item.product.description if cart_item.product.description else f"{cart_item.product.name} item purchased"

         package_items.append({ 
            "name": cart_item.product.name, 
            "description": description, 
            "unit_weight": 1, 
            # "unit_amount": cart_item.product_variant.wholesale_price,
            "unit_amount": retail_price,
            "quantity": cart_item.quantity
         })

      response = shipbubble_service.process_shipping(shipment_data, package_items)
      # response = shipbubble_service.validate_address(shipment_data)
      return JsonResponse(response)
   
   @action(detail=False, methods=['get'], url_path='available-carriers')
   def available_carriers(self, request):
      shipbubble_service = ShipbubbleService()
      response = shipbubble_service.get_available_carrirers()
      return JsonResponse(response)
   
   @action(detail=False, methods=['get'], url_path='label-categories')
   def label_categories(self, request):
      shipbubble_service = ShipbubbleService()
      response = shipbubble_service.get_label_categories()
      return JsonResponse(response)
   
   @action(detail=False, methods=['post'], url_path='shipment-label')
   def create_shipment_label(self, request):
      shipbubble_service = ShipbubbleService()
      shipment_data = request.data
      user_id = request.user.id

      # Validate required fields 
      required_fields = ['request_token', 'service_code' ]
      missing_fields = [field for field in required_fields if field not in shipment_data] 
      if missing_fields: 
         return JsonResponse({'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)

      response = shipbubble_service.create_shipment(shipment_data, user_id)
      return JsonResponse(response)
   
   @action(detail=False, methods=['get'], url_path='track-shipment-label')
   def track_shipment_label(self, request):
      shipbubble_service = ShipbubbleService()
      order_ids = "SB-775B0DFAAADA"

      response = shipbubble_service.track_shipping_status(order_ids)
      return JsonResponse(response)

class Paystack(viewsets.ViewSet):
   permission_classes = [IsAuthenticated]
   
   @action(detail=False, methods=['get'], url_path='get-banks-list')
   def get_bank_list(self, request):
      bank_list = get_bank_list_paystack()

      return JsonResponse(bank_list)
   
   @action(detail=False, methods=['post'], url_path='get-account-name')
   def get_account_name(self, request):
      account_number = request.data.get('account_number') 
      bank_code      = request.data.get('bank_code')

      # Validation
      if not account_number or not bank_code:
         return JsonResponse(
               {"error": "Both 'account_number' and 'bank_code' are required."}, 
               status=400
         )

      bank_details   = get_account_name_paystack(account_number, bank_code)

      return JsonResponse(bank_details)
   
   @action(detail=False, methods=['post'], url_path='get-transfer-recipient')
   def get_receipient_code(self, request):
      data = request.data
      import pdb
      pdb.set_trace()

      required_fields = ['name', 'account_number', 'bank_code']
      missing_fields = [field for field in required_fields if field not in request.data]

      # Validation
      if missing_fields:
         return JsonResponse(
               {"error": f"Missing required fields: {', '.join(missing_fields)}."},
               status=400
         )

      transfer_recipient   = get_receipient_code_transfer_paystack(data)

      return JsonResponse(transfer_recipient)
   
   @action(detail=False, methods=['post'], url_path='initiate-transfer')
   def initiate_transfer(self, request):
      data = request.data

      required_fields = ['amount', 'recipient_code']
      missing_fields = [field for field in required_fields if field not in request.data]

      # Validation
      if missing_fields:
         return JsonResponse(
               {"error": f"Missing required fields: {', '.join(missing_fields)}."},
               status=400
         )

      initialize_transfer   = initiate_transfer_paystack(data)

      return JsonResponse(initialize_transfer)
   
   @action(detail=False, methods=['post'], url_path='otp-transfer')
   def otp_with_transfer(self, request):
      data = request.data

      required_fields = ['otp', 'transfer_code']
      missing_fields = [field for field in required_fields if field not in request.data]

      # Validation
      if missing_fields:
         return JsonResponse(
               {"error": f"Missing required fields: {', '.join(missing_fields)}."},
               status=400
         )

      otp_transfer   = otp_transfer_paystack(data)

      return JsonResponse(otp_transfer)
   
   @action(detail=False, methods=['post'], url_path='process-withdrawal')
   @transaction.atomic  # Ensures atomicity
   def process_withdrawal(self, request):
      amount = request.data.get('amount')

      # Validate amount
      if not amount or not isinstance(amount, (int, float)):
         return JsonResponse({"error": "Invalid or missing 'amount'."}, status=400)
      
      if amount < 1000:
         return JsonResponse({"error": "Amount must be at least 1000."}, status=400)

      # Fetch user's wallet
      wallet = Wallet.objects.filter(store__owner_id=request.user.id).first()

      if not wallet:
         return JsonResponse({"error": "Wallet not found."}, status=404)
      
      if float(wallet.balance) < amount:
         return JsonResponse({"error": "Insufficient balance."}, status=400)
      
      # Get account details
      account_number = wallet.nuban
      bank_code = wallet.bank_code
      if not account_number or not bank_code:
         return JsonResponse({"error": "Bank details not found."}, status=400)
      
      # Step 1: Get transfer recipient code
      recipient_data = {
         "name": wallet.account_name,
         "account_number": account_number,
         "bank_code": bank_code
      }

      recipient_response = get_receipient_code_transfer_paystack(recipient_data)
      if recipient_response.get("status") != True:
         return JsonResponse(
               {"error": "Failed to create transfer recipient.", "details": recipient_response},
               status=400
         )
      recipient_code = recipient_response.get("data", {}).get("recipient_code")

      # Step 2: Initiate transfer
      transfer_data = {
         "amount": amount,
         "recipient_code": recipient_code
      }
      transfer_response = initiate_transfer_paystack(transfer_data)
      if transfer_response.get("status") != True:
         return JsonResponse(
               {"error": "Failed to initiate transfer.", "details": transfer_response},
               status=400
         )

      # Step 3: Deduct amount from wallet
      wallet.balance = str(float(wallet.balance) - amount)
      wallet.save()

      # Create Notification
      notification_message = f"Your withdrawal of {amount} has been successfully processed."
      store = get_object_or_404(Store, id=wallet.store.id)
      
      Notification.objects.create(store=store, message=notification_message)

      return JsonResponse(
         {"message": "Withdrawal successful.", "transaction": transfer_response},
         status=200
      )