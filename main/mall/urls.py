from django.urls import path
from .views import SignInUserView

urlpatterns = [
    path("signin/", SignInUserView.as_view(), name="signin")
]
