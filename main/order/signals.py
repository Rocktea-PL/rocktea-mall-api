from .models import PaymentHistory, StoreOrder, OrderItems, StoreProductPricing
from mall.models import Wallet
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=OrderItems)
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
