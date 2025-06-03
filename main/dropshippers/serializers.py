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