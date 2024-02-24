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
        store_domain = request.META.get('HTTP_ORIGIN', None)
        logger.debug("Domain Name: %s", store_domain)

        # Extracting parameters from the request
        mall_id = request.GET.get("mall", None)
        user_id = request.GET.get("mallcli", None)

        # Validating input parameters
        if mall_id is not None and user_id is not None:
            store = self.get_store_id_by_params(mall_id, user_id)
            request.mall_id = store
            
        elif mall_id is not None and user_id is None:
            mall = self.get_store(mall_id)
            request.mall = mall
            
        elif mall_id is None and user_id is not None:
            user = self.get_user(user_id)
            request.user_id = user
    
        else:
            store_id = self.get_store_id_by_domain_name(store_domain)
            request.store_domain = store_id

        return self.get_response(request)

    def get_store_id_by_domain_name(self, domain_name):
        # print(domain_name)
        try:
            store = Store.objects.get(domain_name=domain_name)
            return store.id
        except Store.DoesNotExist:
            logger.exception("Store Does Not Exist")
            raise NotFoundError("Store Does Not Exist")

    def get_store_id_by_params(self, store_id, user_id):
        try:
            store = Store.objects.get(owner=user_id, id=store_id)
            return store.id
        except Store.DoesNotExist:
            logger.exception("Store Does Not Exist")
            raise NotFoundError("Store Does Not Exist")
        
    def get_store(self, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            raise NotFoundError("Store Does Not Exist")
        return store.id

    def get_user(self, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise NotFoundError("Store Does Not Exist")
        return user.id