import csv, io, json, secrets, hashlib, hmac, copy, mimetypes, os
from datetime import timedelta
from functools import wraps
from pathlib import Path
from PIL import Image, ImageOps
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .models import (SiteSettings, Page, MediaAsset, Revision, Audit, Event, Inquiry, Throttle,
    BlogPost, BlogCategory, BlogTag, SeoMetadata, Service, ServiceArea, CaseStudy, Review,
    Campaign, Integration, Notification)
from .forms import (SetupForm, SettingsForm, UploadForm, InquiryForm, BlogPostForm,
    BlogCategoryForm, SeoMetadataForm, ServiceForm, ServiceAreaForm, CaseStudyForm,
    ReviewForm, CampaignForm, IntegrationForm, NotificationForm, MediaAssetForm)
from . import content

def guard(permission):
    def decorator(fn):
        @login_required
        @wraps(fn)
        def wrapped(request,*args,**kwargs):
            if not request.user.is_staff or not request.user.has_perm('cms.'+permission):return HttpResponseForbidden('你的帳戶沒有這項權限。')
            return fn(request,*args,**kwargs)
        return wrapped
    return decorator

def audit(request,action,target=''):
    Audit.objects.create(author=request.user,action=action,target=target)

def throttled(key,limit,seconds=900):
    hashed=hmac.new(settings.SECRET_KEY.encode(),key.encode(),hashlib.sha256).hexdigest()
    now=timezone.now()
    with transaction.atomic():
        row,_=Throttle.objects.select_for_update().get_or_create(key=hashed,defaults={'start':now})
        if row.start<now-timedelta(seconds=seconds):row.start=now;row.count=0
        row.count+=1;row.save()
        return row.count>limit

@require_http_methods(['GET','POST'])
def setup(request):
    if settings.PRODUCTION or get_user_model().objects.exists():return redirect('login')
    form=SetupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            # Serialize bootstrap via singleton settings row.
            SiteSettings.objects.select_for_update().get(pk=1)
            if get_user_model().objects.exists():return redirect('login')
            user=form.save(commit=False);user.is_staff=True;user.is_superuser=True;user.save()
        login(request,user);audit(request,'建立首位管理員');return redirect('dashboard')
    return render(request,'portal/auth.html',{'form':form,'setup':True})

@require_http_methods(['GET','POST'])
def sign_in(request):
    if not get_user_model().objects.exists():return redirect('setup')
    form=AuthenticationForm(request,data=request.POST or None)
    if request.method=='POST':
        if throttled('login:'+request.META.get('REMOTE_ADDR',''),10):
            form.add_error(None,'嘗試次數過多，請 15 分鐘後再試。')
        elif form.is_valid():
            if not form.get_user().is_staff:form.add_error(None,'此帳戶沒有管理權限。')
            else:login(request,form.get_user());audit(request,'登入');return redirect('workspace')
    return render(request,'portal/auth.html',{'form':form})

@require_POST
def sign_out(request):
    logout(request);return redirect('login')

def stats(days):
    start=timezone.localdate()-timedelta(days=days-1)
    events=Event.objects.filter(created_at__date__gte=start,environment='production' if settings.PRODUCTION else 'local')
    views=events.filter(event='page_view')
    visitor_ids=views.values('session_hash').distinct()
    sessions=visitor_ids.count()
    intentions=events.exclude(event='page_view').filter(session_hash__in=visitor_ids)
    converted=intentions.values('session_hash').distinct().count()
    pv=views.count()
    series={str(r['day']):r['total'] for r in views.annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('id'))}
    maximum=max(series.values(),default=1)
    daily=[{'date':start+timedelta(days=i),'count':series.get(str(start+timedelta(days=i)),0)} for i in range(days)]
    for row in daily:row['level']=round(row['count']/maximum*10) if maximum else 0
    return {'pv':pv,'sessions':sessions,'converted':converted,'rate':round(converted/sessions*100,1) if sessions else None,'whatsapp':intentions.filter(event='whatsapp_click').count(),'telephone':intentions.filter(event='telephone_click').count(),'daily':daily,'pages':list(views.values('page').annotate(total=Count('id')).order_by('-total')),'devices':list(views.values('device').annotate(total=Count('id'))),'days':days}

