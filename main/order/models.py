from django.db import models
from mall.models import Product, CustomUser, Store
from uuid import uuid4


class OrderItems(models.Model):
   order = models.ForeignKey('Order', related_name='order_items', on_delete=models.CASCADE)
   product = models.ForeignKey(Product, related_name='product_orders', on_delete=models.CASCADE, null=True)
   quantity = models.PositiveIntegerField()

   def __str__(self):
      return order.id


class Order(models.Model):
   ORDER_STATUS = (
      ("Pending", "Pending"),
      ("En-Route", "En-Route"),
      ("Under-Review", "Under-Review"),
      ("Delivered", "Delivered")
   )
   id = models.CharField(primary_key=True, default=uuid4, max_length=36)
   buyer = models.ForeignKey(CustomUser, related_name="orders", limit_choices_to={"is_consumer":True}, on_delete=models.CASCADE)
   store = models.ForeignKey(Store, related_name="stores", null=True, on_delete=models.CASCADE)
   status = models.CharField(max_length=12, choices=ORDER_STATUS, default="Pending")
   total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   updated_at = models.DateTimeField(auto_now=True, null=True)

   @property
   def calculate_total_price(self):
      total_price = sum(item.product.price * item.quantity for item in self.order_items.all())
      return total_price

   def save(self, *args, **kwargs):
      self.total_price = self.calculate_total_price
      super().save(*args, **kwargs)
      

# class CartItem(models.Model):
#    product = models.ForeignKey(Product, related_name="cart_products", on_delete=models.CASCADE)
#    quantity = models.PositiveIntegerField()
   
   
#    @property
#    def calculate_total_price(self):
#       total_price = P

