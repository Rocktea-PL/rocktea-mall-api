"""
Order Email Service - Modular email handling for orders
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class OrderEmailService:
    """Service for handling order-related emails with proper data formatting"""
    
    @staticmethod
    def get_order_items_data(order) -> tuple[List[Dict], Decimal]:
        """Extract and format order items with accurate pricing and images"""
        order_items = []
        subtotal = Decimal('0.00')
        
        for item in order.items.all():
            # Get store pricing - same as products endpoint
            try:
                from mall.models import StoreProductPricing
                store_pricing = StoreProductPricing.objects.get(
                    product=item.product, 
                    store=order.store
                )
                unit_price = store_pricing.retail_price
            except StoreProductPricing.DoesNotExist:
                unit_price = Decimal('0.00')
            
            item_total = unit_price * item.quantity
            subtotal += item_total
            
            # Get product image
            product_image = None
            first_image = item.product.images.first()
            if first_image and first_image.images:
                product_image = first_image.images.url
            
            # Format variant
            variant_name = OrderEmailService._format_variant_name(item.product_variant)
            
            order_items.append({
                'product_name': item.product.name,
                'variant_name': variant_name,
                'quantity': item.quantity,
                'unit_price': f"{float(unit_price):.2f}",
                'total_price': f"{float(item_total):.2f}",
                'product_image': product_image
            })
        
        return order_items, subtotal
    
    @staticmethod
    def _format_variant_name(product_variant) -> Optional[str]:
        """Format product variant information"""
        if not product_variant:
            return None
            
        variant_parts = []
        
        if product_variant.size:
            variant_parts.append(f"Size: {product_variant.size}")
            
        if product_variant.colors:
            colors = ', '.join(product_variant.colors) if isinstance(product_variant.colors, list) else str(product_variant.colors)
            variant_parts.append(f"Color: {colors}")
        
        return ' | '.join(variant_parts) if variant_parts else None
    
    @staticmethod
    def get_delivery_fee(order) -> Decimal:
        """Calculate delivery fee from various sources"""
        if order.state and order.state.delivery_fee:
            return Decimal(str(order.state.delivery_fee))
        elif order.shipping_fee:
            return Decimal(str(order.shipping_fee))
        return Decimal('0.00')
    
    @staticmethod
    def build_email_context(order) -> Dict:
        """Build complete email context for order completion email"""
        order_items, subtotal = OrderEmailService.get_order_items_data(order)
        delivery_fee = OrderEmailService.get_delivery_fee(order)
        total_amount = Decimal(str(order.total_price)) if order.total_price else Decimal('0.00')
        
        # Customer name with fallback
        customer_name = f"{order.buyer.first_name} {order.buyer.last_name}".strip()
        if not customer_name:
            customer_name = order.buyer.email.split('@')[0].title()
        
        return {
            'customer_name': customer_name,
            'store_name': order.store.name,
            'order_number': order.order_sn,
            'order_date': order.created_at.strftime('%B %d, %Y') if order.created_at else datetime.now().strftime('%B %d, %Y'),
            'order_status': order.status,
            'subtotal': f"{float(subtotal):.2f}",
            'delivery_fee': f"{float(delivery_fee):.2f}" if delivery_fee > 0 else None,
            'total_amount': f"{float(total_amount):.2f}",
            'delivery_location': order.delivery_location,
            'delivery_code': order.delivery_code,
            'tracking_url': order.tracking_url,
            'order_items': order_items,
            'current_year': datetime.now().year,
            'has_items': len(order_items) > 0
        }