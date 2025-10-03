from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

User = get_user_model()
security_logger = logging.getLogger('django.security')


class Command(BaseCommand):
    help = 'Perform security audit and generate security report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for the report'
        )

    def handle(self, *args, **options):
        days = options['days']
        output_file = options.get('output')
        
        self.stdout.write(self.style.SUCCESS(f'Starting security audit for the last {days} days...'))
        
        # Analyze user accounts
        self.audit_user_accounts()
        
        # Analyze login patterns
        self.audit_login_patterns(days)
        
        # Check for security violations
        self.check_security_violations(days)
        
        # Generate recommendations
        self.generate_recommendations()
        
        self.stdout.write(self.style.SUCCESS('Security audit completed successfully!'))

    def audit_user_accounts(self):
        """Audit user accounts for security issues."""
        self.stdout.write('\n=== USER ACCOUNT AUDIT ===')
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Active users: {active_users}')
        self.stdout.write(f'Staff users: {staff_users}')
        self.stdout.write(f'Superusers: {superusers}')
        
        # Check for inactive superusers
        inactive_superusers = User.objects.filter(is_superuser=True, is_active=False)
        if inactive_superusers.exists():
            self.stdout.write(
                self.style.WARNING(f'Found {inactive_superusers.count()} inactive superuser(s)')
            )
        
        # Check for users without recent login
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stale_users = User.objects.filter(
            last_login__lt=thirty_days_ago,
            is_active=True
        ).exclude(last_login__isnull=True)
        
        if stale_users.exists():
            self.stdout.write(
                self.style.WARNING(f'Found {stale_users.count()} users with no login in 30+ days')
            )

    def audit_login_patterns(self, days):
        """Audit login patterns for anomalies."""
        self.stdout.write('\n=== LOGIN PATTERN AUDIT ===')
        
        # This would require parsing log files or implementing login tracking
        # For now, we'll provide a framework
        self.stdout.write('Login pattern analysis would require log parsing implementation')
        
        # Example of what could be implemented:
        # - Failed login attempts by IP
        # - Successful logins from new locations
        # - Multiple concurrent sessions
        # - Login attempts outside business hours

    def check_security_violations(self, days):
        """Check for security violations in logs."""
        self.stdout.write('\n=== SECURITY VIOLATIONS CHECK ===')
        
        # This would parse security logs for violations
        self.stdout.write('Security violation analysis would require log parsing implementation')
        
        # Example violations to check:
        # - Brute force attempts
        # - Suspicious user agents
        # - Large file uploads
        # - Access to sensitive endpoints

    def generate_recommendations(self):
        """Generate security recommendations."""
        self.stdout.write('\n=== SECURITY RECOMMENDATIONS ===')
        
        recommendations = [
            'Enable two-factor authentication for all admin users',
            'Regularly rotate JWT secret keys',
            'Monitor failed login attempts and implement IP blocking',
            'Review and update CORS settings regularly',
            'Implement regular security audits',
            'Keep all dependencies updated',
            'Use HTTPS in production',
            'Implement proper logging and monitoring',
            'Regular backup and disaster recovery testing',
            'Security awareness training for users'
        ]
        
        for i, recommendation in enumerate(recommendations, 1):
            self.stdout.write(f'{i}. {recommendation}')
        
        # Check current security settings
        from django.conf import settings
        
        self.stdout.write('\n=== CURRENT SECURITY SETTINGS ===')
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'SECURE_SSL_REDIRECT: {getattr(settings, "SECURE_SSL_REDIRECT", False)}')
        self.stdout.write(f'SECURE_HSTS_SECONDS: {getattr(settings, "SECURE_HSTS_SECONDS", 0)}')
        self.stdout.write(f'SESSION_COOKIE_SECURE: {getattr(settings, "SESSION_COOKIE_SECURE", False)}')
        self.stdout.write(f'CSRF_COOKIE_SECURE: {getattr(settings, "CSRF_COOKIE_SECURE", False)}')
        
        if settings.DEBUG:
            self.stdout.write(
                self.style.ERROR('WARNING: DEBUG mode is enabled! Disable in production.')
            )