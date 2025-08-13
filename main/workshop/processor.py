import logging
from .exceptions import NotFoundError
from mall.models import CustomUser, Store
from urllib.parse import urlparse

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
         # First try exact match
         store = Store.objects.get(domain_name=domain_name)
         return store.id
      except Store.DoesNotExist:
         # If exact match fails, try matching by base domain (without query params)
         try:
            from urllib.parse import urlparse
            parsed_domain = urlparse(domain_name)
            base_domain = f"{parsed_domain.scheme}://{parsed_domain.netloc}"
            
            # Look for stores where the domain_name starts with the base domain
            store = Store.objects.filter(domain_name__startswith=base_domain).first()
            if store:
               logger.info(f"Found store by base domain match: {store.domain_name}")
               return store.id
            else:
               logger.error(f"No store found for domain: {domain_name} or base: {base_domain}")
               raise NotFoundError("Store Does Not Exist")
         except Exception as e:
            logger.error(f"Error parsing domain {domain_name}: {e}")
            logger.exception("Store Does Not Exist")
            raise NotFoundError("Store Does Not Exist")


   def get_store_id_by_params(self, store_id, user_id):
      try:
         store = Store.objects.get(owner=user_id, id=store_id)
         return store.id
      except Store.DoesNotExist:
         logger.exception("Store Does Not Exist")
         raise NotFoundError("Store Does Not Exist")