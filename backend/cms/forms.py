from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import SiteSettings, Inquiry
class SetupForm(UserCreationForm):
    class Meta:
        model=get_user_model()
        fields=['username','password1','password2']
class SettingsForm(forms.ModelForm):
    class Meta:
        model=SiteSettings
        fields=['telephone','whatsapp','analytics_enabled']
    def clean_telephone(self): return self.number('telephone')
    def clean_whatsapp(self): return self.number('whatsapp')
    def number(self,key):
        value=self.cleaned_data[key].strip().replace(' ','').lstrip('+')
        if value and (not value.isascii() or not value.isdigit() or not 8<=len(value)<=15): raise forms.ValidationError('請填寫包含國際區號的 8–15 位數字，例如香港區號 852。')
        return value
class UploadForm(forms.Form):
    title=forms.CharField(label='圖片名稱',max_length=120)
    alt=forms.CharField(label='替代文字',max_length=300,help_text='描述圖片內容，方便讀屏使用者理解。')
    image=forms.ImageField(label='圖片檔案',help_text='JPG、PNG、WebP，上限 10 MB。系統會驗證、移除中繼資料並轉為 WebP。')
    def clean_image(self):
        value=self.cleaned_data['image']
        if value.size>10*1024*1024:raise forms.ValidationError('圖片不可超過 10 MB。')
        if value.image.format not in ['JPEG','PNG','WEBP']:raise forms.ValidationError('只支援 JPG、PNG 或 WebP，不接受 SVG、GIF 或可執行檔。')
        if value.image.width*value.image.height>25000000:raise forms.ValidationError('圖片不可超過 2,500 萬像素。')
        return value
class InquiryForm(forms.ModelForm):
    class Meta:
        model=Inquiry
        fields=['name','phone','channel','message','status']
        widgets={'message':forms.Textarea(attrs={'rows':5})}
