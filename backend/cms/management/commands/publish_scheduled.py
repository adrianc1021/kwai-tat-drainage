from django.core.management.base import BaseCommand
from django.utils import timezone
from cms.models import BlogPost

class Command(BaseCommand):
    help='Publish Blog posts whose scheduled time has arrived.'
    def handle(self,*args,**options):
        rows=BlogPost.objects.filter(status='scheduled',scheduled_at__isnull=False,scheduled_at__lte=timezone.now(),deleted_at__isnull=True)
        count=rows.update(status='published',published_at=timezone.now())
        self.stdout.write(f'Published {count} scheduled posts.')
