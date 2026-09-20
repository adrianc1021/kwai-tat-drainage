from django.http import HttpResponseForbidden
from django.conf import settings
class Headers:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        if not settings.PRODUCTION and request.META.get('REMOTE_ADDR','') not in ('127.0.0.1','::1',''):
            return HttpResponseForbidden('本機管理系統只接受本機連線。')
        from django.core.cache import cache
        if cache.add('retention-check',True,3600):
            from django.utils import timezone
            from datetime import timedelta
            from .models import Event, Throttle
            Event.objects.filter(created_at__lt=timezone.now()-timedelta(days=90)).delete()
            Throttle.objects.filter(start__lt=timezone.now()-timedelta(days=1)).delete()
        response=self.get_response(request)
        response['Referrer-Policy']='same-origin'
        response['X-Robots-Tag']='noindex, nofollow'
        response['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; form-action 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.path.startswith(('/manage','/admin','/api')) or 'preview' in request.GET:
            response['Cache-Control']='no-store'
        return response
