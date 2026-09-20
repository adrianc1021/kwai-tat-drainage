import uuid
from django.db import models
from django.conf import settings

class SiteSettings(models.Model):
    name=models.CharField('網站名稱',max_length=80,default='快達通渠')
    telephone=models.CharField('已確認電話',max_length=20,blank=True,default='85293339580')
    whatsapp=models.CharField('已確認 WhatsApp',max_length=20,blank=True,default='85293339580')
    analytics_enabled=models.BooleanField('啟用經同意的訪問統計',default=False)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: verbose_name_plural='網站設定'

class Page(models.Model):
    slug=models.SlugField(unique=True)
    name=models.CharField(max_length=80)
    draft=models.JSONField(default=dict)
    published=models.JSONField(default=dict)
    version=models.PositiveIntegerField(default=1)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: permissions=[('publish_page','Can publish page')]

class MediaAsset(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    title=models.CharField('圖片名稱',max_length=120)
    alt=models.CharField('預設替代文字',max_length=300,blank=True)
    caption=models.CharField('圖片說明',max_length=300,blank=True)
    tags=models.CharField('標籤',max_length=300,blank=True,help_text='以逗號分隔，例如：通渠前,高壓水力,商業工程')
    file=models.FileField(upload_to='images/')
    width=models.PositiveIntegerField()
    height=models.PositiveIntegerField()
    size=models.PositiveIntegerField()
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Revision(models.Model):
    page=models.ForeignKey(Page,on_delete=models.CASCADE)
    snapshot=models.JSONField()
    author=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)

class Audit(models.Model):
    author=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=80)
    target=models.CharField(max_length=120,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class Event(models.Model):
    EVENT_TYPES=[('page_view','瀏覽'),('whatsapp_click','WhatsApp 意向'),('telephone_click','電話意向')]
    session_hash=models.CharField(max_length=64,db_index=True)
    event=models.CharField(max_length=24,choices=EVENT_TYPES)
    page=models.CharField(max_length=32)
    device=models.CharField(max_length=12)
    environment=models.CharField(max_length=12,default='local')
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    class Meta: indexes=[models.Index(fields=['environment','created_at'])]

class Inquiry(models.Model):
    STATUS=[('new','待處理'),('contacted','已聯絡'),('qualified','有效查詢'),('won','已成交'),('closed','已結束')]
    reference=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    name=models.CharField('稱呼',max_length=80,blank=True)
    phone=models.CharField('電話',max_length=24,blank=True)
    message=models.TextField('情況',max_length=2000)
    channel=models.CharField('來源',max_length=20,choices=[('telephone','電話'),('whatsapp','WhatsApp'),('manual','其他／手動')],default='manual')
    status=models.CharField('狀態',max_length=20,choices=STATUS,default='new')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: verbose_name_plural='查詢紀錄'

class Throttle(models.Model):
    key=models.CharField(max_length=64,primary_key=True)
    count=models.PositiveIntegerField(default=0)
    start=models.DateTimeField()


class PageSection(models.Model):
    """Reusable page block metadata; page JSON remains the published payload."""
    page=models.ForeignKey(Page,on_delete=models.CASCADE,related_name='sections')
    kind=models.CharField('區塊類型',max_length=40)
    title=models.CharField('區塊標題',max_length=180,blank=True)
    content=models.JSONField('區塊內容',default=dict)
    position=models.PositiveIntegerField(default=0)
    enabled=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=['position','id']
        indexes=[models.Index(fields=['page','position'])]


class BlogCategory(models.Model):
    name=models.CharField('分類名稱',max_length=80)
    slug=models.SlugField(unique=True)
    description=models.TextField(blank=True)
    class Meta: verbose_name='Blog 分類'; verbose_name_plural='Blog 分類'
    def __str__(self): return self.name


class BlogTag(models.Model):
    name=models.CharField('標籤名稱',max_length=60)
    slug=models.SlugField(unique=True)
    def __str__(self): return self.name


class BlogPost(models.Model):
    STATUS=[('draft','草稿'),('review','審核中'),('scheduled','已排程'),('published','已發布'),('archived','已封存')]
    title=models.CharField('文章標題',max_length=180)
    slug=models.SlugField(unique=True)
    excerpt=models.TextField('摘要',blank=True)
    content=models.TextField('文章內容',blank=True)
    cover=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='blog_covers')
    category=models.ForeignKey(BlogCategory,null=True,blank=True,on_delete=models.SET_NULL,related_name='posts')
    tags=models.ManyToManyField(BlogTag,blank=True,related_name='posts')
    author=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name='blog_posts')
    status=models.CharField(max_length=16,choices=STATUS,default='draft',db_index=True)
    published_at=models.DateTimeField(null=True,blank=True)
    scheduled_at=models.DateTimeField(null=True,blank=True)
    views=models.PositiveIntegerField(default=0)
    search_clicks=models.PositiveIntegerField(default=0)
    cta_conversions=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        ordering=['-updated_at']
        permissions=[('publish_blogpost','Can publish blog post')]
    def __str__(self): return self.title


