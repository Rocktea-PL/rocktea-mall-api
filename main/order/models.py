from django.db import models
from mall.models import Product, CustomUser, Store
from uuid import uuid4


class OrderItems(models.Model):
   order = models.ForeignKey('Order', related_name='order_items', on_delete=models.CASCADE, null=True)
   product = models.ForeignKey(Product, related_name='product_orders', on_delete=models.CASCADE, null=True)
   quantity = models.PositiveIntegerField()


class Order(models.Model):
   STATUS_CHOICES = (
      ("Pending", "Pending"),
      ("Completed", "Completed"),
      ("In-Review", "In-Review")
   )
   
   id = models.CharField(primary_key=True, default=uuid4, max_length=36)
   buyer = models.ForeignKey(CustomUser, related_name='orders', on_delete=models.CASCADE, null=True)
   store = models.ForeignKey(Store, related_name="stores", null=True, on_delete=models.CASCADE)
   status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="Pending", null=True)
   total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
   shipping_address = models.CharField(max_length=300, null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   updated_at = models.DateTimeField(auto_now=True, null=True)
   # affiliate = models.ForeignKey("rocktea_pl.Affiliate", related_name='affiliates', on_delete=models.CASCADE, null=True)

   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         # models.Index(fields=[''], name='serial_number_serial_numberx'),
         models.Index(fields=['id'], name='order_id_idx'),
         models.Index(fields=['buyer'], name='order_buyer_buyerx'),
         models.Index(fields=['store'], name='order_store_storex')
      ]


# class OrderItems(models.Model):
#    order = models.ForeignKey('Order', related_name='order_items', on_delete=models.CASCADE, null=True)
#    product = models.ManyToManyField(Product, related_name='order_products')
#    quantity = models.PositiveIntegerField()
#    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
#    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

#    def __str__(self):
#       return self.order.id


# class Order(models.Model):
#    ORDER_STATUS = (
#       ("Pending", "Pending"),
#       ("En-Route", "En-Route"),
#       ("Under-Review", "Under-Review"),
#       ("Delivered", "Delivered")
#    )
#    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
#    buyer = models.ForeignKey(CustomUser, related_name="orders", on_delete=models.CASCADE, null=True)
#    store = models.ForeignKey(Store, related_name="stores", null=True, on_delete=models.CASCADE)
#    status = models.CharField(max_length=12, choices=ORDER_STATUS, default="Pending")
#    shipping_address = models.CharField(max_length=400, null=True)
#    created_at = models.DateTimeField(auto_now_add=True, null=True)
#    updated_at = models.DateTimeField(auto_now=True, null=True)
   
#    class Meta:
#       # Add an index for the 'uid' field
#       indexes = [
#          # models.Index(fields=[''], name='serial_number_serial_numberx'),
#          models.Index(fields=['id'], name='order_id_idx'),
#          models.Index(fields=['buyer'], name='order_buyer_buyerx'),
#          models.Index(fields=['store'], name='order_store_storex')
#       ]

#    @property
#    def calculate_total_price(self):
#       total_price = sum(item.calculate_item_total_price() for item in self.order_items.all())
#       return total_price

#    def save(self, *args, **kwargs):
#       self.total_price = self.calculate_total_price
#       super().save(*args, **kwargs)
