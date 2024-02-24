import logging
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import CustomUser, Store
from workshop.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class DomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        store_domain = request.META.get('HTTP_HOST', None)
        logger.debug("Domain Name: %s", store_domain)
        
        # Users
        mall_id = request.GET.get("mall", None)
        user_id = request.GET.get("mallcli", None)
        
        if mall_id and user_id is not None:
            store = self.get_store_id_by_params(mall_id, user_id)
            request.mall_id = store
        else:
            store_id = self.get_store_id_by_domain_name(store_domain)
            request.store_domain = store_id
        
        return self.get_response(request)
    
    def get_store_id_by_domain_name(self, domain_name):
        try:
            store = Store.objects.get(domain_name=domain_name)
        except Store.DoesNotExist:
            raise NotFoundError("Store Does Not Exist")

        return store.id
    
    def get_store_id_by_params(self, store_id, user_id):
        try:
            store = Store.objects.get(owner=user_id, id=store_id)
        except Store.DoesNotExist:
            logger.error("Store Does Not Exist")
            raise NotFoundError("Store Does Not Exist")
        return store.id

    

class MallCliMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        store_id = request.GET.get("mall")
        user_id = request.GET.get("mallcli")
        
        store_id = self.get_store_id_by_params(store_id, user_id)
        request.user_store_id = store_id
        return self.get_response(request)
        
        
    def get_store_id_by_params(self, store_id, user_id):
        try:
            store = Store.objects.get(owner=user_id, id=store_id)
        except Store.DoesNotExist:
            logger.error("Store Does Not Exist")
            raise NotFoundError("Store Does Not Exist")
        return store.id







# class DomainNameMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         domain_name = request.META.get('HTTP_HOST', None)
#         logger.debug("Domain Name: %s", domain_name)

#         validated_domain_name = self._validate_domain_name(
#             domain_name, request)
#         request.domain_name = validated_domain_name
#         return self.get_response(request)

#     def _validate_domain_name(self, domain_name, request):
#         user_id = request.GET.get("mallcli")
#         store_id = request.GET.get("mall")

#         if user_id is None:
#             logger.warning("User ID not found in request.")
#             return None

#         try:
#             verified_user = get_object_or_404(CustomUser, id=user_id)
#         except ObjectDoesNotExist:
#             logger.error("User with ID %s does not exist.", user_id)
#             raise serializers.ValidationError(
#                 "Sorry, This User does not exist!")

#         if verified_user.is_store_owner:
#             return self._validate_store_owner(verified_user, store_id)

#         return self._validate_consumer_associated_domain(domain_name, user_id)

#     def _validate_store_owner(self, verified_user, store_id):
#         try:
#             store = get_object_or_404(Store, owner=verified_user, id=store_id)
#             return store.id
#         except ObjectDoesNotExist:
#             logger.error("User does not own the store with ID %s.", store_id)
#             raise serializers.ValidationError(
#                 "This User Does Not Own this Store")

#     def _validate_consumer_associated_domain(self, domain_name, user_id):
#         try:
#             store = Store.objects.get(
#                 domain_name=domain_name, owner_id=user_id)
#             return store.id
#         except Store.DoesNotExist:
#             logger.error(
#                 "Store with domain name %s or user with ID %s does not exist.", domain_name, user_id)
#             raise serializers.ValidationError("Store or User Does Not Exist")