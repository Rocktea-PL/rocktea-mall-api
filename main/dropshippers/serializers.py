from rest_framework import serializers
from mall.serializers import StoreOwnerSerializer
from order.models import Store
from django.db.models import Sum
from mall.models import CustomUser, Store
from django.utils import timezone
from django.utils.timezone import now
from django.db import transaction, IntegrityError
from setup.utils import sendEmail
import logging

logger = logging.getLogger(__name__)

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'domain_name', 'completed', 
            'has_made_payment', 'created_at', 'logo', 'cover_image',
            'TIN_number', 'year_of_establishment'
        ]
        extra_kwargs = {
            'logo': {'allow_null': True},
            'cover_image': {'allow_null': True},
            'domain_name': {'allow_null': True},
            'TIN_number': {'allow_null': True},
            'year_of_establishment': {'allow_null': True}
        }

class DropshipperDetailSerializer(serializers.ModelSerializer):
    """Optimized detailed serializer using annotated fields"""
    company_name = serializers.CharField(source='owners.name', read_only=True)
    
    # Use annotated fields from queryset instead of SerializerMethodField
    total_products = serializers.IntegerField(read_only=True)
    total_products_available = serializers.IntegerField(read_only=True)
    total_products_sold = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_active_user = serializers.BooleanField(read_only=True)
    
    last_active = serializers.DateTimeField(source='last_login', read_only=True)
    store = StoreSerializer(source='owners', read_only=True)
    
    def update(self, instance, validated_data):
        # Handle profile image deletion safely
        new_profile_image = validated_data.get('profile_image')
        if 'profile_image' in validated_data and new_profile_image != instance.profile_image:
            if instance.profile_image:
                try:
                    instance.profile_image.delete(save=False)
                except Exception as e:
                    logger.warning(f"Profile image deletion error: {e}")
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
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
    

    
class DropshipperListSerializer(serializers.ModelSerializer):
    """Optimized list serializer using annotated fields"""
    # Use annotated fields from queryset
    total_products = serializers.IntegerField(read_only=True)
    total_products_available = serializers.IntegerField(read_only=True)
    total_products_sold = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_active_user = serializers.BooleanField(read_only=True)
    
    last_active = serializers.DateTimeField(source='last_login', read_only=True)
    store = StoreSerializer(source='owners', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'contact',
            'profile_image', 'is_active', 'is_verified', 'date_joined',
            'last_active', 'total_products', 'total_products_available', 
            'total_products_sold', 'total_revenue', 'store', 'is_active_user'
        ]

class DropshipperAdminSerializer(StoreOwnerSerializer):
    company_name = serializers.CharField(write_only=True, required=False, allow_null=True)
    TIN_number = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    logo = serializers.ImageField(write_only=True, required=False, allow_null=True)
    year_of_establishment = serializers.DateField(write_only=True, required=False, allow_null=True)
    is_payment = serializers.BooleanField(write_only=True, default=False)
    contact = serializers.CharField(write_only=True, required=False, allow_null=True)
    username = serializers.CharField(write_only=True, required=False, allow_null=True)

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
    profile_image = serializers.ImageField(allow_null=True)

    class Meta(StoreOwnerSerializer.Meta):
        fields = StoreOwnerSerializer.Meta.fields + (
            'company_name', 'date_joined', 'logo', 'contact', 'username',
            'last_active', 'store', 'total_products', 'total_products_available',
            'total_products_sold', 'total_revenue', 'is_active_user',
            'TIN_number', 'year_of_establishment', 'is_payment'
        )
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_null': True},
            'first_name': {'allow_null': True},
            'last_name': {'allow_null': True},
            'email': {'allow_null': True},
            'profile_image': {'allow_null': True}
        }

    def create(self, validated_data):
        # Extract store-related fields
        store_fields = {
            'company_name': validated_data.pop('company_name', None),
            'tin_number': validated_data.pop('TIN_number', None),
            'logo': validated_data.pop('logo', None),
            'year': validated_data.pop('year_of_establishment', None),
            'is_payment': validated_data.pop('is_payment', False)
        }
        
        # Extract user fields
        password = validated_data.pop('password', None)
        contact = validated_data.pop('contact', None)
        username = validated_data.pop('username', None)

        try:
            with transaction.atomic():
                # Create user
                user = CustomUser(**validated_data)
                user.is_store_owner = True
                user.is_active = True
                user.is_verified = True
                
                if username:
                    user.username = username
                if contact:
                    user.contact = contact
                if password:
                    user.set_password(password)
                
                user.save()

                # Create store if company name provided
                store = None
                if store_fields['company_name']:
                    store = Store.objects.create(
                        owner=user,
                        name=store_fields['company_name'],
                        TIN_number=store_fields['tin_number'],
                        logo=store_fields['logo'],
                        year_of_establishment=store_fields['year'],
                        has_made_payment=store_fields['is_payment']
                    )
                    
                # Schedule welcome email
                if store:
                    transaction.on_commit(lambda: self._send_welcome_email(user))
                    
        except IntegrityError as e:
            if 'mall_store_name_key' in str(e):
                raise serializers.ValidationError({
                    'company_name': 'A store with this name already exists.'
                })
            raise
        except Exception as e:
            raise serializers.ValidationError({'non_field_errors': [str(e)]})

        return user

    def _send_welcome_email(self, user):
        """Send welcome email asynchronously"""
        try:
            sendEmail(
                recipientEmail=user.email,
                template_name='emails/admin_created_account.html',
                context={
                    'full_name': user.get_full_name() or user.email,
                    'store_domain': 'Pending setup',
                    'support_email': 'support@yourockteamall.com',
                    'current_year': timezone.now().year,
                    'owner_email': user.email,
                    'is_local': False,
                },
                subject="Welcome to Rocktea Mall - Your Account is Ready!",
                tags=["admin-created-account", "account-setup"]
            )
        except Exception as e:
            logger.error(f"Failed to send admin welcome email to {user.email}: {e}")