@guard('view_event')
def dashboard(request):
    days=int(request.GET.get('days','7')) if request.GET.get('days','7') in ('7','30','90') else 7
    data=stats(days)
    data.update({'active':'dashboard','config':SiteSettings.objects.get(pk=1),'environment':'正式環境' if settings.PRODUCTION else '本機測試','now':timezone.localtime(),'asset_count':MediaAsset.objects.count(),'page_count':Page.objects.count(),'inquiry_count':Inquiry.objects.count() if request.user.has_perm('cms.view_inquiry') else None,'activity':Audit.objects.order_by('-id')[:5] if request.user.has_perm('cms.view_audit') else [],'integrations':Integration.objects.order_by('provider'),'post_count':BlogPost.objects.filter(deleted_at__isnull=True).count(),'service_count':Service.objects.filter(deleted_at__isnull=True).count()})
    return render(request,'portal/dashboard.html',data)

@guard('view_event')
def export_stats(request):
    days=int(request.GET.get('days','30')) if request.GET.get('days','30') in ('7','30','90') else 30
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig');response['Content-Disposition']='attachment; filename="visits.csv"'
    response.write('\ufeff');writer=csv.writer(response);writer.writerow(['日期（香港）','瀏覽頁數','資料環境'])
    for row in stats(days)['daily']:writer.writerow([row['date'],row['count'],'production' if settings.PRODUCTION else 'local'])
    audit(request,'匯出彙總統計');return response

@guard('view_page')
def pages(request):return render(request,'portal/pages.html',{'active':'pages','pages':Page.objects.order_by('id')})

@guard('change_page')
@require_http_methods(['GET','POST'])
def edit_page(request,slug):
    page=get_object_or_404(Page,slug=slug)
    if request.method=='POST':
        if request.POST.get('action')=='publish' and not request.user.has_perm('cms.publish_page'):return HttpResponseForbidden('沒有發布權限。')
        with transaction.atomic():
            page=Page.objects.select_for_update().get(pk=page.pk)
            if str(page.version)!=request.POST.get('version'):
                messages.error(request,'另一個操作已修改此頁。請重新載入後再編輯，避免覆蓋。');return redirect('edit-page',slug=slug)
            snapshot=copy.deepcopy(page.draft)
            if request.POST.get('action')=='publish':
                Revision.objects.create(page=page,snapshot=page.published,author=request.user)
                page.published=copy.deepcopy(page.draft);audit(request,'套用頁面草稿',slug)
                messages.success(request,'草稿已套用到本機網站。沒有公開部署。')
            elif request.POST.get('action')=='restore':
                revision=get_object_or_404(Revision,pk=request.POST.get('revision'),page=page)
                page.draft=copy.deepcopy(revision.snapshot);audit(request,'還原歷史至草稿',slug);messages.success(request,'歷史版本已還原為草稿。可先預覽，再套用。')
            else:
                snapshot['title']=request.POST.get('title','')[:180].strip()
                snapshot['description']=request.POST.get('description','')[:400].strip()
                if not snapshot['title'] or not snapshot['description']:
                    messages.error(request,'SEO 標題及描述不可留空。');return redirect('edit-page',slug=slug)
                for key in snapshot.get('blocks',{}):
                    if key in request.POST:snapshot['blocks'][key]['value']=request.POST[key][:4000]
                for key in content.slots(slug):
                    asset_id=request.POST.get('image_'+key,'')
                    if asset_id:
                        try: asset=MediaAsset.objects.get(pk=asset_id)
                        except (MediaAsset.DoesNotExist,ValueError,ValidationError):raise Http404
                        alt=request.POST.get('alt_'+key,'').strip()[:300]
                        snapshot.setdefault('images',{})[key]={'asset':str(asset.pk),'alt':alt or asset.alt or asset.title,'crop':request.POST.get('crop_'+key) if request.POST.get('crop_'+key) in ('top','center','bottom') else 'center'}
                    else:snapshot.setdefault('images',{}).pop(key,None)
                page.draft=snapshot;audit(request,'儲存頁面草稿',slug);messages.success(request,'草稿已儲存，網站現行內容未更改。')
            page.version+=1;page.save()
        return redirect('edit-page',slug=slug)
    image_slots=[]
    for key,(label,selector) in content.slots(slug).items():
        slot={'key':key,'label':label,'default':selector if selector.startswith('/') else ''}
        slot.update(page.draft.get('images',{}).get(key,{}))
        image_slots.append(slot)
    return render(request,'portal/editor.html',{'active':'pages','page':page,'image_slots':image_slots,'assets':MediaAsset.objects.order_by('-created_at'),'revisions':page.revision_set.order_by('-id')[:10]})

