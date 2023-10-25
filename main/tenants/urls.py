from django.urls import path
from .views import LoginStoreUser

urlpatterns = [
   path("login/", LoginStoreUser.as_view(), name="store-login")
]
