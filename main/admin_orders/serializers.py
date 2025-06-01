from order.models import StoreOrder, OrderItems, PaystackWebhook
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

class AdminOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    product_sku = serializers.CharField(source='product.sku')
    amount = serializers.SerializerMethodField()  # Keep as method field
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItems
        fields = ['product_name', 'product_sku', 'quantity', 'amount', 'product_image']

    def get_amount(self, obj):
        """Get price from product variant or product"""
        try:
            # First priority: price from specific variant in order item
            if obj.product_variant and obj.product_variant.wholesale_price:
                return obj.product_variant.wholesale_price
            
            # Second priority: any variant of the product
            if obj.product and obj.product.product_variants.exists():
                variant = obj.product.product_variants.first()
                return variant.wholesale_price
            
            # Fallback to 0 if no price found
            return 0.00
        except Exception as e:
            logger.error(f"Price error for order item {obj.id}: {e}")
            return 0.00

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
    
class AdminTransactionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='order.id')
    name = serializers.SerializerMethodField()
    invoice_no = serializers.CharField(source='order.order_sn')
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, source='total_price')
    transaction_details = serializers.SerializerMethodField()
    status = serializers.CharField()

    class Meta:
        model = PaystackWebhook
        fields = ['id', 'name', 'invoice_no', 'amount', 'transaction_details', 'status']

    def get_name(self, obj):
        """Get name of the person who processed the transaction"""
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_transaction_details(self, obj):
        """Get formatted transaction details"""
        return {
            "reference": obj.reference,
            "purpose": obj.purpose,
            "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M:%S%p"),
            "payment_method": obj.data.get('channel') if obj.data else "Unknown",
            "currency": obj.data.get('currency') if obj.data else "NGN"
        }