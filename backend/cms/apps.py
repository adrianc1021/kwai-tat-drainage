import os
from django.apps import AppConfig
class CmsConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='cms'
    def ready(self):
        from django.db.models.signals import post_migrate
        def protect_database(**kwargs):
            from django.conf import settings
            database=settings.DATABASES['default']['NAME']
            if database and str(database)!=':memory:' and os.path.exists(database):os.chmod(database,0o600)
        post_migrate.connect(protect_database,dispatch_uid='cms.protect_database')
