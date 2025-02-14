from typing import Dict, Any
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db import transaction
import json
import logging
from rest_framework import status

from main.mall.models import Cart, CustomUser
from main.order.models import PaystackWebhook, StoreOrder
from main.order.serializers import OrderItemsSerializer, OrderSerializer

def clear_user_cache(user_id: int) -> None:
    """Clear user-specific cache entries."""
    cache.delete(f'shipment_{user_id}')

class OrderProcessor:
    """Process Paystack order payments and create orders."""

    def __init__(self, data: Dict[str, Any], metadata: Dict[str, Any], transaction_id: str):
        """
        Initialize the order processor.
        
        Args:
            data (Dict[str, Any]): Payment data from Paystack
            metadata (Dict[str, Any]): Payment metadata
            transaction_id (str): Unique transaction reference
        """
        self.data = data
        self.metadata = metadata
        self.transaction_id = transaction_id
        self.total_price = data.get('amount', 0) / 100

    def process_order(self) -> JsonResponse:
        """
        Process the order payment.
        
        Returns:
            JsonResponse: Processing result with appropriate status code
        """
        user_id = self.metadata.get('user_id')
        if not user_id:
            return JsonResponse(
                {"error": "User ID not found in metadata"},
                status=status.HTTP_400_BAD_REQUEST
            )

        paystack_webhook = PaystackWebhook.objects.filter(
            reference=self.transaction_id
        ).first()
        if not paystack_webhook:
            return JsonResponse(
                {"error": "Transaction reference not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            with transaction.atomic():
                return self._create_order(user_id, paystack_webhook)
        except Exception as e:
            logging.error(f"Order processing failed: {e}")
            clear_user_cache(user_id)
            return JsonResponse(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_order(self, user_id: int, paystack_webhook: PaystackWebhook) -> JsonResponse:
        """
        Create the order and associated items.
        
        Args:
            user_id (int): ID of the user making the purchase
            paystack_webhook (PaystackWebhook): Associated webhook record
            
        Returns:
            JsonResponse: Created order data with status code
        """
        user = get_object_or_404(CustomUser, id=user_id)
        cart = get_object_or_404(Cart, user=user)
        
        order = self._create_order_record(user, cart)
        self._process_cart_items(cart, order)
        self._update_webhook_record(paystack_webhook, order, cart.store.id)
        self._process_shipment_details(order, user_id)
        
        cart.items.all().delete()
        return JsonResponse(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    def _create_order_record(self, user: CustomUser, cart: Cart) -> StoreOrder:
        """
        Create the main order record.
        
        Args:
            user (CustomUser): User making the purchase
            cart (Cart): User's shopping cart
            
        Returns:
            Order: Created order instance
            
        Raises:
            ValueError: If order data is invalid
        """
        order_data = {
            'buyer': user.id,
            'store': cart.store.id,
            'total_price': self.total_price,
            'status': 'Completed',
        }
        order_serializer = OrderSerializer(data=order_data)
        if not order_serializer.is_valid():
            raise ValueError(order_serializer.errors)
        return order_serializer.save()

    def _process_cart_items(self, cart: Cart, order: StoreOrder) -> None:
        """
        Process each cart item and create order items.
        
        Args:
            cart (Cart): User's shopping cart
            order (Order): Created order instance
            
        Raises:
            ValueError: If order item data is invalid
        """
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
                raise ValueError(order_item_serializer.errors)
            order_item_serializer.save()

    def _update_webhook_record(
        self,
        webhook: PaystackWebhook,
        order: StoreOrder,
        store_id: int
    ) -> None:
        """
        Update the Paystack webhook record.
        
        Args:
            webhook (PaystackWebhook): Webhook record to update
            order (Order): Associated order
            store_id (int): ID of the store
        """
        webhook.store_id = store_id
        webhook.data = self.data
        webhook.status = 'Success'
        webhook.order = order
        webhook.save()

    def _process_shipment_details(self, order: StoreOrder, user_id: int) -> None:
        """
        Process shipment details from cache.
        
        Args:
            order (Order): Order to update with shipment details
            user_id (int): ID of the user
        """
        shipment_feedback = cache.get(f'shipment_{user_id}')
        if not shipment_feedback:
            return

        try:
            shipment_data = json.loads(shipment_feedback)
            order.tracking_id = shipment_data['data']['order_id']
            order.tracking_url = shipment_data['data']['tracking_url']
            order.tracking_status = shipment_data['data']['status']
            order.delivery_location = shipment_data['data']['ship_to']['address']
            order.shipping_fee = shipment_data['data']['payment']['shipping_fee']
            order.save()
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Failed to process shipment details: {e}")
        finally:
            clear_user_cache(user_id)