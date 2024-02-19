from .models import Store, CustomUser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers


class DomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extracting the domain name from the request
        domain_name = request.META.get('HTTP_ORIGIN', None)

        validated_domain_name = self._validate_domain_name(
            domain_name, request)

        # Storing the domain name in request object for further use
        request.domain_name = validated_domain_name

        response = self.get_response(request)

        return response

    def _validate_domain_name(self, domain_name, request):
        """
        Verify that the user logged into that account is the owner of the account by matching the Store Domain name to the Registered Store Owner.
        """
        user_id = request.COOKIES.get('user_id')
        store_id = request.COOKIES.get('StoreId')

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
            

        elif verified_user.is_consumer:
            return self.get_consumer_associated_domain(domain_name, verified_user, request)

    def get_consumer_associated_domain(self, domain_name, user_id, request):
        """
        Match Associated Domain with user ID
        """
        try:
            associated_domain = get_object_or_404(
                Store, domain_name=domain_name)
            store = CustomUser.objects.filter(id=user_id, domain_name=domain_name).first()
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Store or User Does Not Exist")
        return store.id