@guard('view_mediaasset')
@require_http_methods(['GET','POST'])
def media(request):
    form=UploadForm(request.POST or None,request.FILES or None)
    if request.method=='POST':
        if not request.user.has_perm('cms.add_mediaasset'):return HttpResponseForbidden()
        if form.is_valid():
            try:
                image=ImageOps.exif_transpose(Image.open(form.cleaned_data['image']))
                image.thumbnail((3200,3200));image=image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
                buffer=io.BytesIO();image.save(buffer,format='WEBP',quality=85,method=4)
                asset=MediaAsset(title=form.cleaned_data['title'],alt=form.cleaned_data['alt'],width=image.width,height=image.height,size=buffer.tell())
                asset.file.save(f'{asset.pk}.webp',ContentFile(buffer.getvalue()),save=True)
                audit(request,'上載圖片',str(asset.pk));messages.success(request,'圖片已上載。前往頁面編輯選擇圖片，再套用草稿。');return redirect('media')
            except (OSError,ValueError,Image.DecompressionBombError):form.add_error('image','無法安全處理此圖片，請改用有效的 JPG、PNG 或 WebP。')
    assets=MediaAsset.objects.all().order_by('-created_at')
    if request.GET.get('q'):assets=assets.filter(title__icontains=request.GET['q'][:120])
    return render(request,'portal/media.html',{'active':'media','assets':assets,'form':form,'total_size':sum(a.size for a in assets),'q':request.GET.get('q','')})

@guard('delete_mediaasset')
@require_POST
def delete_media(request,pk):
    asset=get_object_or_404(MediaAsset,pk=pk)
    used=any(str(pk)==p.get('asset') for page in Page.objects.all() for snapshot in [page.draft,page.published] for p in snapshot.get('images',{}).values()) or any(str(pk)==p.get('asset') for revision in Revision.objects.all() for p in revision.snapshot.get('images',{}).values())
    if used:messages.error(request,'圖片仍被頁面草稿、現行版本或歷史版本使用，不能刪除。')
    else:
        asset.file.delete(save=False);asset.delete();audit(request,'刪除未使用圖片',str(pk));messages.success(request,'圖片已刪除。')
    return redirect('media')

@guard('change_mediaasset')
@require_http_methods(['GET','POST'])
def edit_media(request,pk):
    asset=get_object_or_404(MediaAsset,pk=pk)
    form=MediaAssetForm(request.POST or None,instance=asset)
    if request.method=='POST' and form.is_valid():
        form.save();audit(request,'更新圖片資料',str(pk));messages.success(request,'圖片資料已更新。');return redirect('media')
    return render(request,'portal/media_edit.html',{'active':'media','asset':asset,'form':form})

@guard('change_sitesettings')
@require_http_methods(['GET','POST'])
def site_settings(request):
    config=SiteSettings.objects.get(pk=1);form=SettingsForm(request.POST or None,instance=config)
    if request.method=='POST' and form.is_valid():
        form.save();audit(request,'更新網站設定');messages.success(request,'設定已儲存。');return redirect('settings')
    return render(request,'portal/settings.html',{'active':'settings','form':form})

