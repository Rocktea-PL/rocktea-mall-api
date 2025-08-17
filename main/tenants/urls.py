from django.urls import path
from .views import LoginStoreUser, UpdateProfile

urlpatterns = [
   path("login/", LoginStoreUser.as_view(), name="store-login"),
   path("profile/update/", UpdateProfile.as_view(), name="update-profile")
]
