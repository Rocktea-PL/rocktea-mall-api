from .models import (
   PaymentHistory, StoreOrder, 
   OrderItems, StoreProductPricing
   )
from mall.models import Wallet, Notification, Store
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.shortcuts import get_object_or_404
from setup.tasks import send_email_task
from datetime import datetime

@receiver(post_save, sender=OrderItems)
def create_payment_history(sender, instance, created, **kwargs):
   if created:
      from decimal import Decimal
      
      order = instance.userorder  # Get the related StoreOrder instance
      store_id = order.store.id
      order_id = order.id
      total_profit = Decimal('0.00')

      # Calculate profit only for the current order item
      try:
         pricing = StoreProductPricing.objects.get(
               product=instance.product, store=store_id)
         retail_price = Decimal(str(pricing.retail_price))
         wholesale_price = Decimal(str(instance.product_variant.wholesale_price))
         profit_per_item = retail_price - wholesale_price
         total_profit = profit_per_item * instance.quantity
      except StoreProductPricing.DoesNotExist:
         total_profit = Decimal('0.00')

      # Update store's wallet balance
      wallet, created = Wallet.objects.get_or_create(store_id=store_id)
      wallet.balance = Decimal(str(wallet.balance)) + total_profit
      wallet.save(update_fields=['balance'])

      # Create PaymentHistory object with the calculated total profit
      PaymentHistory.objects.create(
         store_id=store_id, order_id=order_id, amount=total_profit)
      
      # Create Notification
      notification_message = f"Your customer {order.buyer.first_name} {order.buyer.last_name} just made an order, you earned NGN {total_profit}."
      store = get_object_or_404(Store, id=store_id)
      
      Notification.objects.create(store=store, message=notification_message, notification_type='payment')

@receiver(post_save, sender=StoreOrder)
def send_order_completion_email(sender, instance, created, **kwargs):
   """Send order completion email when order status is Completed"""
   if instance.status == 'Completed' and instance.buyer and instance.buyer.email:
      # Use the email service instead of duplicating logic
      from order.email_service import OrderEmailService
      from setup.tasks import send_order_completion_email_task
      
      # Trigger the email task
      send_order_completion_email_task.delay(instance.id)

