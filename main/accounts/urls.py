from django.urls import path
from .views import AdminTokenObtainPairView

urlpatterns = [
    path('admin/login', AdminTokenObtainPairView.as_view(), name='admin_login'),
]