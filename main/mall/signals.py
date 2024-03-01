from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404

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
      
      # Create Notification
      notification_message = f"{related_store.name} you just added a new product {product.name} from your Marketplace."
      
      store = get_object_or_404(Store, id=related_store)
      
      Notification.objects.create(store=store, message=notification_message)





