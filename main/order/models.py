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
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING,null=True)
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True)
   
   def __str__(self):
      return self.cart.id


"""=======IGNORE=============IGNORE ============ X=======X ==========IGNORE=========X=============X============XIGNORE----------------=="""
# class OrderItems(models.Model):
#    order = models.ForeignKey('Order', related_name='order_items', on_delete=models.CASCADE, null=True)
#    product = models.ForeignKey(Product, related_name='product_orders', on_delete=models.CASCADE, null=True)
#    # store_variant = models.ForeignKey(StoreProductVariant, related_name='store_orders', on_delete=models.CASCADE, null=True)
#    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True)
#    quantity = models.PositiveIntegerField()


# class Order(models.Model):
#    STATUS_CHOICES = (
#       ("Pending", "Pending"),
#       ("Completed", "Completed"),
#       ("In-Review", "In-Review")
#    )

#    id = models.CharField(primary_key=True, default=uuid4, max_length=36)
#    buyer = models.ForeignKey(CustomUser, related_name='orders_buyer', on_delete=models.CASCADE, null=True)
#    store = models.ForeignKey(Store, related_name="stores", null=True, on_delete=models.CASCADE)
#    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="Pending", null=True)
#    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
#    shipping_address = models.CharField(max_length=300, null=True)
#    created_at = models.DateTimeField(auto_now_add=True, null=True)
#    updated_at = models.DateTimeField(auto_now=True, null=True)

#    class Meta:
#       # Add an index for the 'uid' field
#       indexes = [
#          models.Index(fields=['id'], name='order_id_idx'),
#          models.Index(fields=['buyer'], name='order_buyer_buyerx'),
#          models.Index(fields=['store'], name='order_store_storex')
#       ]
