import copy, io, json, tempfile
from datetime import timedelta
from pathlib import Path
from PIL import Image
from urllib.error import URLError
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from .models import Page, SiteSettings, MediaAsset, Event, Revision, Audit, Inquiry, BlogPost, SeoMetadata, Service, Integration
from .views import stats

class CMSFlowTests(TestCase):
    def setUp(self):
        call_command('init_cms',verbosity=0)
        self.admin=get_user_model().objects.create_superuser('test_owner',password='Testing-only-random-982!')
        self.client.force_login(self.admin)
        self.media_dir=tempfile.TemporaryDirectory()
        self.override=override_settings(MEDIA_ROOT=self.media_dir.name);self.override.enable()
    def tearDown(self):self.override.disable();self.media_dir.cleanup()
    def upload(self):
        out=io.BytesIO();Image.new('RGB',(120,80),'blue').save(out,format='PNG')
        return self.client.post('/manage/media/',{'title':'測試圖片','alt':'藍色測試圖','image':SimpleUploadedFile('test.png',out.getvalue(),content_type='image/png')})
    def test_image_upload_can_use_file_name_defaults(self):
        out=io.BytesIO();Image.new('RGB',(120,80),'green').save(out,format='JPEG')
        response=self.client.post('/manage/media/',{'image':SimpleUploadedFile('kitchen-drain.jpeg',out.getvalue(),content_type='image/jpeg')})
        self.assertEqual(response.status_code,302)
        asset=MediaAsset.objects.get()
        self.assertEqual(asset.title,'kitchen-drain')
        self.assertEqual(asset.alt,'')
    def test_manager_pages_render(self):
        for path in ['/manage/','/manage/pages/','/manage/pages/index/','/manage/media/','/manage/settings/','/manage/history/','/manage/inquiries/']:
            with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
    def test_anonymous_cannot_read_or_mutate_management(self):
        c=Client()
        for path in ['/manage/','/manage/pages/index/','/manage/media/','/manage/inquiries/','/manage/export/']:
            self.assertEqual(c.get(path).status_code,302)
            self.assertEqual(c.post(path,{}).status_code,302)
    def test_csrf_required(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.admin)
        self.assertEqual(c.post('/manage/settings/',{}).status_code,403)
        self.assertEqual(c.post('/api/consent/',json.dumps({'choice':'yes'}),content_type='application/json').status_code,403)
    def test_image_validation_and_private_drafts(self):
        self.assertEqual(self.upload().status_code,302)
        a=MediaAsset.objects.get();self.assertEqual(a.width,120)
        self.assertEqual(self.client.post(f'/manage/media/{a.pk}/edit/',{'title':'更新圖片','alt':'更新替代文字','caption':'工程說明','tags':'通渠前,住宅'}).status_code,302)
        a.refresh_from_db();self.assertEqual(a.caption,'工程說明');self.assertEqual(a.tags,'通渠前,住宅')
        self.assertEqual(Client().get(f'/media/{a.pk}.webp').status_code,404)
        self.assertEqual(self.client.get(f'/media/{a.pk}.webp').status_code,200)
        self.assertEqual(Image.open(a.file).format,'WEBP')
        self.client.post('/manage/media/',{'title':'malicious','alt':'bad','image':SimpleUploadedFile('fake.png',b'<script>alert(1)</script>',content_type='image/png')})
        self.assertEqual(MediaAsset.objects.count(),1)
    def test_draft_publish_image_rollback_and_no_xss(self):
        self.upload();a=MediaAsset.objects.get();page=Page.objects.get(slug='cases');original=copy.deepcopy(page.published)
        key=next(k for k,v in page.draft['blocks'].items() if v['label']=='h1')
        data={'version':page.version,'title':'測試新標題','description':'測試描述',key:'<script>alert(1)</script>','image_image_0':str(a.pk),'alt_image_0':'測試主視覺','crop_image_0':'top','action':'save'}
        self.client.post('/manage/pages/cases/',data)
        page.refresh_from_db();self.assertEqual(page.published,original)
        self.assertNotContains(Client().get('/cases.html'),'測試新標題')
        self.assertEqual(Client().get('/cases.html?preview=draft').status_code,403)
        self.assertContains(self.client.get('/cases.html?preview=draft'),'&lt;script&gt;')
        self.client.post('/manage/pages/cases/',{'version':page.version,'action':'publish'})
        page.refresh_from_db()
        r=Client().get('/cases.html');self.assertContains(r,'測試新標題');self.assertContains(r,f'/media/{a.pk}.webp');self.assertNotContains(r,'<script>alert(1)</script>')
        self.assertEqual(Client().get(f'/media/{a.pk}.webp').status_code,200)
        self.client.post(f'/manage/media/{a.pk}/delete/');self.assertEqual(MediaAsset.objects.count(),1)
        self.client.post('/manage/pages/cases/',{'version':page.version,'action':'restore','revision':Revision.objects.get().pk})
        page.refresh_from_db();self.assertEqual(page.draft,original);self.assertNotEqual(page.published,original)

    @override_settings(RENDER_DEPLOY_HOOK_URL='https://api.render.com/deploy/srv_test')
    def test_publish_triggers_render_deploy_hook_after_commit(self):
        page=Page.objects.get(slug='index')
        class Response:
            status=201
            def __enter__(self): return self
            def __exit__(self,*args): return False
        with patch('cms.views.urllib.request.urlopen',return_value=Response()) as request:
            response=self.client.post('/manage/pages/index/',{'version':page.version,'action':'publish'},follow=True)
        page.refresh_from_db()
        self.assertEqual(response.status_code,200)
        self.assertTrue(page.published)
        request.assert_called_once()
        self.assertContains(response,'Render 已收到重新部署通知。')

    @override_settings(RENDER_DEPLOY_HOOK_URL='https://api.render.com/deploy/srv_test')
    def test_publish_remains_public_when_render_deploy_hook_fails(self):
        page=Page.objects.get(slug='index')
        with patch('cms.views.urllib.request.urlopen',side_effect=URLError('offline')):
            response=self.client.post('/manage/pages/index/',{'version':page.version,'action':'publish'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'網站內容已生效')
        self.assertContains(Client().get('/'),page.published['title'])

    def test_publish_without_render_deploy_hook_is_immediately_public(self):
        page=Page.objects.get(slug='index')
        response=self.client.post('/manage/pages/index/',{'version':page.version,'action':'publish'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'網站已立即更新')
        self.assertContains(Client().get('/'),page.published['title'])
    def test_stale_version_does_not_overwrite(self):
        page=Page.objects.get(slug='index')
        self.client.post('/manage/pages/index/',{'version':0,'title':'bad','description':'bad','action':'save'})
        page.refresh_from_db();self.assertEqual(page.version,1)
    def test_editor_cannot_publish_or_view_inquiries(self):
        u=get_user_model().objects.create_user('editor',password='something-safe',is_staff=True)
        u.user_permissions.add(Permission.objects.get(codename='change_page'))
        c=Client();c.force_login(u)
        self.assertEqual(c.post('/manage/pages/index/',{'action':'publish','version':1}).status_code,403)
        self.assertEqual(c.get('/manage/inquiries/').status_code,403)
        c.post('/manage/blog/new/', {'title':'未授權發布','slug':'blocked-publish','content':'內容','status':'published'})
        self.assertFalse(BlogPost.objects.filter(slug='blocked-publish').exists())
    def test_contact_configuration_validated_and_rendered(self):
        self.client.post('/manage/settings/',{'telephone':'javascript:alert(1)','whatsapp':''})
        self.assertEqual(SiteSettings.objects.get().telephone,'85293339580')
        self.client.post('/manage/settings/',{'telephone':'85200000000','whatsapp':'85200000000'})
        config=SiteSettings.objects.get()
        self.assertEqual(config.telephone,'85200000000')
        self.assertEqual(config.whatsapp,'85200000000')

    def test_published_homepage_media_manifest(self):
        self.upload();a=MediaAsset.objects.get();page=Page.objects.get(slug='index')
        self.client.post('/manage/pages/index/',{'version':page.version,'title':page.draft['title'],'description':page.draft['description'],'image_hero_poster':str(a.pk),'alt_hero_poster':'測試首頁封面','crop_hero_poster':'center','action':'save'})
        page.refresh_from_db()
        self.client.post('/manage/pages/index/',{'version':page.version,'action':'publish'})
        payload=self.client.get('/api/public-media/').json()
        self.assertEqual(payload['media']['index:hero_poster']['url'],f'/media/{a.pk}.webp')
    def test_inquiry_manual_and_private(self):
        self.client.post('/manage/inquiries/',{'name':'測試','phone':'00000000','message':'測試內容','channel':'manual','status':'new'})
        row=Inquiry.objects.get();self.assertEqual(Event.objects.count(),0)
        self.client.post(f'/manage/inquiries/{row.pk}/status/',{'status':'qualified'});row.refresh_from_db();self.assertEqual(row.status,'qualified')
        self.assertFalse(Audit.objects.filter(target__contains='00000000').exists())
        self.client.post(f'/manage/inquiries/{row.pk}/delete/');self.assertEqual(Inquiry.objects.count(),0)
    def test_analytics_consent_admin_exclusion_allowlist_and_rate(self):
        c=Client();data={'event':'page_view','page':'index','device':'mobile'}
        def send(payload):return c.post('/api/event/',json.dumps(payload),content_type='application/json')
        send(data);self.assertEqual(Event.objects.count(),0)
        conf=SiteSettings.objects.get();conf.analytics_enabled=True;conf.save()
        send(data);self.assertEqual(Event.objects.count(),0)
        c.post('/api/consent/',json.dumps({'choice':'yes'}),content_type='application/json')
        self.assertEqual(send({**data,'phone':'secret'}).status_code,400)
        send(data);send(data)
        send({**data,'event':'whatsapp_click'});send({**data,'event':'whatsapp_click'})
        self.assertEqual(stats(7)['sessions'],1);self.assertEqual(stats(7)['converted'],1);self.assertEqual(stats(7)['rate'],100)
        self.assertEqual(stats(7)['pv'],2)
        c.force_login(self.admin);send(data);self.assertEqual(Event.objects.count(),4)
        self.assertNotContains(c.get('/index.html'),'data-consent')
        c.logout();c.post('/api/consent/',json.dumps({'choice':'no'}),content_type='application/json');send(data);self.assertEqual(Event.objects.count(),4)
    def test_bootstrap_closed_when_user_exists(self):
        self.assertEqual(Client().get('/manage/setup/').status_code,302)

    def test_blog_draft_is_private_and_published_is_readable(self):
        category = __import__('cms.models', fromlist=['BlogCategory']).BlogCategory.objects.create(name='通渠知識', slug='drainage')
        response=self.client.post('/manage/blog/new/', {'title':'廁所去水變慢時先做甚麼','slug':'slow-drain','excerpt':'先確認問題位置，再聯絡客服。','content':'第一段實用內容。','category':category.pk,'status':'draft'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Client().get('/blog/slow-drain/').status_code,404)
        post=BlogPost.objects.get(slug='slow-drain');post.status='published';post.save()
        self.assertContains(Client().get('/blog/slow-drain/'),'廁所去水變慢時先做甚麼')

    def test_scheduled_blog_command_publishes_due_posts(self):
        post=BlogPost.objects.create(title='排水小知識',slug='drainage-tip',status='scheduled',scheduled_at=timezone.now()-timedelta(minutes=2))
        call_command('publish_scheduled')
        post.refresh_from_db();self.assertEqual(post.status,'published');self.assertIsNotNone(post.published_at)

    def test_seo_metadata_persists_for_page(self):
        page=Page.objects.get(slug='index')
        response=self.client.post(f'/manage/seo/page/{page.pk}/', {'title':'快達通渠首頁','description':'香港通渠及排水問題查詢。','canonical':'','index':'','follow':'on','og_title':'首頁','og_description':'','og_image':'','primary_keywords':'通渠','secondary_keywords':'','breadcrumb_title':'首頁','schema_type':'WebPage'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(SeoMetadata.objects.get(page=page).title,'快達通渠首頁')
        self.assertContains(Client().get('/'),'<title>快達通渠首頁</title>',html=False)

    def test_services_and_integration_are_real_records(self):
        response=self.client.post('/manage/services/new/', {'name':'住宅通渠','slug':'residential-drainage','summary':'處理住宅渠道淤塞查詢。','content':'先了解位置和現場情況。','emergency':'on','price_note':'需按現場確認','status':'draft'})
        self.assertEqual(response.status_code,302);self.assertTrue(Service.objects.filter(slug='residential-drainage').exists())
        row=Integration.objects.get(provider='ga4')
        response=self.client.post('/manage/integrations/', {'pk':row.pk,'property_id':'G-TEST','enabled':'on'})
        self.assertEqual(response.status_code,302);row.refresh_from_db();self.assertTrue(row.enabled);self.assertEqual(row.property_id,'G-TEST')

    def test_new_management_modules_render(self):
        for path in ['/manage/blog/','/manage/services/','/manage/areas/','/manage/cases/','/manage/reviews/','/manage/campaigns/','/manage/seo/','/manage/integrations/','/manage/notifications/','/manage/users/']:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code,200)
        for path in ['/manage/blog/new/','/manage/services/new/','/manage/areas/new/','/manage/cases/new/','/manage/reviews/new/','/manage/campaigns/new/']:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code,200)

    def test_dynamic_seo_routes_exist(self):
        self.assertEqual(Client().get('/sitemap.xml').status_code,200)
        self.assertEqual(Client().get('/robots.txt').status_code,200)

    def test_public_pages_are_server_rendered_and_have_one_h1(self):
        routes = ['/', *[f'/{slug}.html' for slug in ('services','drainage','high-pressure','cctv','commercial','pricing','areas','cases','tips','about','faq','contact','privacy')]]
        for route in routes:
            with self.subTest(route=route):
                response = Client().get(route)
                self.assertEqual(response.status_code, 200)
                soup = __import__('bs4', fromlist=['BeautifulSoup']).BeautifulSoup(response.content, 'html.parser')
                self.assertEqual(len(soup.select('main h1')), 1)
                self.assertNotIn('<div id=\"root\"></div>', response.content.decode())
                self.assertTrue(soup.title and soup.title.get_text(strip=True))
                self.assertTrue(soup.select_one('meta[name=\"description\"]'))

    def test_site_copy_settings_are_rendered_from_cms(self):
        config = SiteSettings.objects.get(pk=1)
        config.announcement = '測試公告列'
        config.footer_note = '測試頁尾簡介'
        config.save()
        response = Client().get('/')
        self.assertContains(response, '測試公告列')
        self.assertContains(response, '測試頁尾簡介')

    def test_preview_is_noindex_and_sitemap_has_lastmod(self):
        page = Page.objects.get(slug='index')
        preview = self.client.get('/?preview=draft')
        self.assertContains(preview, 'noindex, nofollow, noarchive', html=False)
        self.assertNotContains(preview, 'rel=\"canonical\"', html=False)
        seo = SeoMetadata.objects.create(page=page, index=False, follow=True)
        sitemap = Client().get('/sitemap.xml').content.decode()
        self.assertNotIn('<loc>http://testserver/</loc>', sitemap)
        self.assertIn('<lastmod>', sitemap)
        seo.delete()

    def test_homepage_image_and_phone_links_are_present(self):
        response = Client().get('/')
        self.assertContains(response, 'data-media=\"home-hero\"', html=False)
        self.assertContains(response, 'tel:+85293339580', html=False)
        self.assertContains(response, 'wa.me/85293339580', html=False)

    @override_settings(PRODUCTION=True)
    def test_production_public_pages_are_not_marked_noindex(self):
        response = Client().get('/')
        self.assertNotIn('X-Robots-Tag', response)
        self.assertEqual(response['Content-Security-Policy'].split(';')[0], "default-src 'self'")
        private = Client().get('/manage/login/')
        self.assertEqual(private['X-Robots-Tag'], 'noindex, nofollow')

    @override_settings(PRODUCTION=True, SITE_URL='https://rapidflowhk.com')
    def test_legacy_render_host_redirects_to_primary_domain(self):
        response = Client().get('/pricing.html?from=old-host', HTTP_HOST='kwai-tat-drainage-cms.onrender.com')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://rapidflowhk.com/pricing.html?from=old-host')

    def test_primary_domain_is_used_for_sitemap_and_robots(self):
        sitemap = Client().get('/sitemap.xml', HTTP_HOST='rapidflowhk.com').content.decode()
        robots = Client().get('/robots.txt', HTTP_HOST='rapidflowhk.com').content.decode()
        self.assertIn('<loc>https://rapidflowhk.com/</loc>', sitemap)
        self.assertIn('Sitemap: https://rapidflowhk.com/sitemap.xml', robots)

    def test_unknown_public_path_uses_custom_404(self):
        response = Client().get('/not-a-real-page')
        self.assertEqual(response.status_code, 404)
        self.assertIn('找不到這個頁面', response.content.decode())
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_project_files_not_served(self):
        for path in ['/private/cms.sqlite3','/site-src/build.py','/requirements.txt','/secret.key','/../README.md']:
            self.assertEqual(Client().get(path).status_code,404)

    def test_public_blog_has_independent_indexable_metadata(self):
        from bs4 import BeautifulSoup
        post=BlogPost.objects.create(title='渠管檢查',slug='pipe-check',excerpt='了解渠道檢查安排。',content='文章內容',status='published')
        response=Client().get('/blog/pipe-check/')
        soup=BeautifulSoup(response.content,'html.parser')
        self.assertEqual(soup.select_one('meta[name="robots"]')['content'],'index, follow')
        self.assertEqual(soup.select_one('meta[name="description"]')['content'],post.excerpt)
        self.assertNotContains(response,'網站管理後台')
        self.assertEqual(len(soup.select('h1')),1)
        SeoMetadata.objects.create(post=post,index=False,title='文章自訂標題')
        response=Client().get('/blog/pipe-check/')
        self.assertContains(response,'文章自訂標題')
        self.assertContains(response,'noindex, follow')
        self.assertNotContains(Client().get('/sitemap.xml'),'/blog/pipe-check/')

    def test_sitemap_and_robots_use_configured_origin(self):
        from unittest.mock import patch
        with patch.dict('os.environ',{'SITE_URL':'https://rapidflowhk.com'}):
            self.assertContains(Client().get('/sitemap.xml'),'https://rapidflowhk.com/')
            self.assertNotContains(Client().get('/sitemap.xml'),'http://testserver')
            self.assertContains(Client().get('/robots.txt'),'https://rapidflowhk.com/sitemap.xml')
