from .models import (
   PaymentHistory, StoreOrder, 
   OrderItems, StoreProductPricing
   )
from mall.models import Wallet, Notification, Store
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404


""" @receiver(post_save, sender=OrderItems)
def create_payment_history(sender, instance, created, **kwargs):
   if created:
      order = instance.userorder  # Get the related StoreOrder instance
      store_id = order.store.id
      order_id = order.id
      total_amount = 0

      for item in order.items.all():  # Iterate over all items in the order
         # Fetch the retail price from StoreProductPricing model
         product = item.product
         pricing = StoreProductPricing.objects.get(
            product=product, store=store_id)
         total_amount += pricing.retail_price * item.quantity

      # Update store's wallet balance
      wallet, created = Wallet.objects.get_or_create(store_id=store_id)
      wallet.balance += total_amount  # Add the new balance to the existing balance
      wallet.save()

      # Create PaymentHistory object with the calculated total amount
      PaymentHistory.objects.create(
         store_id=store_id, order_id=order_id, amount=total_amount)
      
      # Create Notification
      notification_message = f"Your customer {order.buyer.first_name} {order.buyer.last_name} just made an order, you earned NGN {total_amount}."
      store = get_object_or_404(Store, id=store_id)
      
      Notification.objects.create(store=store, message=notification_message) """

@receiver(post_save, sender=OrderItems)
def create_payment_history(sender, instance, created, **kwargs):
   if created:
      order = instance.userorder  # Get the related StoreOrder instance
      store_id = order.store.id
      order_id = order.id
      total_profit = 0

      for item in order.items.all():  # Iterate over all items in the order
         # Fetch the retail and wholesale prices from StoreProductPricing model
         product = item.product
         pricing = StoreProductPricing.objects.get(
               product=product, store=store_id)
         retail_price = pricing.retail_price
         wholesale_price = item.product_variant.wholesale_price
         profit_per_item = retail_price - wholesale_price
         total_profit += profit_per_item * item.quantity

      # Update store's wallet balance
      wallet, created = Wallet.objects.get_or_create(store_id=store_id)
      wallet.balance += total_profit  # Add the new balance to the existing balance
      wallet.save()

      # Create PaymentHistory object with the calculated total profit
      PaymentHistory.objects.create(
         store_id=store_id, order_id=order_id, amount=total_profit)
      
      # Create Notification
      notification_message = f"Your customer {order.buyer.first_name} {order.buyer.last_name} just made an order, you earned NGN {total_profit}."
      store = get_object_or_404(Store, id=store_id)
      
      Notification.objects.create(store=store, message=notification_message)
