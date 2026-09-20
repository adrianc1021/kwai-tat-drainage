import os, sqlite3, tempfile, zipfile
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
class Command(BaseCommand):
    help='Create a private, consistent database + media backup. Includes personal data and secret key.'
    def handle(self,*args,**options):
        folder=settings.PRIVATE_DIR/'backups';folder.mkdir(exist_ok=True,mode=0o700)
        target=folder/f"cms-{timezone.now().strftime('%Y%m%d-%H%M%S-%f')}.zip"
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/'cms.sqlite3'
            with sqlite3.connect(settings.DATABASES['default']['NAME']) as source, sqlite3.connect(db) as dest:source.backup(dest)
            with os.fdopen(fd,'wb') as output,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.write(db,'cms.sqlite3');archive.write(settings.PRIVATE_DIR/'secret.key','secret.key')
                for file in settings.MEDIA_ROOT.rglob('*'):
                    if file.is_file():archive.write(file,'media/'+str(file.relative_to(settings.MEDIA_ROOT)))
        self.stdout.write(f'Private backup created: {target}')
