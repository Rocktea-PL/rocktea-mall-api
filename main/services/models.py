from django.db import models
from mall.models import ServicesBusinessInformation, CustomUser

class ServicesCategory(models.Model):
   name = models.CharField(max_length=50, unique=True)
   
   def __str__(self):
      return self.name
   
