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
      # Get order items with proper pricing
      order_items = []
      subtotal = 0
      
      for item in instance.items.all():
         try:
            # Get store pricing for accurate customer pricing
            store_pricing = StoreProductPricing.objects.get(
               product=item.product, 
               store=instance.store
            )
            item_price = float(store_pricing.retail_price) * item.quantity
            subtotal += item_price
            
            order_items.append({
               'product_name': item.product.name,
               'variant_name': item.product_variant.name if item.product_variant else None,
               'quantity': item.quantity,
               'price': f"{item_price:.2f}"
            })
         except StoreProductPricing.DoesNotExist:
            # Fallback to wholesale price if store pricing not found
            item_price = float(item.product_variant.wholesale_price) * item.quantity if item.product_variant else 0
            subtotal += item_price
            
            order_items.append({
               'product_name': item.product.name,
               'variant_name': item.product_variant.name if item.product_variant else None,
               'quantity': item.quantity,
               'price': f"{item_price:.2f}"
            })
      
      # Get delivery fee
      delivery_fee = 0
      if instance.state:
         delivery_fee = float(instance.state.delivery_fee)
      elif instance.shipping_fee:
         delivery_fee = float(instance.shipping_fee)
      
      # Prepare email context
      context = {
         'customer_name': f"{instance.buyer.first_name} {instance.buyer.last_name}".strip() or instance.buyer.email,
         'store_name': instance.store.name,
         'order_number': instance.order_sn,
         'order_date': instance.created_at.strftime('%B %d, %Y') if instance.created_at else datetime.now().strftime('%B %d, %Y'),
         'order_status': instance.status,
         'subtotal': f"{subtotal:.2f}",
         'delivery_fee': f"{delivery_fee:.2f}",
         'total_amount': f"{float(instance.total_price):.2f}" if instance.total_price else "0.00",
         'delivery_location': instance.delivery_location,
         'delivery_code': instance.delivery_code,
         'tracking_url': instance.tracking_url,
         'order_items': order_items,
         'current_year': datetime.now().year
      }
      
      # Send email asynchronously
      send_email_task.delay(
         recipient_email=instance.buyer.email,
         template_name='emails/order_completion.html',
         context=context,
         subject=f'Order Confirmed - #{instance.order_sn} from {instance.store.name}',
         tags=['order_completion', 'customer_notification']
      )
