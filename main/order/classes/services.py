import json
import logging
import hashlib
import hmac
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from order.models import CustomUser, Store, Cart
from order.serializers import OrderSerializer, OrderItemsSerializer
from order.classes.cache_helpers import CacheHelper

class PaystackService:
    @staticmethod
    def verify_signature(payload, sig_header):
        """Verify Paystack signature"""
        if not sig_header:
            logging.error("Missing signature header")
            return None, Response({"error": "Missing signature header"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            secret = settings.PAYSTACK_SECRET_KEY
            hash_signature = hmac.new(secret.encode('utf-8'), payload, digestmod=hashlib.sha512).hexdigest()
            if hash_signature != sig_header:
                raise Exception("Invalid signature")
            return json.loads(payload.decode('utf-8')), None
        except (ValueError, KeyError, Exception) as e:
            logging.error(f"Signature verification failed: {e}")
            return None, Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_order_payment(data, metadata):
        """Handles order payment processing"""
        user_id = metadata.get('user_id')
        if not user_id:
            return Response({"error": "User ID not found in metadata"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, id=user_id)

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            CacheHelper.clear_user_cache(user_id)
            return Response({"error": "User does not have a cart"}, status=status.HTTP_404_NOT_FOUND)

        order_data = {
            'buyer': user.id,
            'store': cart.store.id,
            'total_price': data.get('amount') / 100,  # Paystack sends amount in kobo
            'status': 'Completed',
        }

        order_serializer = OrderSerializer(data=order_data)
        if order_serializer.is_valid():
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
                if order_item_serializer.is_valid():
                    order_item_serializer.save()
                else:
                    CacheHelper.clear_user_cache(user_id)
                    return Response(order_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            cart.items.all().delete()
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        else:
            CacheHelper.clear_user_cache(user_id)
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_store_payment(data, email):
        """Handles store payment processing"""
        user = get_object_or_404(CustomUser, email=email)
        store = get_object_or_404(Store, owner=user)

        store.has_made_payment = True
        store.save()

        return Response({"message": "Store payment processed successfully"}, status=status.HTTP_200_OK)
