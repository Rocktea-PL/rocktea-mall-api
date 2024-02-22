from .models import Store, CustomUser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers


class DomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extracting the domain name from the request
        domain_name = request.META.get('HTTP_HOST', None)
        # print("Domain Name: ", domain_name)  # Add this line for debugging

        validated_domain_name = self._validate_domain_name(
            domain_name, request)

        # Storing the domain name in request object for further use
        request.domain_name = validated_domain_name

        response = self.get_response(request)

        return response

    def _validate_domain_name(self, domain_name, request):
        # print("DOME " + str(domain_name))
        """
        Verify that the user logged into that account is the owner of the account by matching the Store Domain name to the Registered Store Owner.
        """
        
        user_id = request.GET.get("mallcli")
        store_id = request.GET.get("mall")

        if user_id is None:
            # Return None or some default value to indicate that user_id is not found
            return None

        try:
            verified_user = get_object_or_404(CustomUser, id=user_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Sorry, This User does not exist!")

        if verified_user.is_store_owner:
            try:
                store = Store.objects.get(owner=verified_user, id=store_id)
            except Store.DoesNotExist:
                raise serializers.ValidationError("This User Does Not Own this Store")
            # print(store.id)
            return store.id
            

        # verified_user.is_consumer:
        return self.get_consumer_associated_domain(domain_name, request)

    def get_consumer_associated_domain(self, domain_name, request):
        """
        Match Associated Domain with user ID
        """
        try:
            associated_domain = Store.objects.get(domain_name=domain_name)
            return associated_domain.id
        except Store.DoesNotExist:
            raise serializers.ValidationError("Store Does Not Exist for this Domain")