class SeoMetadata(models.Model):
    page=models.OneToOneField(Page,null=True,blank=True,on_delete=models.CASCADE,related_name='seo')
    post=models.OneToOneField(BlogPost,null=True,blank=True,on_delete=models.CASCADE,related_name='seo')
    service=models.OneToOneField('Service',null=True,blank=True,on_delete=models.CASCADE,related_name='seo')
    area=models.OneToOneField('ServiceArea',null=True,blank=True,on_delete=models.CASCADE,related_name='seo')
    title=models.CharField('SEO title',max_length=180,blank=True)
    description=models.CharField('Meta description',max_length=320,blank=True)
    canonical=models.URLField('Canonical URL',blank=True)
    index=models.BooleanField(default=False)
    follow=models.BooleanField(default=True)
    og_title=models.CharField(max_length=180,blank=True)
    og_description=models.CharField(max_length=320,blank=True)
    og_image=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='seo_images')
    primary_keywords=models.CharField(max_length=240,blank=True)
    secondary_keywords=models.CharField(max_length=400,blank=True)
    breadcrumb_title=models.CharField(max_length=120,blank=True)
    schema_type=models.CharField(max_length=40,default='WebPage')
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.CheckConstraint(check=(models.Q(page__isnull=False)|models.Q(post__isnull=False)|models.Q(service__isnull=False)|models.Q(area__isnull=False)),name='seo_has_target')]


class Redirect(models.Model):
    source=models.CharField('舊網址',max_length=220,unique=True)
    target=models.CharField('新網址',max_length=220)
    status_code=models.PositiveSmallIntegerField(default=301)
    enabled=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)


class Service(models.Model):
    STATUS=[('draft','草稿'),('published','已發布'),('archived','已封存')]
    name=models.CharField('服務名稱',max_length=120)
    slug=models.SlugField(unique=True)
    summary=models.CharField('短描述',max_length=260,blank=True)
    content=models.TextField('詳細內容',blank=True)
    cover=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='service_covers')
    emergency=models.BooleanField('可作緊急查詢分類',default=False)
    price_note=models.CharField('收費顯示說明',max_length=180,blank=True)
    status=models.CharField(max_length=16,choices=STATUS,default='draft',db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    class Meta: ordering=['name']
    def __str__(self): return self.name


class ServiceArea(models.Model):
    STATUS=[('draft','草稿'),('published','已發布'),('archived','已封存')]
    name=models.CharField('地區名稱',max_length=100)
    slug=models.SlugField(unique=True)
    region=models.CharField('所屬區域',max_length=60,blank=True)
    content=models.TextField('獨立內容',blank=True)
    service_hours=models.CharField(max_length=160,blank=True)
    status=models.CharField(max_length=16,choices=STATUS,default='draft',db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    class Meta: ordering=['name']
    def __str__(self): return self.name


class CaseStudy(models.Model):
    STATUS=[('draft','草稿'),('published','已發布'),('archived','已封存')]
    title=models.CharField('個案名稱',max_length=160)
    slug=models.SlugField(unique=True)
    date=models.DateField(null=True,blank=True)
    area=models.CharField('地區',max_length=80,blank=True)
    service=models.CharField('服務類型',max_length=120,blank=True)
    problem=models.TextField('問題描述',blank=True)
    method=models.TextField('處理方法',blank=True)
    duration=models.CharField('所需時間',max_length=80,blank=True)
    before=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='case_before')
    after=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='case_after')
    consent=models.BooleanField('已取得公開同意',default=False)
    anonymized=models.BooleanField('已移除個人資料',default=False)
    testimonial=models.TextField('客戶評語',blank=True)
    status=models.CharField(max_length=16,choices=STATUS,default='draft',db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=['-date','-updated_at']


class Review(models.Model):
    STATUS=[('pending','待審核'),('approved','已核准'),('hidden','已隱藏'),('archived','已封存')]
    display_name=models.CharField('顯示名稱',max_length=80)
    source=models.CharField('評價來源',max_length=120)
    body=models.TextField('評價內容')
    review_date=models.DateField(null=True,blank=True)
    consent=models.BooleanField('已獲授權使用',default=False)
    status=models.CharField(max_length=16,choices=STATUS,default='pending',db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class Campaign(models.Model):
    STATUS=[('draft','草稿'),('active','進行中'),('ended','已結束')]
    name=models.CharField('活動名稱',max_length=140)
    landing_page=models.CharField(max_length=220,blank=True)
    banner=models.ForeignKey(MediaAsset,null=True,blank=True,on_delete=models.SET_NULL,related_name='campaign_banners')
    offer=models.TextField('宣傳內容',blank=True)
    cta=models.CharField('CTA',max_length=80,blank=True)
    utm_campaign=models.SlugField(max_length=120,blank=True)
    starts_at=models.DateTimeField(null=True,blank=True)
    ends_at=models.DateTimeField(null=True,blank=True)
    budget=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    notes=models.TextField(blank=True)
    status=models.CharField(max_length=16,choices=STATUS,default='draft',db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class Integration(models.Model):
    PROVIDERS=[('ga4','Google Analytics 4'),('search_console','Google Search Console'),('pagespeed','PageSpeed Insights'),('gbp','Google Business Profile')]
    provider=models.CharField(max_length=30,choices=PROVIDERS,unique=True)
    enabled=models.BooleanField(default=False)
    property_id=models.CharField(max_length=180,blank=True)
    last_sync=models.DateTimeField(null=True,blank=True)
    error_message=models.CharField(max_length=300,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class Notification(models.Model):
    LEVELS=[('info','提示'),('warning','注意'),('error','錯誤')]
    title=models.CharField(max_length=160)
    body=models.TextField()
    level=models.CharField(max_length=12,choices=LEVELS,default='info')
    starts_at=models.DateTimeField(null=True,blank=True)
    ends_at=models.DateTimeField(null=True,blank=True)
    enabled=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
