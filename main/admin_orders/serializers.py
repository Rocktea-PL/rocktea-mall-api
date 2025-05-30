from order.models import StoreOrder, OrderItems
from mall.models import ProductImage
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class AdminOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    product_sku = serializers.CharField(source='product.sku')
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, source='product.price')
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItems
        fields = ['product_name', 'product_sku', 'quantity', 'amount', 'product_image']

    def get_product_image(self, obj):
        try:
            if obj.product.images.exists():
                return obj.product.images.first().images.url
            return None
        except Exception as e:
            logger.error(f"Image error: {e}")
            return None

class AdminOrderSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='id')
    invoice_no = serializers.CharField(source='order_sn')
    order_date = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S%p")
    items = AdminOrderItemSerializer(many=True, source='items.all')
    total = serializers.DecimalField(max_digits=10, decimal_places=2, source='total_price')
    buyer_name = serializers.SerializerMethodField()
    buyer_contact = serializers.SerializerMethodField()
    delivery_location = serializers.CharField(allow_blank=True, allow_null=True)
    delivery_code = serializers.CharField()

    class Meta:
        model = StoreOrder
        fields = [
            'order_id', 'invoice_no', 'order_date', 'status',
            'total', 'items', 'buyer_name', 'buyer_contact',
            'delivery_location', 'tracking_id', 'tracking_url',
            'delivery_code'
        ]

    def get_buyer_name(self, obj):
        return f"{obj.buyer.first_name} {obj.buyer.last_name}"

    def get_buyer_contact(self, obj):
        return str(obj.buyer.contact)