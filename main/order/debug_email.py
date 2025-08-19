"""
Debug order email to see what data we have
"""
from order.models import StoreOrder
from order.email_service import OrderEmailService

def debug_order_email(order_id):
    """Debug order email data"""
    try:
        order = StoreOrder.objects.select_related('buyer', 'store', 'state').prefetch_related('items__product', 'items__product_variant').get(id=order_id)
        
        print(f"Order ID: {order.id}")
        print(f"Order SN: {order.order_sn}")
        print(f"Store: {order.store.name}")
        print(f"Buyer: {order.buyer.email}")
        print(f"Items count: {order.items.count()}")
        
        for item in order.items.all():
            print(f"  - Product: {item.product.name}")
            print(f"    Quantity: {item.quantity}")
            print(f"    Variant: {item.product_variant}")
            
            # Check store pricing
            from mall.models import StoreProductPricing
            try:
                pricing = StoreProductPricing.objects.get(product=item.product, store=order.store)
                print(f"    Store Price: {pricing.retail_price}")
            except StoreProductPricing.DoesNotExist:
                print(f"    No store pricing found")
        
        # Test email service
        context = OrderEmailService.build_email_context(order)
        print(f"\nEmail context:")
        print(f"  Has items: {context.get('has_items')}")
        print(f"  Items count: {len(context.get('order_items', []))}")
        print(f"  Subtotal: {context.get('subtotal')}")
        print(f"  Total: {context.get('total_amount')}")
        
        for item in context.get('order_items', []):
            print(f"  - {item['product_name']}: {item['quantity']} x ₦{item['unit_price']} = ₦{item['total_price']}")
        
        return context
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None