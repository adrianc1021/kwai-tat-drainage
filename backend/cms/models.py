import uuid
from django.db import models
from django.conf import settings

class SiteSettings(models.Model):
    name=models.CharField('網站名稱',max_length=80,default='快達通渠')
    telephone=models.CharField('已確認電話',max_length=20,blank=True)
    whatsapp=models.CharField('已確認 WhatsApp',max_length=20,blank=True)
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
