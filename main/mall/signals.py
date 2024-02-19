from .models import Store, Wallet, StoreProductPricing, MarketPlace
from django.dispatch import receiver
from django.db.models.signals import post_save

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





