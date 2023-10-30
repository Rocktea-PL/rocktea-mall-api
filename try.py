# from django.db import models


# class Store(models.Model):
#    name = models.CharField(max_length=100)


# class Dropshippers(models.Model):
#    store = models.OneToOneField(Store, on_delete=models.CASCADE)
#    name = models.CharField(max_length=100)
   

# class Product(models.Model):
#    name = models.CharField(max_length=100)
   

# class ProductVariant(models.Model):
#    product = models.ManyToManyField(Product)
#    size = models.CharField(max_length=50)
#    wholesale_price = models.DecimalField(max_digits=11, decimal_places=2)
#    retail_price = models.DecimalField(max_digits=11, decimal_places=2)
   
