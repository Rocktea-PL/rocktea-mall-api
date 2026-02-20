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
        if not (user.is_superuser or user.is_staff or user.is_active_admin):
            raise ValidationError("This user is not authorized as an admin.")
        
        # Get the first assigned role or use admin_role field
        assigned_roles = user.get_assigned_roles()
        if assigned_roles:
            admin_role = assigned_roles[0]  # Get first assigned role
        elif user.is_superuser:
            admin_role = 'super_admin'
        else:
            admin_role = user.admin_role if user.admin_role else None
        
        # Add additional response data if needed
        data['user_id'] = user.id
        data['email'] = user.email
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        data['is_superuser'] = user.is_superuser
        data['admin_role'] = admin_role
        data['is_active_admin'] = user.is_active_admin
        return data
   