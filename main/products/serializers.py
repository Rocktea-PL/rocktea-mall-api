from rest_framework import serializers
from django.db.models import Sum
from mall.models import Product, ProductVariant, Category, SubCategories, ProductTypes, Brand, ProductImage
from order.models import OrderItems
import json
import logging
from django.core.exceptions import ValidationError as DjangoValidationError

logger = logging.getLogger(__name__)

class BaseAdminProductSerializer(serializers.ModelSerializer):
    """Base serializer with common fields for both list and detail views"""
    # category_name = serializers.CharField(source='category.name', read_only=True)
    # brand_name = serializers.CharField(source='brand.name', read_only=True)
    # subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    # producttype_name = serializers.CharField(source='producttype.name', read_only=True)
    category = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    producttype = serializers.SerializerMethodField()
    wholesale_price = serializers.SerializerMethodField()
    units_sold = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'quantity', 'category', 
            'brand', 'subcategory', 'producttype', 'wholesale_price',
            'units_sold', 'stock_status', 'is_available', 'upload_status',
            'created_at', 'image_count', 'product_images', 'size', 'colors'
        ]
    
    def get_wholesale_price(self, obj):
        variant = obj.product_variants.first()
        if variant and variant.wholesale_price is not None:
            return f"{variant.wholesale_price:,.2f}"  # Simplified formatting
        return "0.00"
    
    def get_units_sold(self, obj):
        total_sold = OrderItems.objects.filter(product=obj).aggregate(
            total=Sum('quantity')
        )['total']
        return total_sold or 0
    
    def get_stock_status(self, obj):
        if obj.quantity == 0:
            return 'out_of_stock'
        elif obj.quantity <= 10:
            return 'low_stock'
        else:
            return 'in_stock'
    
    def get_image_count(self, obj):
        return obj.images.count()
    
    def get_product_images(self, obj):
        """Return all image URLs for the product"""
        return [img.images.url for img in obj.images.all() if img.images]
    
    def get_category(self, obj):
        if obj.category:
            return {'id': obj.category.id, 'name': obj.category.name}
        return None

    def get_brand(self, obj):
        if obj.brand:
            return {'id': obj.brand.id, 'name': obj.brand.name}
        return None

    def get_subcategory(self, obj):
        if obj.subcategory:
            return {'id': obj.subcategory.id, 'name': obj.subcategory.name}
        return None

    def get_producttype(self, obj):
        if obj.producttype:
            return {'id': obj.producttype.id, 'name': obj.producttype.name}
        return None
    
    def get_size(self, obj):
        variant = obj.product_variants.first()
        return variant.size if variant else None
    
    def get_colors(self, obj):
        variant = obj.product_variants.first()
        return variant.colors if variant else None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_at'] = instance.formatted_created_at()
        return representation
    
class AdminProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products by admin"""
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
    producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
    wholesale_price = serializers.DecimalField(max_digits=11, decimal_places=2, write_only=True)
    size = serializers.CharField(required=False, allow_blank=True, write_only=True)
    colors = serializers.CharField(required=False, allow_blank=True, write_only=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'quantity', 'category', 'subcategory', 
            'brand', 'producttype', 'wholesale_price', 'size', 'colors',
            'is_available', 'upload_status', 'images'
        ]
        extra_kwargs = {
            'upload_status': {'default': 'Approved'}
        }

    def validate(self, data):
        """Enhanced validation with detailed error messages"""
        errors = {}
        
        # Validate category exists and is active
        if 'category' in data:
            try:
                category = data['category']
                if not hasattr(category, 'id'):
                    errors['category'] = "Invalid category provided"
            except Exception as e:
                errors['category'] = f"Category validation error: {str(e)}"
        
        # Validate subcategory exists and belongs to the category
        if 'subcategory' in data and 'category' in data:
            try:
                subcategory = data['subcategory']
                category = data['category']
                if subcategory.category_id != category.id:
                    errors['subcategory'] = "Subcategory does not belong to the selected category"
            except Exception as e:
                errors['subcategory'] = f"Subcategory validation error: {str(e)}"
        
        # Validate brand exists
        if 'brand' in data:
            try:
                brand = data['brand']
                if not hasattr(brand, 'id'):
                    errors['brand'] = "Invalid brand provided"
            except Exception as e:
                errors['brand'] = f"Brand validation error: {str(e)}"
        
        # Validate producttype exists
        if 'producttype' in data:
            try:
                producttype = data['producttype']
                if not hasattr(producttype, 'id'):
                    errors['producttype'] = "Invalid product type provided"
            except Exception as e:
                errors['producttype'] = f"Product type validation error: {str(e)}"
        
        # Validate wholesale_price
        if 'wholesale_price' in data:
            if data['wholesale_price'] <= 0:
                errors['wholesale_price'] = "Wholesale price must be greater than 0"
        
        # Validate quantity
        if 'quantity' in data:
            if data['quantity'] < 0:
                errors['quantity'] = "Quantity cannot be negative"
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    
    def create(self, validated_data):
        try:
            # Extract variant data
            wholesale_price = validated_data.pop('wholesale_price')
            size = validated_data.pop('size', '')
            colors = validated_data.pop('colors', '')
            images = validated_data.pop('images', [])
            
            # Create product
            product = Product.objects.create(**validated_data)
            logger.info(f"Created product with ID: {product.id}")

            # Convert string representations to actual lists
            size_list = self._parse_array(size)
            colors_list = self._parse_array(colors)
            
            # Create product variant with wholesale price
            variant = ProductVariant.objects.create(
                wholesale_price=wholesale_price,
                size=size_list,
                colors=colors_list
            )
            logger.info(f"Created variant with ID: {variant.id}")
            
            # Add product to variant
            variant.product.add(product)
            logger.info(f"Linked product {product.id} to variant {variant.id}")

            # Handle images - FIXED HERE
            for image in images:
                try:
                    # Create ProductImage instance with the uploaded image
                    product_image = ProductImage.objects.create(images=image)
                    
                    # Add the image to the product's images
                    product.images.add(product_image)
                    logger.info(f"Added image to product {product.id}")
                except Exception as e:
                    logger.error(f"Failed to create product image: {e}")
            
            # Refresh the product instance to include images
            product.refresh_from_db()
            logger.info(f"Successfully created product: {product.name} (ID: {product.id})")
            return product
            
        except DjangoValidationError as e:
            logger.error(f"Error creating product: {str(e)}")
            # Re-raise with more specific error
            error_data = {
                "error": "Validation failed",
                "details": e.messages,
                "code": "validation_error"
            }
            raise serializers.ValidationError(error_data)
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            error_data = {
                "error": "Product creation failed",
                "details": "An unexpected error occurred. Please try again.",
                "code": "product_creation_error"
            }
            raise serializers.ValidationError(error_data)

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

class AdminProductListSerializer(BaseAdminProductSerializer):
    """Serializer for listing products (minimal fields)"""
    class Meta(BaseAdminProductSerializer.Meta):
        fields = [
            'id', 'sku', 'name', 'description', 'quantity', 'category', 
            'brand', 'subcategory', 'producttype',
            'wholesale_price', 'units_sold', 'stock_status', 'is_available',
            'upload_status', 'created_at', 'image_count', 'product_images', 'size', 'colors'
        ]

class AdminProductDetailSerializer(BaseAdminProductSerializer):
    """Detailed serializer for individual product view"""
    
    class Meta(BaseAdminProductSerializer.Meta):
        fields = BaseAdminProductSerializer.Meta.fields
        read_only_fields = ('id', 'sku', 'sales_count')

class AdminProductSerializer(serializers.ModelSerializer):
    """General admin product serializer for updates"""
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        required=False  # Make optional for updates
    )
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=SubCategories.objects.all(),
        required=False
    )
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        required=False
    )
    producttype = serializers.PrimaryKeyRelatedField(
        queryset=ProductTypes.objects.all(),
        required=False
    )
    wholesale_price = serializers.DecimalField(
        max_digits=11, 
        decimal_places=2, 
        required=False
    )
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False),
        required=False,
        write_only=True
    )
    size = serializers.CharField(required=False, allow_blank=True, write_only=True)
    colors = serializers.CharField(required=False, allow_blank=True, write_only=True)
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'quantity', 'category',
            'subcategory', 'brand', 'producttype', 'wholesale_price',
            'is_available', 'upload_status', 'images', 'size', 'colors'
        ]
        read_only_fields = ('id', 'sku')
        # Make all fields optional for updates
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'quantity': {'required': False},
            'is_available': {'required': False},
            'upload_status': {'required': False},
        }

    # def get_product_images(self, obj):
    #     """Return image URLs for read operations"""
    #     return [img.images.url for img in obj.images.all() if img.images]
    
    def update(self, instance, validated_data):
        # Extract special fields that need custom handling
        # new_images = validated_data.pop('images', None)
        new_images = validated_data.pop('images', [])
        wholesale_price = validated_data.pop('wholesale_price', None)
        size = validated_data.pop('size', None)
        colors = validated_data.pop('colors', None)
        
        # Handle image updates ONLY if new images are explicitly provided
        # if new_images:  # Changed from `is not None` to just check if truthy
        if new_images is not None:
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
        
        # Update variant fields
        variant = instance.product_variants.first()
        if variant is None:
            # Create new variant if none exists
            variant = ProductVariant.objects.create(
                wholesale_price=wholesale_price or 0,
                size=[],
                colors=[]
            )
            variant.product.add(instance)
        
        # Update wholesale_price if provided
        if wholesale_price is not None:
            variant.wholesale_price = wholesale_price
        
        # Update size if provided
        if size is not None:
            size_list = self._parse_array(size)
            variant.size = size_list
        
        # Update colors if provided
        if colors is not None:
            colors_list = self._parse_array(colors)
            variant.colors = colors_list
        
        # Save the variant if any changes were made
        if any([wholesale_price is not None, size is not None, colors is not None]):
            variant.save()
        
        # Update other product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance
        instance.save()
        return instance
    
    def _parse_array(self, value):
        """Convert string representation to list"""
        if not value:
            return []
        try:
            if value.startswith('[') and value.endswith(']'):
                return json.loads(value)
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in value.split(',') if item.strip()]

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