@guard('view_audit')
def history(request):return render(request,'portal/history.html',{'active':'history','records':Audit.objects.select_related('author').order_by('-id')[:200]})

@guard('view_inquiry')
@require_http_methods(['GET','POST'])
def inquiries(request):
    form=InquiryForm(request.POST or None)
    if request.method=='POST':
        if not request.user.has_perm('cms.add_inquiry'):return HttpResponseForbidden()
        if form.is_valid():
            row=form.save();audit(request,'建立手動查詢',str(row.reference));messages.success(request,'查詢紀錄已儲存。手動紀錄不會增加網站轉換數。');return redirect('inquiries')
    rows=Inquiry.objects.order_by('-id')
    if request.GET.get('status') in dict(Inquiry.STATUS):rows=rows.filter(status=request.GET['status'])
    return render(request,'portal/inquiries.html',{'active':'inquiries','rows':rows[:100],'form':form,'statuses':Inquiry.STATUS})

@guard('change_inquiry')
@require_POST
def inquiry_status(request,pk):
    row=get_object_or_404(Inquiry,pk=pk)
    if request.POST.get('status') in dict(Inquiry.STATUS):
        row.status=request.POST['status'];row.save();audit(request,'更新查詢狀態',str(row.reference))
    return redirect('inquiries')

@guard('delete_inquiry')
@require_POST
def inquiry_delete(request,pk):
    row=get_object_or_404(Inquiry,pk=pk);ref=str(row.reference);row.delete();audit(request,'刪除查詢',ref);messages.success(request,'查詢個人資料已刪除。');return redirect('inquiries')

def public_page(request,slug='index'):
    page=get_object_or_404(Page,slug=slug)
    preview=request.GET.get('preview')=='draft'
    if preview and (not request.user.is_staff or not request.user.has_perm('cms.view_page')):return HttpResponseForbidden()
    config=SiteSettings.objects.get(pk=1)
    html=content.render(slug,page.draft if preview else page.published,config.analytics_enabled and not request.user.is_staff and not preview)
    if preview:
        soup=BeautifulSoup(html,'html.parser')
        robots_tag=soup.select_one('meta[name="robots"]')
        if robots_tag:
            robots_tag['content']='noindex, nofollow, noarchive'
        else:
            soup.head.append(soup.new_tag('meta',attrs={'name':'robots','content':'noindex, nofollow, noarchive'}))
        canonical=soup.select_one('link[rel="canonical"]')
        if canonical: canonical.decompose()
        html=str(soup)
    seo=getattr(page,'seo',None)
    if seo and not preview:
        soup=BeautifulSoup(html,'html.parser')
        if seo.title and soup.title: soup.title.string=seo.title
        description=soup.select_one('meta[name="description"]')
        if seo.description and description: description['content']=seo.description
        robots=soup.select_one('meta[name="robots"]')
        if robots: robots['content']=('index' if seo.index else 'noindex')+', '+('follow' if seo.follow else 'nofollow')
        if seo.canonical:
            link=soup.select_one('link[rel="canonical"]')
            if not link: link=soup.new_tag('link',rel='canonical');soup.head.append(link)
            link['href']=seo.canonical
        for prop,value in [('og:title',seo.og_title),('og:description',seo.og_description)]:
            if value:
                tag=soup.select_one(f'meta[property="{prop}"]')
                if not tag: tag=soup.new_tag('meta',attrs={'property':prop});soup.head.append(tag)
                tag['content']=value
        html=str(soup)
    response=HttpResponse(html)
    response['Cache-Control']='no-store'
    return response

