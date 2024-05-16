from django.db import models
from mall.models import Product, CustomUser, Store, ProductVariant, StoreProductPricing, Wallet
from uuid import uuid4
import random as rand, string
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save


class StoreOrder(models.Model):
   STATUS_CHOICES = (
      ("Pending", "Pending"),
      ("nmpleted", "Completed"),
      ("Enroute", "Enroute"),
      ("Delivered", "Delivered"),
      ("Returned", "Returned")
   )
   id = models.CharField(primary_key=True, default=uuid4, max_length=36)
   buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_orders', null=True)
   store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='store_orders', null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   total_price = models.DecimalField(decimal_places=2, max_digits=11, default=0.00, null=True)
   status = models.CharField(max_length=9, choices=STATUS_CHOICES, default="Pending", null=True)
   order_sn = models.CharField(max_length=5, unique=True, null=True)
   delivery_code = models.CharField(max_length=5, null=True, unique=True)
   delivery_location = models.CharField(max_length=200, null=True)
   state = models.ForeignKey('State', on_delete=models.CASCADE, null=True)
   
   def save(self, *args, **kwargs):
      if not self.order_sn:
         random_digits = "".join(rand.choices(string.digits, k=5))
         self.order_sn = random_digits
   
      if not self.delivery_code:
         self.delivery_code = "".join(rand.choices(string.ascii_uppercase + string.digits, k=5))
      return super(StoreOrder, self).save(*args, **kwargs)


class PaymentHistory(models.Model):
   store = models.ForeignKey(Store, on_delete=models.CASCADE)
   order = models.ForeignKey(StoreOrder, on_delete=models.CASCADE)
   amount = models.DecimalField(max_digits=11, decimal_places=2)
   payment_date = models.DateTimeField(auto_now_add=True)

   def __str__(self):
      return self.order.sn


class State(models.Model):
   STATE_CHOICES = (
      ('Abia', 'Abia'),
      ('Adamawa', 'Adamawa'),
      ('Akwa Ibom', 'Akwa Ibom'),
      ('Anambra', 'Anambra'),
      ('Bauchi', 'Bauchi'),
      ('Bayelsa', 'Bayelsa'),
      ('Benue', 'Benue'),
      ('Borno', 'Borno'),
      ('Cross River', 'Cross River'),
      ('Delta', 'Delta'),
      ('Ebonyi', 'Ebonyi'),
      ('Edo', 'Edo'),
      ('Ekiti', 'Ekiti'),
      ('Enugu', 'Enugu'),
      ('FCT (Abuja)', 'FCT (Abuja)'),
      ('Gombe', 'Gombe'),
      ('Imo', 'Imo'),
      ('Jigawa', 'Jigawa'),
      ('Kaduna', 'Kaduna'),
      ('Kano', 'Kano'),
      ('Katsina', 'Katsina'),
      ('Kebbi', 'Kebbi'),
      ('Kogi', 'Kogi'),
      ('Kwara', 'Kwara'),
      ('Lagos', 'Lagos'),
      ('Nasarawa', 'Nasarawa'),
      ('Niger', 'Niger'),
      ('Ogun', 'Ogun'),
      ('Ondo', 'Ondo'),
      ('Osun', 'Osun'),
      ('Oyo', 'Oyo'),
      ('Plateau', 'Plateau'),
      ('Rivers', 'Rivers'),
      ('Sokoto', 'Sokoto'),
      ('Taraba', 'Taraba'),
      ('Yobe', 'Yobe'),
      ('Zamfara', 'Zamfara')
   )
   
   state = models.CharField(choices=STATE_CHOICES, max_length=11)
   delivery_fee = models.DecimalField(max_digits=11, decimal_places=2, default=1500.00)
   zip_code = models.BigIntegerField()
   
   def __str__(self):
      return self.state



class AssignOrder(models.Model):
   order = models.ManyToManyField(StoreOrder)
   rider = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, limit_choices_to={'is_logistics':True}, null=True)


class OrderItems(models.Model):
   userorder = models.ForeignKey(StoreOrder, on_delete=models.CASCADE, related_name='items', null=True)
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_product', null=True)
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING, null=True)
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True, null=True)

   def __str__(self):
      return self.created_at


class OrderDeliveryConfirmation(models.Model):
   userorder = models.ForeignKey('StoreOrder', on_delete=models.DO_NOTHING)
   code = models.CharField(max_length=5)

   def __str__(self):
      return self.code

   def save(self, *args, **kwargs):
      store = self.get_store_order()
      if store.delivery_code == self.code:
         store.status = "Delivered"
         store.save()
         super(OrderDeliveryConfirmation, self).save(*args, **kwargs)
         return Response("Order Confirmed Succesfully")
      else:
         raise ValidationError("Incorrect Delivery Code")

   def get_store_order(self):
      try:
         return StoreOrder.objects.get(id=self.userorder_id)
      except StoreOrder.DoesNotExist:
         raise ValidationError("Store Order Not Found")


class Cart(models.Model):
   user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_cart', null=True)
   store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stores_cart', null=True)
   created_at = models.DateTimeField(auto_now_add=True, null=True)
   price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True)


class CartItem(models.Model):
   cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product')  # Assuming you have a Product model
   product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING, null=True)
   quantity = models.PositiveIntegerField(default=1)
   created_at = models.DateTimeField(auto_now_add=True)
   price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True)
   
   def __str__(self):
      return self.cart.id