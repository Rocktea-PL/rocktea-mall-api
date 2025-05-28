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

class DropshipperListSerializer(StoreOwnerSerializer):
    """Optimized serializer for list view with analytics"""
    total_products = serializers.IntegerField(read_only=True)
    total_products_available = serializers.IntegerField(read_only=True)
    total_products_sold = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    last_active = serializers.DateTimeField(source='last_login', read_only=True)
    is_active = serializers.BooleanField()
    is_verified = serializers.BooleanField()
    store = StoreSerializer(source='owners', read_only=True)
    is_active_user = serializers.BooleanField(read_only=True)

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'is_active', 'is_verified', 'date_joined', 'last_active',
            'total_products', 'total_products_available', 
            'total_products_sold', 'total_revenue', 'store', 'is_active_user'
        )
        read_only_fields = ('completed_steps', 'date_joined')

class DropshipperAdminSerializer(StoreOwnerSerializer):
    company_name = serializers.CharField(write_only=True, required=False)
    is_active = serializers.BooleanField(default=True)
    is_verified = serializers.BooleanField(default=True)
    last_active = serializers.DateTimeField(source='last_login', read_only=True)
    store = StoreSerializer(source='owners', read_only=True)
    total_products = serializers.IntegerField(read_only=True)
    total_products_available = serializers.IntegerField(read_only=True)
    total_products_sold = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    is_active_user = serializers.BooleanField(read_only=True)

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'is_active', 'is_verified', 'company_name', 'date_joined', 
            'last_active', 'store', 'total_products', 'total_products_available',
            'total_products_sold', 'total_revenue', 'is_active_user'
        )
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
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