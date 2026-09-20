import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create the first CMS administrator from deployment environment variables.'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            self.stdout.write('CMS administrator already exists; no account changed.')
            return
        username = os.environ.get('CMS_ADMIN_USERNAME', '').strip()
        password = os.environ.get('CMS_ADMIN_PASSWORD', '')
        if not username or not password:
            self.stdout.write('No bootstrap credentials supplied; CMS remains locked until configured.')
            return
        if len(password) < 12:
            raise CommandError('CMS_ADMIN_PASSWORD must be at least 12 characters.')
        user = User.objects.create_superuser(username=username, password=password)
        self.stdout.write(f'Created initial CMS administrator: {user.username}')
