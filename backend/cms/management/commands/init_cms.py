import copy
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from cms.models import Page, SiteSettings, BlogCategory, Integration, PageSection
from cms.content import PAGE_NAMES,initial
class Command(BaseCommand):
    help='Initialize page drafts without replacing existing edits.'
    def handle(self,*args,**options):
        SiteSettings.objects.get_or_create(pk=1)
        for slug,name in PAGE_NAMES.items():
            snapshot=initial(slug)
            page,_=Page.objects.get_or_create(slug=slug,defaults={'name':name,'draft':snapshot,'published':copy.deepcopy(snapshot)})
            for position,(key,block) in enumerate(page.draft.get('blocks',{}).items()):
                PageSection.objects.get_or_create(page=page,kind=block.get('label','text'),position=position,defaults={'title':key,'content':{'value':block.get('value','')}})
        roles={
            '內容編輯':['view_page','change_page','view_mediaasset','add_mediaasset','view_blogpost','add_blogpost','change_blogpost','view_blogcategory','view_blogtag','view_seometadata','change_seometadata','view_service','add_service','change_service','view_servicearea','add_servicearea','change_servicearea','view_casestudy','add_casestudy','change_casestudy','view_review','add_review','change_review'],
            '數據分析':['view_event','view_integration','view_audit'],
            '營運管理':['view_inquiry','add_inquiry','change_inquiry','delete_inquiry','view_audit','view_campaign','add_campaign','change_campaign','view_notification','add_notification','change_notification'],
        }
        for name,codes in roles.items():
            group,_=Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(content_type__app_label='cms',codename__in=codes))
        for name,slug in [('通渠知識','drainage-knowledge'),('家居保養','home-care'),('緊急處理','emergency'),('商業渠務','commercial-drainage'),('工程個案','case-study'),('常見問題','faq')]:
            BlogCategory.objects.get_or_create(slug=slug,defaults={'name':name})
        for provider,_ in Integration.PROVIDERS:
            Integration.objects.get_or_create(provider=provider)
        self.stdout.write(f'Initialized {len(PAGE_NAMES)} pages, settings and permission groups. Existing content preserved.')
