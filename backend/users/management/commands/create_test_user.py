from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for development'
    
    def add_arguments(self, parser):
        parser.add_argument('--admin', action='store_true', help='Create admin user')
        parser.add_argument('--regular', action='store_true', help='Create regular user')
        parser.add_argument('--all', action='store_true', help='Create all test users')
    
    def handle(self, *args, **options):
        if options['admin'] or options['all']:
            self.create_admin_user()
        
        if options['regular'] or options['all']:
            self.create_regular_user()
    
    def create_admin_user(self):
        try:
            admin_user = User.objects.create_superuser(
                email='admin@trojandefender.com',
                password='TrojanDefender2024!',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Admin user created: {admin_user.email}\n'
                    f'Password: TrojanDefender2024!\n'
                    f'Admin URL: http://localhost:8000/admin/'
                )
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )
    
    def create_regular_user(self):
        try:
            regular_user = User.objects.create_user(
                email='test@trojandefender.com',
                password='TestUser2024!',
                first_name='Test',
                last_name='User',
                organization='Test Organization'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Regular user created: {regular_user.email}\n'
                    f'Password: TestUser2024!'
                )
            )
        except IntegrityError:
            self.stdout.write(
                self.style.WARNING('Regular user already exists')
            )