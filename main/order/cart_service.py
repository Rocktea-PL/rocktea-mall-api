"""
Cart Service - Handles cart operations with proper price calculations
"""
from decimal import Decimal
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from mall.models import StoreProductPricing, ProductVariant
import logging

logger = logging.getLogger(__name__)

class CartService:
    """Service for cart operations following SOLID principles"""
    
    @staticmethod
    def get_item_price(product_id, store, quantity=1):
        """Get correct price for a product in a store"""
        try:
            pricing = StoreProductPricing.objects.get(product_id=product_id, store=store)
            unit_price = Decimal(str(pricing.retail_price))
            total_price = unit_price * quantity
            return unit_price, total_price
        except StoreProductPricing.DoesNotExist:
            logger.warning(f"No pricing found for product {product_id} in store {store.id}")
            return Decimal('0.00'), Decimal('0.00')
    
    @staticmethod
    def update_cart_total(cart):
        """Recalculate and update cart total price"""
        total = Decimal('0.00')
        for item in cart.items.all():
            unit_price, item_total = CartService.get_item_price(item.product.id, cart.store, item.quantity)
            item.unit_price = unit_price
            item.price = item_total
            item.save(update_fields=['unit_price', 'price'])
            total += item_total
        
        cart.price = total
        cart.save(update_fields=['price'])
        return total
    
    @staticmethod
    def add_or_update_item(cart, product_id, product_variant_id, quantity, store):
        """Add new item or update existing item quantity and price"""
        existing_item = cart.items.filter(
            product_id=product_id, 
            product_variant_id=product_variant_id
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            unit_price, item_total = CartService.get_item_price(product_id, store, existing_item.quantity)
            existing_item.unit_price = unit_price
            existing_item.price = item_total
            existing_item.save(update_fields=['quantity', 'unit_price', 'price'])
            return existing_item
        else:
            product_variant = get_object_or_404(ProductVariant, id=product_variant_id)
            unit_price, item_total = CartService.get_item_price(product_id, store, quantity)
            
            return CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                product_variant=product_variant,
                quantity=quantity,
                unit_price=unit_price,
                price=item_total
            )
    
    @staticmethod
    def update_item_quantity(cart_item, new_quantity):
        """Update cart item quantity and recalculate price"""
        if new_quantity <= 0:
            cart_item.delete()
            return None
        
        cart_item.quantity = new_quantity
        unit_price, item_total = CartService.get_item_price(
            cart_item.product.id, 
            cart_item.cart.store, 
            new_quantity
        )
        cart_item.unit_price = unit_price
        cart_item.price = item_total
        cart_item.save(update_fields=['quantity', 'unit_price', 'price'])
        
        CartService.update_cart_total(cart_item.cart)
        return cart_item