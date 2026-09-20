from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from cms.models import Event,Throttle
class Command(BaseCommand):
    help='Remove events older than 90 days and expired abuse counters.'
    def handle(self,*args,**options):
        n,_=Event.objects.filter(created_at__lt=timezone.now()-timedelta(days=90)).delete()
        Throttle.objects.filter(start__lt=timezone.now()-timedelta(days=1)).delete()
        self.stdout.write(f'Removed {n} expired analytics rows.')
