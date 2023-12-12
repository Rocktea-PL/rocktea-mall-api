from django.contrib import admin
from .models import StoreOrder, OrderItems

# Register your models here.
admin.site.register(StoreOrder)
admin.site.register(OrderItems)