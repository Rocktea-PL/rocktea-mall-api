from mall.models import Store
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.serializers import ValidationError
from rest_framework import response, status


def get_store_instance(request):
   """Get Store ID using Store Domain Name """
   store_domain = request.domain_name
   try:
      store = get_object_or_404(Store, domain_name=store_domain)
   except Http404:
      raise ValidationError("Store Does Not Exist")
   return store.id
