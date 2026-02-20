from django.core.management.base import BaseCommand
from mall.models import CustomUser
from mall.admin_roles import AdminUserRole, AdminCustomPermission
from mall.admin_audit import AdminAuditLog

class Command(BaseCommand):
    help = 'Delete a user and all related records'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email of the user to delete')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            user_id = user.id
            
            self.stdout.write(f'Deleting user: {user.email} ({user.first_name} {user.last_name})')
            
            # Delete related records
            AdminAuditLog.objects.filter(admin_user=user).delete()
            self.stdout.write('  - Deleted audit logs')
            
            AdminUserRole.objects.filter(user=user).delete()
            AdminUserRole.objects.filter(assigned_by=user).delete()
            self.stdout.write('  - Deleted user roles')
            
            AdminCustomPermission.objects.filter(user=user).delete()
            AdminCustomPermission.objects.filter(assigned_by=user).delete()
            self.stdout.write('  - Deleted custom permissions')
            
            # Delete products created by this user
            products_count = user.created_products.count()
            user.created_products.all().delete()
            self.stdout.write(f'  - Deleted {products_count} products')
            
            # Delete the user
            user.delete()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted user: {email}'))
            
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User not found: {email}'))
