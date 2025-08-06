from mall.models import CustomUser, Store
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from django.shortcuts import get_object_or_404
from workshop.processor import DomainNameHandler
from setup.utils import sendEmail
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urlparse
from django.urls import reverse
from django.utils import timezone

# Generate verification token and send email
from django.contrib.auth.tokens import PasswordResetTokenGenerator

# Send verification email in background
from threading import Thread

from setup.utils import get_store_domain

import logging  # Add this import at the top of your file

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)  # Set the logging level

handler = DomainNameHandler()

class StoreUserSignUpSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)
    store_id = serializers.UUIDField(required=False, write_only=True, help_text="Store ID for user registration")

    class Meta:
        model = CustomUser
        fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_consumer", "associated_domain", "password", "store_id")
        read_only_fields = ("username", "is_consumer", "associated_domain", "is_verified")

    def validate_password(self, value):
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', value):
            raise serializers.ValidationError("Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        store_instance = None
        
        # Method 1: Check for store_id in request data or query params
        request = self.context['request']
        store_id = request.data.get('store_id') or request.query_params.get('mallcli')
        
        if store_id:
            try:
                store_instance = Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                pass
        
        # Method 2: Extract from referer URL if store_id not provided
        if not store_instance:
            referer = request.META.get('HTTP_REFERER', '')
            if referer:
                # Extract mallcli parameter from referer
                import re
                mallcli_match = re.search(r'mallcli=([^&]+)', referer)
                if mallcli_match:
                    try:
                        store_instance = Store.objects.get(id=mallcli_match.group(1))
                    except Store.DoesNotExist:
                        pass
                
                # Extract from subdomain if mallcli not found
                if not store_instance:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(referer)
                    hostname = parsed_url.hostname
                    if hostname and hostname != 'localhost':
                        # Extract subdomain (e.g., tulbadex-stores from tulbadex-stores.user-dev.yourockteamall.com)
                        parts = hostname.split('.')
                        if len(parts) > 2:  # Has subdomain
                            subdomain = parts[0]
                            try:
                                store_instance = Store.objects.get(slug=subdomain)
                            except Store.DoesNotExist:
                                pass

        user = CustomUser.objects.create(
            associated_domain=store_instance,
            is_verified=True,  # User can't login until verified
            **validated_data
        )

        user.is_consumer = True

        if password:
            user.set_password(password)
            user.save()

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        user.verification_token = token
        user.save()
        firstName = user.get_full_name() or user.email

        def send_verification_email():
            try:
                sendStoreWelcomeEmail(
                    token=token,
                    email=user.email,
                    firstName=firstName,
                    store=store_instance,
                    request=self.context['request']
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")

        # Start email sending in background thread
        email_thread = Thread(target=send_verification_email)
        email_thread.start()
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)  # Remove the password field from the response
        return representation

class UserLogin(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token

    def get_store(self, user):
        store_id = self.context['request'].query_params.get('store_id')
        
        if store_id:
            try:
                return Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                raise serializers.ValidationError({'error': 'Store not found'})
        elif user.associated_domain:
            return user.associated_domain
        else:
            return None

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Check if user exists and password is correct
        try:
            user = CustomUser.objects.get(email=email)
            if not user.check_password(password):
                from workshop.exceptions import ValidationError
                raise ValidationError("Invalid credentials. Please check your email and password.")
        except CustomUser.DoesNotExist:
            from workshop.exceptions import ValidationError
            raise ValidationError("Invalid credentials. Please check your email and password.")
        
        # Call parent validate to get tokens
        data = super().validate(attrs)
        
        # Check if user is verified
        if not self.user.is_verified:
            from workshop.exceptions import ValidationError
            raise ValidationError("Email not verified. Please check your email for verification link.")
      
        if not self.user.is_consumer:
            from workshop.exceptions import ValidationError
            raise ValidationError("User is not a consumer")

        store = self.get_store(self.user)
        
        user_data = {
                "id": self.user.id,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email,
                "username": self.user.username,
                "contact": str(self.user.contact),
                "is_store_owner": self.user.is_store_owner,
                "is_verified": self.user.is_verified,
            }

        if store:
            user_data['store_data'] = {
                "store": store.name,
                "id": store.id,
            }

        data['user_data'] = user_data

        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        return data
   

def sendStoreWelcomeEmail(token, email, firstName, store, request):
    # Get verification URL (keep for backend processing but don't show in email)
    referer = request.META.get('HTTP_REFERER')
    if referer and 'swagger' not in referer.lower():
        parsed_referer = urlparse(referer)
        verification_url = f"{parsed_referer.scheme}://{parsed_referer.netloc}/verify-email/?token={token}"
        store_url = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
    else:
        current_site = get_current_site(request).domain
        relativeLink = reverse('verify-email')
        verification_url = 'http://'+ current_site+relativeLink+"?token="+str(token)
        store_url = f"http://{current_site}"
    
    try:
        subject = f"Welcome to {store.name if store else 'RockTeaMall'} - Your Account is Ready!"
        context = {
            'full_name': firstName,
            'store_name': store.name if store else 'RockTeaMall',
            'store_url': store_url,
            'store_domain': store.domain_name if store else store_url,
            'verification_url': verification_url,  # Keep for backend but hidden in template
            'current_year': timezone.now().year,
            'support_email': 'support@yourockteamall.com',
         }
        
        from setup.utils import sendEmail
        sendEmail(
            recipientEmail=email,
            template_name='emails/store_user_welcome.html',
            context=context,
            subject=subject,
            tags=["user-registration", "store-welcome", "user-onboarding"]
        )
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return None