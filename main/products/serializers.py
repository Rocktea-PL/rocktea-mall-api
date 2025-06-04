from rest_framework import serializers
from django.db.models import Sum
from mall.models import Product, ProductVariant, Category, SubCategories, ProductTypes, Brand, ProductImage
from order.models import OrderItems
import json
from mall.serializers import ProductVariantSerializer, ProductImageSerializer
import logging

logger = logging.getLogger(__name__)

class AdminProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products by admin"""
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
    producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
    wholesale_price = serializers.DecimalField(max_digits=11, decimal_places=2, write_only=True)
    size = serializers.CharField(required=False, allow_blank=True, write_only=True)
    colors = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'quantity', 'category', 'subcategory', 
            'brand', 'producttype', 'wholesale_price', 'size', 'colors',
            'is_available', 'upload_status'
        ]
        extra_kwargs = {
            'upload_status': {'default': 'Approved'}
        }
    
    def create(self, validated_data):
        # Extract variant data
        wholesale_price = validated_data.pop('wholesale_price')
        size = validated_data.pop('size', '')
        colors = validated_data.pop('colors', '')
        
        # Create product
        product = Product.objects.create(**validated_data)

        # Convert string representations to actual lists
        size_list = self._parse_array(size)
        colors_list = self._parse_array(colors)
        
        # Create product variant with wholesale price
        variant = ProductVariant.objects.create(
            wholesale_price=wholesale_price,
            size=size_list,
            colors=colors_list
        )
        
        # Add product to variant using the proper ManyToMany method
        variant.product.add(product)
        
        return product

    def _parse_array(self, value):
        """Convert string representation to list"""
        if not value:
            return []
        
        try:
            # Try to parse as JSON if it looks like JSON
            if value.startswith('[') and value.endswith(']'):
                return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Fallback to comma-separated values
        return [item.strip() for item in value.split(',') if item.strip()]


class AdminProductListSerializer(serializers.ModelSerializer):
    """Serializer for listing products in admin panel"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    wholesale_price = serializers.SerializerMethodField()
    units_sold = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'quantity', 'category_name', 'brand_name',
            'wholesale_price', 'units_sold', 'stock_status', 'is_available',
            'upload_status', 'created_at', 'image_count', 'primary_image'
        ]

    def get_primary_image(self, obj):
        """Get URL of the first product image"""
        first_image = obj.images.first()
        if first_image and first_image.images:
            return first_image.images.url
        return None
    
    def get_wholesale_price(self, obj):
        """Get wholesale price from product variant with fallback"""
        variant = obj.product_variants.first()
        if variant and variant.wholesale_price is not None:
            return '{:,.2f}'.format(variant.wholesale_price)
        return "0.00"
    
    def get_units_sold(self, obj):
        """Calculate total units sold for this product"""
        total_sold = OrderItems.objects.filter(product=obj).aggregate(
            total=Sum('quantity')
        )['total']
        return total_sold or 0
    
    def get_stock_status(self, obj):
        """Determine stock status based on quantity"""
        if obj.quantity == 0:
            return 'out_of_stock'
        elif obj.quantity <= 10:
            return 'low_stock'
        else:
            return 'in_stock'
    
    def get_image_count(self, obj):
        """Get count of product images"""
        return obj.images.count()
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_at'] = instance.formatted_created_at()
        return representation


class AdminProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual product view"""
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
    producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
    images = ProductImageSerializer(many=True, read_only=True)
    product_variants = ProductVariantSerializer(many=True, read_only=True)
    units_sold = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    sales_analytics = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'quantity', 'category',
            'subcategory', 'brand', 'producttype', 'images', 'product_variants',
            'units_sold', 'stock_status', 'sales_analytics', 'is_available',
            'upload_status', 'created_at', 'sales_count'
        ]
        read_only_fields = ('id', 'sku', 'created_at', 'sales_count')

    def get_units_sold(self, obj):
        """Calculate total units sold"""
        total_sold = OrderItems.objects.filter(product=obj).aggregate(
            total=Sum('quantity')
        )['total']
        return total_sold or 0
    
    def get_stock_status(self, obj):
        """Get detailed stock status"""
        units_sold = self.get_units_sold(obj)
        remaining_stock = obj.quantity
        
        status = 'in_stock'
        if remaining_stock == 0:
            status = 'out_of_stock'
        elif remaining_stock <= 10:
            status = 'low_stock'
        
        return {
            'status': status,
            'current_quantity': remaining_stock,
            'units_sold': units_sold,
            'reorder_level': 10  # Configurable reorder level
        }
    
    def get_sales_analytics(self, obj):
        """Get basic sales analytics"""
        order_items = OrderItems.objects.filter(product=obj).select_related(
            'userorder__store'
        )
        
        # Sales by store
        sales_by_store = {}
        total_revenue = 0
        
        for item in order_items:
            store_name = item.userorder.store.name
            if store_name not in sales_by_store:
                sales_by_store[store_name] = {'quantity': 0, 'orders': 0}
            
            sales_by_store[store_name]['quantity'] += item.quantity
            sales_by_store[store_name]['orders'] += 1
            
            # Calculate revenue based on wholesale price
            variant = obj.product_variants.first()
            if variant:
                total_revenue += float(variant.wholesale_price) * item.quantity
        
        return {
            'total_revenue': '{:,.2f}'.format(total_revenue),
            'sales_by_store': sales_by_store,
            'total_orders': order_items.count()
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_at'] = instance.formatted_created_at()
        return representation


class AdminProductSerializer(serializers.ModelSerializer):
    """General admin product serializer for updates"""
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
    producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
    wholesale_price = serializers.DecimalField(max_digits=11, decimal_places=2, required=False)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'quantity', 'category',
            'subcategory', 'brand', 'producttype', 'wholesale_price',
            'is_available', 'upload_status', 'images'
        ]
        read_only_fields = ('id', 'sku')
    
    def update(self, instance, validated_data):
        # Extract special fields that need custom handling
        new_images = validated_data.pop('images', None)
        wholesale_price = validated_data.pop('wholesale_price', None)
        
        # Handle image updates ONLY if new images are explicitly provided
        if new_images:  # Changed from `is not None` to just check if truthy
            try:
                # Get current images to delete them properly
                current_images = list(instance.images.all())
                
                # Clear the relationship first to avoid foreign key constraints
                instance.images.clear()
                
                # Delete old images from Cloudinary and database
                for old_image in current_images:
                    try:
                        # Delete from Cloudinary first
                        if old_image.images:
                            old_image.images.delete(save=False)
                    except Exception as e:
                        logger.error(f"Failed to delete image from Cloudinary: {e}")
                    
                    # Delete the ProductImage instance
                    try:
                        old_image.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete ProductImage instance: {e}")
                
                # Add new images
                for img in new_images:
                    try:
                        # Create new ProductImage with the uploaded image
                        product_image = ProductImage.objects.create(images=img)
                        instance.images.add(product_image)
                        logger.info(f"Successfully created new ProductImage with ID: {product_image.id}")
                    except Exception as e:
                        logger.error(f"Failed to create new ProductImage: {e}")
                        raise serializers.ValidationError(f"Failed to upload image: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error handling image updates: {e}")
                raise serializers.ValidationError(f"Failed to update images: {str(e)}")
        
        # Update wholesale price in variant if provided
        if wholesale_price is not None:
            try:
                variant = instance.product_variants.first()
                if variant:
                    variant.wholesale_price = wholesale_price
                    variant.save()
                else:
                    # Create a new variant if none exists
                    variant = ProductVariant.objects.create(
                        wholesale_price=wholesale_price,
                        size=[],
                        colors=[]
                    )
                    variant.product.add(instance)
            except Exception as e:
                logger.error(f"Failed to update wholesale price: {e}")
        
        # Update other product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance
        instance.save()
        return instance


class BulkStockUpdateSerializer(serializers.Serializer):
    """Serializer for bulk stock updates"""
    updates = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_updates(self, value):
        """Validate bulk update data"""
        if not value:
            raise serializers.ValidationError("Updates list cannot be empty")
        
        for i, update in enumerate(value):
            if not isinstance(update, dict):
                raise serializers.ValidationError(f"Update {i+1}: Must be a dictionary")
            
            if 'product_id' not in update:
                raise serializers.ValidationError(f"Update {i+1}: Missing 'product_id'")
            
            if 'quantity' not in update:
                raise serializers.ValidationError(f"Update {i+1}: Missing 'quantity'")
            
            # Validate product_id exists
            try:
                product_id = int(update['product_id'])
                if not Product.objects.filter(id=product_id).exists():
                    raise serializers.ValidationError(f"Update {i+1}: Product with ID {product_id} does not exist")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Update {i+1}: Invalid product_id: {update['product_id']}")
            
            # Validate quantity
            try:
                quantity = int(update['quantity'])
                if quantity < 0:
                    raise serializers.ValidationError(f"Update {i+1}: Quantity cannot be negative")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Update {i+1}: Invalid quantity: {update['quantity']}")
        
        return value


class ProductApprovalSerializer(serializers.Serializer):
    """Serializer for product approval"""
    product_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        default='approve'
    )
    
    def validate_product_ids(self, value):
        """Validate that all product IDs exist"""
        if not value:
            raise serializers.ValidationError("Product IDs list cannot be empty")
        
        # Convert to integers and validate
        valid_ids = []
        for product_id in value:
            try:
                valid_ids.append(int(product_id))
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Invalid product ID: {product_id}")
        
        # Check if all products exist
        existing_count = Product.objects.filter(id__in=valid_ids).count()
        if existing_count != len(valid_ids):
            raise serializers.ValidationError("Some product IDs do not exist")
        
        return valid_ids