def custom_404(request, exception):
    """Serve the generated, noindex 404 page for unknown public paths."""
    page = content.site_dir() / '404.html'
    if page.is_file():
        response = HttpResponse(page.read_text())
    else:
        response = HttpResponse('<!doctype html><html lang="zh-HK"><title>找不到頁面｜快達通渠</title><h1>找不到這個頁面</h1><p><a href="/">返回首頁</a></p></html>')
    response.status_code = 404
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@require_GET
def public_media(request):
    """Return only published image assignments for the React homepage/runtime."""
    assignments = {}
    for page in Page.objects.all():
        for key, placement in page.published.get('images', {}).items():
            asset = MediaAsset.objects.filter(pk=placement.get('asset')).first()
            if not asset:
                continue
            assignments[f'{page.slug}:{key}'] = {
                'url': f'/media/{asset.pk}.webp',
                'alt': placement.get('alt') or asset.alt or asset.title,
                'width': asset.width,
                'height': asset.height,
            }
    response = JsonResponse({'media': assignments})
    response['Cache-Control'] = 'no-store'
    return response

def asset_file(request,pk):
    asset=get_object_or_404(MediaAsset,pk=pk)
    if not request.user.is_staff:
        used=any(str(pk)==p.get('asset') for page in Page.objects.all() for p in page.published.get('images',{}).values())
        if not used:raise Http404
    return FileResponse(asset.file.open('rb'),content_type='image/webp')

def site_asset(request, name=None, path=None, root=None):
    """Serve the generated public build and collected CMS assets safely."""
    relative = Path(path or name or '')
    if not relative.parts or '..' in relative.parts or relative.is_absolute():
        raise Http404
    if root:
        candidate = Path(settings.SITE_DIR) / root / relative
    elif path is not None and path.startswith('portal/'):
        candidate = Path(settings.STATIC_ROOT) / relative
    elif path is not None:
        candidate = Path(settings.SITE_DIR) / 'assets' / relative
    else:
        candidate = Path(settings.SITE_DIR) / relative
    try:
        candidate = candidate.resolve()
        root_path = (Path(settings.SITE_DIR).resolve() if root
                     else Path(settings.STATIC_ROOT).resolve()
                     if path is not None and path.startswith('portal/')
                     else Path(settings.SITE_DIR).resolve())
    except (OSError, ValueError):
        raise Http404
    if root_path not in candidate.parents and candidate != root_path:
        raise Http404
    if not candidate.is_file():
        raise Http404
    content_type = mimetypes.guess_type(candidate.name)[0] or 'application/octet-stream'
    return FileResponse(candidate.open('rb'), content_type=content_type)

def token(request):return JsonResponse({'token':get_token(request),'consent':request.get_signed_cookie('kt_consent',default='',salt='consent')})

@require_POST
def consent(request):
    if len(request.body)>1024:return JsonResponse({'error':'too large'},status=400)
    try:choice=json.loads(request.body).get('choice')
    except (ValueError,AttributeError):return JsonResponse({'error':'invalid'},status=400)
    if choice not in ('yes','no','reset'):return JsonResponse({'error':'invalid'},status=400)
    response=JsonResponse({'ok':True})
    if choice=='reset':response.delete_cookie('kt_consent')
    else:response.set_signed_cookie('kt_consent',choice,salt='consent',max_age=180*86400,httponly=True,secure=settings.PRODUCTION,samesite='Strict')
    if choice!='yes':response.delete_cookie('kt_visit')
    return response

