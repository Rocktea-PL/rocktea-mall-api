import logging
from .exceptions import NotFoundError
from mall.models import CustomUser, Store

logger = logging.getLogger(__name__)


class DomainNameHandler:
   def __init__(self):
      pass

   def process_request(self, store_domain=None, mall_id=None, user_id=None):
      if store_domain is None and mall_id and user_id is not None:
         return self.get_store_id_by_params(mall_id, user_id)
      else:
         return self.get_store_id_by_domain_name(store_domain)


   def get_store_id_by_domain_name(self, domain_name):
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