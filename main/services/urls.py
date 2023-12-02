from .views import SignInServicesView
from django.urls import path


urlpatterns = [
   path('login', SignInServicesView.as_view(), name='services')
]