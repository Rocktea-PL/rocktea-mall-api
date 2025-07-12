from rest_framework import serializers
from mall.serializers import StoreOwnerSerializer
from mall.models import CustomUser
from order.models import Store
from django.db.models import Sum, Count, Q

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'email', 'domain_name', 'completed', 
            'has_made_payment', 'created_at', 'logo', 'cover_image'
        ]
        extra_kwargs = {
            'logo': {'allow_null': True},
            'cover_image': {'allow_null': True},
            'domain_name': {'allow_null': True}
        }

# dropshippers/serializers.py
from rest_framework import serializers
from mall.models import CustomUser, Store
from django.db.models import Sum, Count, Q
from datetime import datetime, timezone
from django.utils.timezone import now

class DropshipperDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for dropshipper admin view"""
    company_name = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    total_products_available = serializers.SerializerMethodField()
    total_products_sold = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    is_active_user = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email', 'contact',
            'profile_image', 'is_store_owner', 'completed_steps', 'is_active',
            'is_verified', 'date_joined', 'last_active', 'total_products',
            'total_products_available', 'total_products_sold', 'total_revenue',
            'store', 'is_active_user', 'company_name'
        ]
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'profile_image': {'allow_null': True, 'required': False},
            'contact': {'allow_null': True},
            'username': {'allow_null': True},
            'first_name': {'allow_null': True},
            'last_name': {'allow_null': True},
            'email': {'allow_null': True}
        }
    
    def get_company_name(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return obj.owners.name
        return None
    
    def get_total_products(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return obj.owners.pricings.count()
        return 0
    
    def get_total_products_available(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return obj.owners.pricings.filter(
                product__is_available=True
            ).count()
        return 0
    
    def get_total_products_sold(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return obj.owners.store_orders.filter(
                status='Completed'
            ).aggregate(
                total=Sum('items__quantity')
            )['total'] or 0
        return 0
    
    def get_total_revenue(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return obj.owners.store_orders.filter(
                status='Completed'
            ).aggregate(
                total=Sum('total_price')
            )['total'] or 0.0
        return 0.0
    
    def get_last_active(self, obj):
        return obj.last_login.isoformat() if obj.last_login else None
    
    def get_is_active_user(self, obj):
        if obj.last_login:
            thirty_days_ago = now() - timezone.timedelta(days=30)
            return obj.last_login >= thirty_days_ago
        return False
    
    def get_store(self, obj):
        if hasattr(obj, 'owners') and obj.owners:
            return {
                'id': obj.owners.id,
                'name': obj.owners.name,
                'email': obj.owners.email,
                'domain_name': obj.owners.domain_name,
                'logo': obj.owners.logo.url if obj.owners.logo else None,
                'cover_image': obj.owners.cover_image.url if obj.owners.cover_image else None
            }
        return None
    
class DropshipperListSerializer(StoreOwnerSerializer):
    """Optimized serializer for list view with analytics"""
    total_products = serializers.IntegerField(read_only=True, allow_null=True)
    total_products_available = serializers.IntegerField(read_only=True, allow_null=True)
    total_products_sold = serializers.IntegerField(read_only=True, allow_null=True)
    total_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True,
        allow_null=True
    )
    last_active = serializers.DateTimeField(source='last_login', read_only=True, allow_null=True)
    is_active = serializers.BooleanField(allow_null=True)
    is_verified = serializers.BooleanField(allow_null=True)
    store = StoreSerializer(source='owners', read_only=True, allow_null=True)
    is_active_user = serializers.BooleanField(read_only=True, allow_null=True)
    profile_image = serializers.ImageField(allow_null=True)  # Add this

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'is_active', 'is_verified', 'date_joined', 'last_active',
            'total_products', 'total_products_available', 
            'total_products_sold', 'total_revenue', 'store', 'is_active_user'
        )
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'contact': {'allow_null': True},
            'username': {'allow_null': True},
            'first_name': {'allow_null': True},
            'last_name': {'allow_null': True},
            'email': {'allow_null': True},
            'profile_image': {'allow_null': True}
        }

class DropshipperAdminSerializer(StoreOwnerSerializer):
    company_name = serializers.CharField(write_only=True, required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True, allow_null=True)
    is_verified = serializers.BooleanField(default=True, allow_null=True)
    last_active = serializers.DateTimeField(source='last_login', read_only=True, allow_null=True)
    store = StoreSerializer(source='owners', read_only=True, allow_null=True)
    total_products = serializers.IntegerField(read_only=True, allow_null=True)
    total_products_available = serializers.IntegerField(read_only=True, allow_null=True)
    total_products_sold = serializers.IntegerField(read_only=True, allow_null=True)
    total_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True,
        allow_null=True
    )
    is_active_user = serializers.BooleanField(read_only=True, allow_null=True)
    profile_image = serializers.ImageField(allow_null=True)  # Add this

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'is_active', 'is_verified', 'company_name', 'date_joined', 
            'last_active', 'store', 'total_products', 'total_products_available',
            'total_products_sold', 'total_revenue', 'is_active_user'
        )
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_null': True},
            'contact': {'allow_null': True},
            'username': {'allow_null': True},
            'first_name': {'allow_null': True},
            'last_name': {'allow_null': True},
            'email': {'allow_null': True},
            'profile_image': {'allow_null': True}
        }

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', None)
        password = validated_data.pop('password', None)
        
        # Create user
        user = super().create(validated_data)
        
        # Set additional admin-managed fields
        user.is_store_owner = True
        user.is_active = validated_data.get('is_active', True)
        user.is_verified = validated_data.get('is_verified', True)
        
        if password:
            user.set_password(password)
        
        user.save()
        
        # Create store
        if company_name:
            Store.objects.create(
                owner=user,
                name=company_name,
                email=user.email,
                has_made_payment=True
            )
        
        return user