@require_POST
def event(request):
    if not SiteSettings.objects.get(pk=1).analytics_enabled or request.user.is_staff or request.get_signed_cookie('kt_consent',default='',salt='consent')!='yes':return JsonResponse({'recorded':False})
    if len(request.body)>1024:return JsonResponse({'error':'too large'},status=400)
    if throttled('event-ip:'+request.META.get('REMOTE_ADDR',''),2000,3600):return JsonResponse({'error':'rate limit'},status=429)
    try:data=json.loads(request.body)
    except ValueError:return JsonResponse({'error':'invalid'},status=400)
    if not isinstance(data,dict) or set(data)!= {'event','page','device'}:return JsonResponse({'error':'invalid'},status=400)
    if not all(isinstance(value,str) for value in data.values()):return JsonResponse({'error':'invalid'},status=400)
    if data['event'] not in dict(Event.EVENT_TYPES) or data['page'] not in content.PAGE_NAMES or data['device'] not in ('mobile','tablet','desktop'):return JsonResponse({'error':'invalid'},status=400)
    sid=request.get_signed_cookie('kt_visit',default='',salt='visit',max_age=1800) or secrets.token_urlsafe(24)
    hashed=hmac.new(settings.SECRET_KEY.encode(),sid.encode(),hashlib.sha256).hexdigest()
    if throttled('event:'+hashed,120,60):return JsonResponse({'error':'rate limit'},status=429)
    Event.objects.create(session_hash=hashed,event=data['event'],page=data['page'],device=data['device'],environment='production' if settings.PRODUCTION else 'local')
    response=JsonResponse({'recorded':True})
    response.set_signed_cookie('kt_visit',sid,salt='visit',max_age=1800,httponly=True,secure=settings.PRODUCTION,samesite='Strict')
    return response

@login_required
def workspace(request):
    for permission, destination in [('view_event','dashboard'),('view_page','pages'),('view_mediaasset','media'),('view_inquiry','inquiries'),('change_sitesettings','settings')]:
        if request.user.is_staff and request.user.has_perm('cms.'+permission):return redirect(destination)
    return HttpResponseForbidden('此帳戶尚未分配工作權限，請聯絡管理員。')


MANAGERS={
    'blog': {'label':'Blog 文章','model':BlogPost,'form':BlogPostForm,'permission':'blogpost','active':'blog','title_field':'title'},
    'services': {'label':'服務頁','model':Service,'form':ServiceForm,'permission':'service','active':'services','title_field':'name'},
    'areas': {'label':'服務地區','model':ServiceArea,'form':ServiceAreaForm,'permission':'servicearea','active':'areas','title_field':'name'},
    'cases': {'label':'工程個案','model':CaseStudy,'form':CaseStudyForm,'permission':'casestudy','active':'cases','title_field':'title'},
    'reviews': {'label':'評價管理','model':Review,'form':ReviewForm,'permission':'review','active':'reviews','title_field':'display_name'},
    'campaigns': {'label':'宣傳活動','model':Campaign,'form':CampaignForm,'permission':'campaign','active':'campaigns','title_field':'name'},
}

def _can(request, action, model_name):
    return request.user.is_staff and request.user.has_perm(f'cms.{action}_{model_name}')

@login_required
def manager_list(request, kind):
    cfg=MANAGERS.get(kind)
    if not cfg or not _can(request,'view',cfg['permission']): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    model=cfg['model']; rows=model.objects.all()
    if hasattr(model,'deleted_at'): rows=rows.filter(deleted_at__isnull=True)
    q=request.GET.get('q','').strip()[:120]
    if q:
        field=cfg['title_field']; rows=rows.filter(**{f'{field}__icontains':q})
    return render(request,'portal/manager_list.html',{'active':cfg['active'],'kind':kind,'label':cfg['label'],'rows':rows,'config':cfg,'q':q})

@login_required
@require_http_methods(['GET','POST'])
def manager_edit(request, kind, pk=None):
    cfg=MANAGERS.get(kind)
    if not cfg: raise Http404
    action='change' if pk else 'add'
    if not _can(request,action,cfg['permission']): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    model=cfg['model']; instance=get_object_or_404(model,pk=pk) if pk else None
    if request.method=='POST':
        form=cfg['form'](request.POST,request.FILES,instance=instance)
        if form.is_valid():
            if kind == 'blog' and form.cleaned_data.get('status') == 'published' and not request.user.has_perm('cms.publish_blogpost'):
                form.add_error('status','只有獲授權發布角色可以發布文章。')
            if kind in ('services','areas','cases') and form.cleaned_data.get('status') == 'published' and not request.user.has_perm('cms.publish_page'):
                form.add_error('status','只有獲授權發布角色可以發布公開內容。')
            if form.errors:
                return render(request,'portal/manager_form.html',{'active':cfg['active'],'kind':kind,'label':cfg['label'],'form':form,'instance':instance,'config':cfg})
            row=form.save()
            if kind == 'blog' and row.status == 'published' and not row.published_at:
                row.published_at=timezone.now();row.save(update_fields=['published_at'])
            audit(request,('更新' if instance else '建立')+cfg['label'],str(row.pk))
            messages.success(request,f'{cfg["label"]}已儲存。')
            return redirect('manager-list',kind=kind)
    else: form=cfg['form'](instance=instance)
    return render(request,'portal/manager_form.html',{'active':cfg['active'],'kind':kind,'label':cfg['label'],'form':form,'instance':instance,'config':cfg})

