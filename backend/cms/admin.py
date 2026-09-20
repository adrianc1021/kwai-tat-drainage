from django.contrib import admin
from .models import (Inquiry, Page, MediaAsset, BlogPost, BlogCategory, BlogTag, SeoMetadata,
                      Service, ServiceArea, CaseStudy, Review, Campaign, Integration, Notification, PageSection)
admin.site.site_header='快達通渠 · 帳戶及權限管理'
admin.site.site_title='快達通渠管理'
admin.site.index_title='進階管理'
# Users and groups use Django's audited built-in password/permission management.
admin.site.register([Page,MediaAsset,BlogPost,BlogCategory,BlogTag,SeoMetadata,Service,ServiceArea,CaseStudy,Review,Campaign,Integration,Notification,PageSection])
