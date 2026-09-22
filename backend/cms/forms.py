from pathlib import Path
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import SiteSettings, Inquiry, MediaAsset, BlogPost, BlogCategory, BlogTag, SeoMetadata, Service, ServiceArea, CaseStudy, Review, Campaign, Integration, Notification
class SetupForm(UserCreationForm):
    class Meta:
        model=get_user_model()
        fields=['username','password1','password2']
class SettingsForm(forms.ModelForm):
    class Meta:
        model=SiteSettings
        fields=['telephone','whatsapp','announcement','footer_note','analytics_enabled']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['announcement'].required=False
        self.fields['footer_note'].required=False
    def clean_telephone(self): return self.number('telephone')
    def clean_whatsapp(self): return self.number('whatsapp')
    def number(self,key):
        value=self.cleaned_data[key].strip().replace(' ','').lstrip('+')
        if value and (not value.isascii() or not value.isdigit() or not 8<=len(value)<=15): raise forms.ValidationError('請填寫包含國際區號的 8–15 位數字，例如香港區號 852。')
        return value
class UploadForm(forms.Form):
    title=forms.CharField(label='圖片名稱',max_length=120,required=False,help_text='可留空，系統會使用檔案名稱。')
    alt=forms.CharField(label='替代文字',max_length=300,required=False,help_text='一般內容圖片建議填寫；裝飾圖片可留空，之後仍可編輯。')
    image=forms.ImageField(label='圖片檔案',help_text='只支援 JPG、PNG、WebP，上限 10 MB。系統會驗證、移除中繼資料並轉為 WebP。',widget=forms.ClearableFileInput(attrs={'accept':'.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp'}))

    def clean_title(self):
        title=self.cleaned_data.get('title','').strip()
        if title:return title
        upload=self.files.get('image')
        stem=Path(getattr(upload,'name','')).stem
        stem=re.sub(r'[\r\n\t]+',' ',stem).strip()
        return stem[:120] or '未命名圖片'

    def clean_image(self):
        value=self.cleaned_data['image']
        if value.size>10*1024*1024:raise forms.ValidationError('圖片不可超過 10 MB。')
        if value.image.format not in ['JPEG','PNG','WEBP']:raise forms.ValidationError('只支援 JPG、PNG 或 WebP，不接受 SVG、GIF 或可執行檔。')
        if value.image.width*value.image.height>25000000:raise forms.ValidationError('圖片不可超過 2,500 萬像素。')
        return value

class MediaAssetForm(forms.ModelForm):
    class Meta:
        model=MediaAsset
        fields=['title','alt','caption','tags']
        widgets={'caption':forms.Textarea(attrs={'rows':2})}
class InquiryForm(forms.ModelForm):
    class Meta:
        model=Inquiry
        fields=['name','phone','channel','message','status']
        widgets={'message':forms.Textarea(attrs={'rows':5})}

class BlogPostForm(forms.ModelForm):
    class Meta:
        model=BlogPost
        fields=['title','slug','excerpt','content','cover','category','tags','status','scheduled_at']
        widgets={'content':forms.Textarea(attrs={'rows':16,'class':'rich-editor','placeholder':'以清楚段落撰寫文章內容；發布前請核實服務資料。'}),'scheduled_at':forms.DateTimeInput(attrs={'type':'datetime-local'})}
    def clean_slug(self):
        value=self.cleaned_data['slug'].strip().lower()
        if not value: raise forms.ValidationError('請填寫 URL slug。')
        return value

class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model=BlogCategory; fields=['name','slug','description']

class SeoMetadataForm(forms.ModelForm):
    class Meta:
        model=SeoMetadata
        fields=['title','description','canonical','index','follow','og_title','og_description','og_image','primary_keywords','secondary_keywords','breadcrumb_title','schema_type']
        widgets={'description':forms.Textarea(attrs={'rows':3}),'og_description':forms.Textarea(attrs={'rows':3})}

class ServiceForm(forms.ModelForm):
    class Meta:
        model=Service; fields=['name','slug','summary','content','cover','emergency','price_note','status']
        widgets={'content':forms.Textarea(attrs={'rows':8})}

class ServiceAreaForm(forms.ModelForm):
    class Meta:
        model=ServiceArea; fields=['name','slug','region','content','service_hours','status']
        widgets={'content':forms.Textarea(attrs={'rows':8})}

class CaseStudyForm(forms.ModelForm):
    class Meta:
        model=CaseStudy; fields=['title','slug','date','area','service','problem','method','duration','before','after','consent','anonymized','testimonial','status']
        widgets={'date':forms.DateInput(attrs={'type':'date'}),'problem':forms.Textarea(attrs={'rows':4}),'method':forms.Textarea(attrs={'rows':4}),'testimonial':forms.Textarea(attrs={'rows':3})}

class ReviewForm(forms.ModelForm):
    class Meta:
        model=Review; fields=['display_name','source','body','review_date','consent','status']
        widgets={'review_date':forms.DateInput(attrs={'type':'date'}),'body':forms.Textarea(attrs={'rows':5})}

class CampaignForm(forms.ModelForm):
    class Meta:
        model=Campaign; fields=['name','landing_page','banner','offer','cta','utm_campaign','starts_at','ends_at','budget','notes','status']
        widgets={'offer':forms.Textarea(attrs={'rows':4}),'notes':forms.Textarea(attrs={'rows':3}),'starts_at':forms.DateTimeInput(attrs={'type':'datetime-local'}),'ends_at':forms.DateTimeInput(attrs={'type':'datetime-local'})}

class IntegrationForm(forms.ModelForm):
    class Meta:
        model=Integration; fields=['enabled','property_id']

class NotificationForm(forms.ModelForm):
    class Meta:
        model=Notification; fields=['title','body','level','starts_at','ends_at','enabled']
        widgets={'body':forms.Textarea(attrs={'rows':3}),'starts_at':forms.DateTimeInput(attrs={'type':'datetime-local'}),'ends_at':forms.DateTimeInput(attrs={'type':'datetime-local'})}
