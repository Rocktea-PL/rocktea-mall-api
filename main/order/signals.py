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
      
      order = instance.userorder
      store_id = order.store.id
      order_id = order.id
      total_profit = Decimal('0.00')

      try:
         pricing = StoreProductPricing.objects.get(
               product=instance.product, store=store_id)
         retail_price = Decimal(str(pricing.retail_price))
         wholesale_price = Decimal(str(instance.product_variant.wholesale_price))
         profit_per_item = retail_price - wholesale_price
         total_profit = profit_per_item * instance.quantity
      except StoreProductPricing.DoesNotExist:
         total_profit = Decimal('0.00')

      wallet, created = Wallet.objects.get_or_create(store_id=store_id)
      wallet.balance = Decimal(str(wallet.balance)) + total_profit
      wallet.save(update_fields=['balance'])

      PaymentHistory.objects.create(
         store_id=store_id, order_id=order_id, amount=total_profit)

@receiver(post_save, sender=StoreOrder)
def send_order_completion_email(sender, instance, created, **kwargs):
   """Send order completion email when order status changes to Completed"""
   if not created and instance.status == 'Completed' and instance.buyer and instance.buyer.email:
      from order.email_service import OrderEmailService
      from setup.tasks import send_order_completion_email_task
      
      send_order_completion_email_task.delay(instance.id)

@receiver(post_save, sender=StoreOrder)
def create_order_notification(sender, instance, created, **kwargs):
   """Create notification for store owner when order is created"""
   if created and instance.store:
      from decimal import Decimal
      
      total_profit = Decimal('0.00')
      for item in instance.items.all():
         try:
            pricing = StoreProductPricing.objects.get(
               product=item.product, store=instance.store.id)
            retail_price = Decimal(str(pricing.retail_price))
            wholesale_price = Decimal(str(item.product_variant.wholesale_price))
            profit_per_item = retail_price - wholesale_price
            total_profit += profit_per_item * item.quantity
         except StoreProductPricing.DoesNotExist:
            pass
      
      notification_message = f"Your customer {instance.buyer.first_name} {instance.buyer.last_name} just made an order, you earned NGN {total_profit}."
      Notification.objects.create(
         store=instance.store, 
         message=notification_message, 
         notification_type='payment'
      )

