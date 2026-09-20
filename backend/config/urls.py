from django.contrib import admin
from django.urls import path
from cms import views as v
urlpatterns=[
 path('admin/',admin.site.urls),
 path('manage/setup/',v.setup,name='setup'),path('manage/login/',v.sign_in,name='login'),path('manage/logout/',v.sign_out,name='logout'),
 path('manage/workspace/',v.workspace,name='workspace'),path('manage/',v.dashboard,name='dashboard'),path('manage/export/',v.export_stats,name='export'),
 path('manage/pages/',v.pages,name='pages'),path('manage/pages/<slug:slug>/',v.edit_page,name='edit-page'),
 path('manage/media/',v.media,name='media'),path('manage/media/<uuid:pk>/delete/',v.delete_media,name='delete-media'),
 path('manage/settings/',v.site_settings,name='settings'),path('manage/history/',v.history,name='history'),
 path('manage/inquiries/',v.inquiries,name='inquiries'),path('manage/inquiries/<int:pk>/status/',v.inquiry_status,name='inquiry-status'),path('manage/inquiries/<int:pk>/delete/',v.inquiry_delete,name='inquiry-delete'),
 path('manage/seo/',v.seo_manager,name='seo'),path('manage/seo/<str:target>/<int:pk>/',v.seo_edit,name='seo-edit'),
 path('manage/integrations/',v.integrations,name='integrations'),path('manage/users/',v.users,name='users'),path('manage/notifications/',v.notifications,name='notifications'),
 path('manage/<str:kind>/',v.manager_list,name='manager-list'),path('manage/<str:kind>/new/',v.manager_edit,name='manager-new'),path('manage/<str:kind>/<int:pk>/',v.manager_edit,name='manager-edit'),path('manage/<str:kind>/<int:pk>/delete/',v.manager_delete,name='manager-delete'),
 path('api/token/',v.token),path('api/consent/',v.consent),path('api/event/',v.event),path('api/public-media/',v.public_media),
 path('media/<uuid:pk>.webp',v.asset_file),
 path('assets/<path:path>',v.site_asset),
 path('media-assets/<path:path>',v.site_asset,{'root':'media-assets'}),
 path('blog/',v.public_blog,name='blog-list'),path('blog/<slug:slug>/',v.public_blog,name='blog-post'),
 path('sitemap.xml',v.sitemap,name='sitemap'),path('robots.txt',v.robots,name='robots'),
 path('',v.public_page,name='home'),path('<slug:slug>.html',v.public_page),path('<str:name>',v.site_asset)
]
