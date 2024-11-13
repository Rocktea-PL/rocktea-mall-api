from django.contrib import admin
from .models import StoreOrder, OrderItems, PaystackWebhook, PaymentHistory

# Register your models here.
admin.site.register(StoreOrder)
admin.site.register(OrderItems)
admin.site.register(PaystackWebhook)
admin.site.register(PaymentHistory)