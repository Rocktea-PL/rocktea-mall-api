from mall.models import Store, Wallet, StoreProductPricing, MarketPlace
from order.models import PaymentHistory, StoreOrder, OrderItems
from django.dispatch import receiver

# Signals
@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
   #Create Wallet for every Store
   if created:
      Wallet.objects.get_or_create(store=instance)


@receiver(post_save, sender=StoreProductPricing)
def create_marketplace(sender, instance, created, **kwargs):
   if created:
      related_product = instance.product
      related_store = instance.store
      MarketPlace.objects.get_or_create(
         store=related_store, product=related_product)


@receiver(post_save, sender=OrderItems)
def create_payment_history(sender, instance, created, **kwargs):
   if created:
      order = instance.userorder  # Get the related StoreOrder instance
      store_id = order.store.id
      order_id = order.id

      total_amount = 0
      for item in order.items.all():  # Iterate over all items in the order
         total_amount += item.product.retail_price * item.quantity

      # Update store's wallet balance
      wallet, created = Wallet.objects.get_or_create(store_id=store_id)
      wallet.balance += total_amount
      wallet.save()

      # Create PaymentHistory object with the calculated total amount
      PaymentHistory.objects.create(
         store_id=store_id, order_id=order_id, amount=total_amount)


