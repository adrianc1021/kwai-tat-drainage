import copy
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from cms.models import Page, SiteSettings
from cms.content import PAGE_NAMES,initial
class Command(BaseCommand):
    help='Initialize page drafts without replacing existing edits.'
    def handle(self,*args,**options):
        SiteSettings.objects.get_or_create(pk=1)
        for slug,name in PAGE_NAMES.items():
            snapshot=initial(slug)
            Page.objects.get_or_create(slug=slug,defaults={'name':name,'draft':snapshot,'published':copy.deepcopy(snapshot)})
        roles={'內容編輯':['view_page','change_page','view_mediaasset','add_mediaasset'], '數據分析':['view_event'], '營運管理':['view_inquiry','add_inquiry','change_inquiry','delete_inquiry','view_audit']}
        for name,codes in roles.items():
            group,_=Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(content_type__app_label='cms',codename__in=codes))
        self.stdout.write(f'Initialized {len(PAGE_NAMES)} pages, settings and permission groups. Existing content preserved.')