@login_required
@require_POST
def manager_delete(request,kind,pk):
    cfg=MANAGERS.get(kind)
    if not cfg or not _can(request,'delete',cfg['permission']): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    row=get_object_or_404(cfg['model'],pk=pk)
    if hasattr(row,'deleted_at'):
        row.deleted_at=timezone.now();row.save(update_fields=['deleted_at','updated_at'])
    else: row.delete()
    audit(request,'封存'+cfg['label'],str(pk));messages.success(request,cfg['label']+'已封存。')
    return redirect('manager-list',kind=kind)

@login_required
def seo_manager(request):
    if not _can(request,'view','seo_metadata'): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    pages=Page.objects.order_by('name');posts=BlogPost.objects.filter(deleted_at__isnull=True).order_by('-updated_at')
    return render(request,'portal/seo.html',{'active':'seo','pages':pages,'posts':posts})

@login_required
@require_http_methods(['GET','POST'])
def seo_edit(request,target,pk):
    if not _can(request,'change','seo_metadata'): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    relation={'page':('page',Page),'post':('post',BlogPost)}.get(target)
    if not relation: raise Http404
    key,model=relation; obj=get_object_or_404(model,pk=pk)
    seo,created=SeoMetadata.objects.get_or_create(**{key:obj})
    if request.method=='POST':
        form=SeoMetadataForm(request.POST,request.FILES,instance=seo)
        if form.is_valid(): form.save();audit(request,'更新 SEO 設定',f'{target}:{pk}');messages.success(request,'SEO 設定已儲存。');return redirect('seo')
    else: form=SeoMetadataForm(instance=seo)
    return render(request,'portal/seo_form.html',{'active':'seo','form':form,'target':target,'obj':obj})

@login_required
@require_http_methods(['GET','POST'])
def integrations(request):
    if not _can(request,'view','integration'): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    for provider,label in Integration.PROVIDERS:
        Integration.objects.get_or_create(provider=provider)
    if request.method=='POST':
        row=get_object_or_404(Integration,pk=request.POST.get('pk'))
        if not _can(request,'change','integration'): return HttpResponseForbidden('你的帳戶沒有這項權限。')
        form=IntegrationForm(request.POST,instance=row)
        if form.is_valid(): form.save();audit(request,'更新整合設定',row.provider);messages.success(request,'整合設定已儲存；未設定憑證前不會顯示外部數據。');return redirect('integrations')
    return render(request,'portal/integrations.html',{'active':'integrations','rows':Integration.objects.order_by('provider')})

@login_required
def users(request):
    if not request.user.is_superuser: return HttpResponseForbidden('只有擁有者可以管理使用者。')
    return render(request,'portal/users.html',{'active':'users','users':get_user_model().objects.filter(is_staff=True).order_by('username')})

@login_required
@require_http_methods(['GET','POST'])
def notifications(request):
    if not _can(request,'view','notification'): return HttpResponseForbidden('你的帳戶沒有這項權限。')
    form=NotificationForm(request.POST or None)
    if request.method=='POST' and _can(request,'add','notification') and form.is_valid():
        row=form.save();audit(request,'建立通知 Banner',str(row.pk));messages.success(request,'通知 Banner 已儲存。');return redirect('notifications')
    return render(request,'portal/notifications.html',{'active':'notifications','rows':Notification.objects.order_by('-created_at'),'form':form})

