from django.urls import path, include
from .views import (
    AdminDashboardView,
    DropshipperAnalyticsView
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dropshipper-analytic/', DropshipperAnalyticsView.as_view(), name='admin-dashboard'),
]