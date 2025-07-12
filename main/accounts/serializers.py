from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from mall.models import CustomUser
from django.db.models import Q
from workshop.exceptions import ValidationError

# Create your views here.
class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims for admin user
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Check if user has admin privileges
        if not (user.is_superuser or user.is_staff):
            raise ValidationError("This user is not authorized as an admin.")
        
        # Add additional response data if needed
        data['user_id'] = user.id
        data['email'] = user.email
        data['is_superuser'] = user.is_superuser
        return data
   