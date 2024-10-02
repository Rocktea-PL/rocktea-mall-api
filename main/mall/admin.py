from django.contrib import admin
from .models import CustomUser, Product, Category, SubCategories, ProductTypes, Brand, ProductImage, ProductVariant, Store
from django.utils.html import format_html

admin.site.register(CustomUser)
# admin.site.register(Product)
admin.site.register(Category)
admin.site.register(SubCategories)
admin.site.register(ProductTypes)
admin.site.register(Brand)
admin.site.register(ProductVariant)
# admin.site.register(Store)
admin.site.register(ProductImage)

admin.site.site_header = 'RockTea Mall'
admin.site.site_title = 'Dropshipping Made Easy'


class ProductList(admin.ModelAdmin):
    list_display = ["name", "quantity", "description", "category", "subcategory", "brand", "producttype", "product_image"]
    list_select_related = ["category", "subcategory", "brand", "producttype"]
    list_per_page = 10
    
    def product_image(self, obj):
        image_urls = [image.images.url for image in obj.images.all()]
        return format_html('<br>'.join('<a href="{0}">{0}</a>'.format(url) for url in image_urls))

    # Double-underscore is used to notation to specify the related field's attribute to search
    search_fields = ["name", "brand__name", "subcategory__name", "producttype__name"]

    # actions = [approve_products, reject_product]
    
        
    ordering = ['-created_at']
    

admin.site.register(Product, ProductList)


class StoreList(admin.ModelAdmin):
    list_display = ["name", "email", "domain_name", "completed"]
    list_select_related = ["owner", "category"]
    list_per_page = 10

    search_fields = ["name"]

    ordering = ['-created_at']
    
admin.site.register(Store, StoreList)