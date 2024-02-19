from django.contrib import admin
from .models import CustomUser, Product, Category, SubCategories, ProductTypes, Brand, ProductImage, ProductVariant, Store

admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(SubCategories)
admin.site.register(ProductTypes)
admin.site.register(Brand)
admin.site.register(ProductVariant)
admin.site.register(Store)
admin.site.register(ProductImage)
