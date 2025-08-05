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
    category = serializers.IntegerField(write_only=True, required=False, allow_null=True)

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
            'TIN_number', 'year_of_establishment', 'is_payment', 'category'
        )
        read_only_fields = ('completed_steps', 'date_joined')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_null': True},
            'first_name': {'allow_null': True},
            'last_name': {'allow_null': True},
            'email': {'allow_null': True},
            'profile_image': {'allow_null': True}
        }

    def validate(self, data):
        # Validate store fields if provided
        company_name = data.get('company_name')
        tin_number = data.get('TIN_number')
        
        if company_name and Store.objects.filter(name=company_name).exists():
            raise serializers.ValidationError({
                'company_name': 'A store with this name already exists.'
            })
        
        if tin_number and Store.objects.filter(TIN_number=tin_number).exists():
            raise serializers.ValidationError({
                'TIN_number': 'A store with this TIN number already exists.'
            })
        
        return data

    def create(self, validated_data):
        # Extract store-related fields safely
        store_fields = {
            'company_name': validated_data.pop('company_name', None),
            'tin_number': validated_data.pop('TIN_number', None),
            'logo': validated_data.pop('logo', None),
            'year': validated_data.pop('year_of_establishment', None),
            'is_payment': validated_data.pop('is_payment', False),
            'category': validated_data.pop('category', None)
        }
        
        # Extract user fields
        password = validated_data.pop('password', None)
        contact = validated_data.pop('contact', None)
        username = validated_data.pop('username', None)

        try:
            with transaction.atomic():
                # Generate unique username if not provided
                if not username:
                    base_username = validated_data.get('email', '').split('@')[0]
                    username = base_username
                    counter = 1
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                
                # Create user with basic fields including profile_image
                user = CustomUser.objects.create(
                    first_name=validated_data.get('first_name', ''),
                    last_name=validated_data.get('last_name', ''),
                    email=validated_data.get('email'),
                    username=username,
                    contact=contact,
                    profile_image=validated_data.get('profile_image'),
                    is_store_owner=True,
                    is_active=True,
                    is_verified=True,
                    completed_steps=4
                )
                
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
                        has_made_payment=store_fields['is_payment'],
                        category_id=store_fields['category']
                    )
                
                # Send welcome email
                transaction.on_commit(lambda: self._send_welcome_email(user))
                    
        except IntegrityError as e:
            error_msg = str(e).lower()
            if 'email' in error_msg:
                raise serializers.ValidationError({
                    'email': 'A user with this email already exists.'
                })
            elif 'contact' in error_msg:
                raise serializers.ValidationError({
                    'contact': 'A user with this contact number already exists.'
                })
            elif 'username' in error_msg:
                raise serializers.ValidationError({
                    'username': 'A user with this username already exists.'
                })
            elif 'name' in error_msg:
                raise serializers.ValidationError({
                    'company_name': 'A store with this name already exists.'
                })
            else:
                raise serializers.ValidationError({
                    'non_field_errors': ['This data already exists in the system.']
                })
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })

        return user

    def update(self, instance, validated_data):
        # Validate store fields for update
        company_name = validated_data.get('company_name')
        tin_number = validated_data.get('TIN_number')
        
        if company_name:
            existing_store = Store.objects.filter(name=company_name).exclude(
                owner=instance
            ).first()
            if existing_store:
                raise serializers.ValidationError({
                    'company_name': 'A store with this name already exists.'
                })
        
        if tin_number:
            existing_store = Store.objects.filter(TIN_number=tin_number).exclude(
                owner=instance
            ).first()
            if existing_store:
                raise serializers.ValidationError({
                    'TIN_number': 'A store with this TIN number already exists.'
                })
        
        # Extract store-related fields safely
        store_fields = {
            'company_name': validated_data.pop('company_name', None),
            'tin_number': validated_data.pop('TIN_number', None),
            'logo': validated_data.pop('logo', None),
            'year': validated_data.pop('year_of_establishment', None),
            'is_payment': validated_data.pop('is_payment', None),
            'category': validated_data.pop('category', None)
        }
        
        # Extract user fields
        password = validated_data.pop('password', None)
        contact = validated_data.pop('contact', None)
        username = validated_data.pop('username', None)

        try:
            with transaction.atomic():
                # Handle username uniqueness if provided
                if username and username != instance.username:
                    if CustomUser.objects.filter(username=username).exclude(id=instance.id).exists():
                        raise serializers.ValidationError({
                            'username': 'A user with this username already exists.'
                        })
                    instance.username = username
                
                # Update user fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                
                if contact:
                    instance.contact = contact
                if password:
                    instance.set_password(password)
                
                instance.save()

                # Update or create store if company name provided
                if store_fields['company_name']:
                    if hasattr(instance, 'owners') and instance.owners:
                        # Update existing store
                        store = instance.owners
                        store.name = store_fields['company_name']
                        if store_fields['tin_number'] is not None:
                            store.TIN_number = store_fields['tin_number']
                        if store_fields['logo'] is not None:
                            store.logo = store_fields['logo']
                        if store_fields['year'] is not None:
                            store.year_of_establishment = store_fields['year']
                        if store_fields['is_payment'] is not None:
                            store.has_made_payment = store_fields['is_payment']
                        if store_fields['category'] is not None:
                            store.category_id = store_fields['category']
                        store.save()
                    else:
                        # Create new store
                        Store.objects.create(
                            owner=instance,
                            name=store_fields['company_name'],
                            TIN_number=store_fields['tin_number'],
                            logo=store_fields['logo'],
                            year_of_establishment=store_fields['year'],
                            has_made_payment=store_fields['is_payment'] or False,
                            category_id=store_fields['category']
                        )
                    
        except IntegrityError as e:
            error_msg = str(e).lower()
            if 'email' in error_msg:
                raise serializers.ValidationError({
                    'email': 'A user with this email already exists.'
                })
            elif 'contact' in error_msg:
                raise serializers.ValidationError({
                    'contact': 'A user with this contact number already exists.'
                })
            elif 'username' in error_msg:
                raise serializers.ValidationError({
                    'username': 'A user with this username already exists.'
                })
            elif 'name' in error_msg:
                raise serializers.ValidationError({
                    'company_name': 'A store with this name already exists.'
                })
            else:
                raise serializers.ValidationError({
                    'non_field_errors': ['This data already exists in the system.']
                })
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })

        return instance

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