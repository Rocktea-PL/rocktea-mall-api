from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a true superuser with full system privileges'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email address for the superuser')
        parser.add_argument('--password', required=True, help='Password for the superuser')
        parser.add_argument('--first-name', help='First name')
        parser.add_argument('--last-name', help='Last name')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')
        
        user_data = {
            'email': email,
            'first_name': options.get('first_name', ''),
            'last_name': options.get('last_name', ''),
        }
        
        user = User.objects.create_true_superuser(
            password=password,
            **user_data
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'True superuser created successfully: {user.email} (ID: {user.id})'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'WARNING: This user has full system privileges. Use with caution.'
            )
        )