def public_blog(request,slug=None):
    base=os.environ.get('SITE_URL','').rstrip('/') or request.build_absolute_uri('/').rstrip('/')
    posts=BlogPost.objects.filter(status='published',deleted_at__isnull=True)
    post=get_object_or_404(posts,slug=slug) if slug else None
    seo=getattr(post,'seo',None) if post else None
    title=(seo.title if seo and seo.title else post.title+'｜快達通渠') if post else '通渠文章及家居排水知識｜快達通渠'
    description=(seo.description if seo and seo.description else post.excerpt or post.content[:160]) if post else '閱讀快達通渠的通渠、家居排水保養及渠道檢查文章，了解常見問題和查詢安排。'
    canonical=(seo.canonical if seo and seo.canonical else base+'/blog/'+post.slug+'/') if post else base+'/blog/'
    index=(seo.index if seo else True) if post else posts.exists()
    follow=seo.follow if seo else True
    context={'post':post,'posts':posts.order_by('-published_at','-updated_at'), 'seo_title':title,
             'seo_description':description,'canonical':canonical,
             'robots':('index' if index else 'noindex')+', '+('follow' if follow else 'nofollow'),
             'og_title':seo.og_title if seo and seo.og_title else title,
             'og_description':seo.og_description if seo and seo.og_description else description}
    asset=(seo.og_image if seo and seo.og_image else post.cover) if post else None
    context['og_image']=base+'/media/'+str(asset.pk)+'.webp' if asset else base+'/media-assets/hero.webp'
    if post:
        BlogPost.objects.filter(pk=post.pk).update(views=F('views')+1)
        article={'@context':'https://schema.org','@type':'BlogPosting','headline':title,
                 'description':description,'url':canonical,'mainEntityOfPage':canonical,
                 'inLanguage':'zh-HK','author':{'@type':'Organization','name':'快達通渠','url':base+'/'},
                 'publisher':{'@type':'Organization','name':'快達通渠','url':base+'/'},
                 'dateModified':post.updated_at.isoformat()}
        if post.published_at: article['datePublished']=post.published_at.isoformat()
        if asset: article['image']=context['og_image']
        context['article_schema']=json.dumps(article,ensure_ascii=False).replace('<','\\u003c')
    return render(request,'portal/public_blog.html' if post else 'portal/public_blog_list.html',context)

@require_GET
def sitemap(request):
    from xml.sax.saxutils import escape
    base=os.environ.get('SITE_URL','').rstrip('/') or request.build_absolute_uri('/').rstrip('/')
    rows=[]
    for page in Page.objects.order_by('slug'):
        seo=getattr(page,'seo',None)
        if seo and not seo.index: continue
        url=base+'/' if page.slug=='index' else base+'/'+page.slug+'.html'
        if seo and seo.canonical and seo.canonical != url: continue
        rows.append((url,page.updated_at))
    for post in BlogPost.objects.filter(status='published',deleted_at__isnull=True).order_by('slug'):
        seo=getattr(post,'seo',None)
        if seo and (not seo.index or (seo.canonical and seo.canonical != base+'/blog/'+post.slug+'/')): continue
        rows.append((base+'/blog/'+post.slug+'/',post.updated_at))
    body=''.join(f'<url><loc>{escape(url)}</loc><lastmod>{date.date().isoformat()}</lastmod></url>' for url,date in rows)
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+body+'</urlset>',content_type='application/xml')

@require_GET
def robots(request):
    base=os.environ.get('SITE_URL','').rstrip('/') or request.build_absolute_uri('/').rstrip('/')
    return HttpResponse('User-agent: *\nDisallow: /manage/\nDisallow: /admin/\nDisallow: /api/\nDisallow: /*?preview=\nSitemap: '+base+'/sitemap.xml\n',content_type='text/plain')
