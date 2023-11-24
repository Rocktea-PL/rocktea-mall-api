from django.db import models
from mall.models import Product, CustomUser, Store, ProductVariant #StoreProductVariant
from uuid import uuid4


class OrderItems(models.Model):
   order = models.ForeignKey('Order', related_name='order_items', on_delete=models.CASCADE, null=True)
   product = models.ForeignKey(Product, related_name='product_orders', on_delete=models.CASCADE, null=True)
   # store_variant = models.ForeignKey(StoreProductVariant, related_name='store_orders', on_delete=models.CASCADE, null=True)
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True)
   quantity = models.PositiveIntegerField()


class Order(models.Model):
   STATUS_CHOICES = (
      ("Pending", "Pending"),
      ("Completed", "Completed"),
      ("In-Review", "In-Review")
   )
   
   id = models.CharField(primary_key=True, default=uuid4, max_length=36)
   buyer = models.ForeignKey(CustomUser, related_name='orders_buyer', on_delete=models.CASCADE, null=True)
   store = models.ForeignKey(Store, related_name="stores", null=True, on_delete=models.CASCADE)
   status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="Pending", null=True)
   total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
   shipping_address = models.CharField(max_length=300, null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   updated_at = models.DateTimeField(auto_now=True, null=True)

   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         # models.Index(fields=[''], name='serial_number_serial_numberx'),
         models.Index(fields=['id'], name='order_id_idx'),
         models.Index(fields=['buyer'], name='order_buyer_buyerx'),
         models.Index(fields=['store'], name='order_store_storex')
      ]


class Cart(models.Model):
   user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_cart', null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)


class CartItem(models.Model):
   cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product')  # Assuming you have a Product model
   # product_variant = models.ForeignKey()
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True)
