from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import AdminTokenObtainPairSerializer

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer