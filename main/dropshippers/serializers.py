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
    """Detailed serializer for dropshipper admin view"""
    company_name = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    total_products_available = serializers.SerializerMethodField()
    total_products_sold = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    is_active_user = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    
    def update(self, instance, validated_data):
        # Check if DNS updates should be skipped
        skip_dns_update = self.context.get('skip_dns_update', False)
        
        # Handle profile image deletion safely
        new_profile_image = validated_data.get('profile_image')
        if 'profile_image' in validated_data and new_profile_image != instance.profile_image:
            if instance.profile_image:
                try:
                    instance.profile_image.delete(save=False)
                except Exception as e:
                    print(f"Cloudinary deletion error during profile image update: {e}")
        
        # Update user fields
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
                'email': obj.owners.owner.email,
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
        company_name = validated_data.pop('company_name', None)
        password     = validated_data.pop('password', None)
        tin_number   = validated_data.pop('TIN_number', None)
        logo         = validated_data.pop('logo', None)
        year         = validated_data.pop('year_of_establishment', None)
        is_payment   = validated_data.pop('is_payment', False)
        contact      = validated_data.pop('contact', None)
        username     = validated_data.pop('username', None)

        user = None
        store = None
        
        try:
            with transaction.atomic():
                # build the user **without** calling super().create
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

                # Only create store if company_name is provided
                if company_name:
                    store = Store.objects.create(
                        owner=user,
                        name=company_name,
                        TIN_number=tin_number,
                        logo=logo,
                        year_of_establishment=year,
                        has_made_payment=is_payment
                    )
                    
                # Only send email if both user and store creation were successful
                # Schedule email after transaction commits to ensure data consistency
                if store:
                    transaction.on_commit(lambda: self.send_admin_created_email(user))
                    
        except IntegrityError as e:
            if 'duplicate key value violates unique constraint "mall_store_name_key"' in str(e):
                raise serializers.ValidationError({'company_name': 'A store with this name already exists.'})
            raise
        except Exception as e:
            raise serializers.ValidationError({'non_field_errors': [str(e)]})

        return user

    def send_admin_created_email(self, user):

        try:
            subject = "Welcome to Rocktea Mall - Your Account is Ready!"
            context = {
                'full_name': user.get_full_name() or user.first_name or user.email,
                'store_domain': 'Pending setup',
                'support_email': 'support@yourockteamall.com',
                'current_year': timezone.now().year,
                'owner_email': user.email,
                'is_local': False,
            }
            sendEmail(
                recipientEmail=user.email,
                template_name='emails/admin_created_account.html',
                context=context,
                subject=subject,
                tags=["admin-created-account", "account-setup"]
            )
        except Exception as e:
            # Log but don't prevent user creation
            print(f"Failed to send admin created email: {str(e)}")
            logger.error(f"Failed to send admin created email to {user.email}: {str(e)}")