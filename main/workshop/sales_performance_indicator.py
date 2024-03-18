from mall.models import Store, Product
from order.models import StoreOrder, OrderItems
from django.shortcuts import get_object_or_404


class SalesPerformanceIndicator:
   def __init__(self):
      pass
   
   def total_sale_for_product(self):
      product = get_object_or_404(Product, id=product_id)
      sales_count = product.sales_count
      return sales_count
   
   def time_since_product_added(self, item, timesince):
      pass
   
   def freq_of_sale(self, item, time_since):
      pass