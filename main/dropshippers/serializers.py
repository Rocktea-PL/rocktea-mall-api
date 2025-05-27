from rest_framework import serializers
from mall.serializers import StoreOwnerSerializer
from mall.models import CustomUser
from order.models import Store

class DropshipperAdminSerializer(StoreOwnerSerializer):
    company_name = serializers.CharField(write_only=True)
    is_active = serializers.BooleanField(default=True)
    is_verified = serializers.BooleanField(default=True)

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'is_active', 'is_verified', 'company_name'
        )
        read_only_fields = ('completed_steps',)
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