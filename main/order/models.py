from django.db import models
from mall.models import Product, CustomUser, Store, ProductVariant #StoreProductVariant
from uuid import uuid4
import random as rand, string


class StoreOrder(models.Model):
   STATUS_CHOICES = (
      ("Pending", "Pending"),
      ("Completed", "Completed"),
      ("In-Review", "In-Review")
   )
   id = models.CharField(primary_key=True, default=uuid4, max_length=36)
   buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_orders', null=True)
   store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='store_orders', null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   total_price = models.DecimalField(decimal_places=2, max_digits=11, default=0.00, null=True)
   status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="Pending", null=True)
   order_id = models.CharField(max_length=5, unique=True, null=True)
   
   def save(self, *args, **kwargs):
      if not self.order_id:
         random_digits = "".join(rand.choices(string.digits, k=5))
         self.order_id = random_digits
      return super(StoreOrder, self).save(*args, **kwargs)


class OrderItems(models.Model):
   userorder = models.ForeignKey(StoreOrder, on_delete=models.CASCADE, related_name='items', null=True)
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_product', null=True)
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING, null=True)
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True, null=True)


class Cart(models.Model):
   user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_cart', null=True)
   store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stores_cart', null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   


class CartItem(models.Model):
   cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product')  # Assuming you have a Product model
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING, null=True)
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True)
   price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True)
   
   def __str__(self):
      return self.cart.id