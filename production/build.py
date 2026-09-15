"""Build the allowlisted public site. No internal files or credentials are copied."""
import argparse, html, json, os, re, shutil
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'content.json').read_text())
PAGES={p['slug']:p for p in DATA['pages']}
OUT=ROOT/'site'
ESC=lambda s:html.escape(str(s),quote=True)
def href(slug): return '/'+('' if slug=='index' else slug+'.html')
def copy(key,text,tag='p',cls=''):
 return f'<{tag} data-copy="{ESC(key)}"'+(f' class="{cls}"' if cls else '')+'>'+ESC(text).replace('\n','<br>')+f'</{tag}>'
def link(slug,label,cls='text-link'):return f'<a class="{cls}" href="{href(slug)}">{ESC(label)}</a>'
def cta(kind='whatsapp',label=None,location='body'):
 label=label or ('WhatsApp 傳送現場照片' if kind=='whatsapp' else '致電查詢')
 num=DATA.get(kind,'')
 url=('https://wa.me/'+num+'?text='+quote('你好，我想查詢通渠服務。')) if num and kind=='whatsapp' else ('tel:+'+num if num else '/contact.html#'+kind)
 symbol='↗' if kind=='whatsapp' else '↗'
 return f'<a class="button {"primary" if kind=="whatsapp" else "secondary"}" href="{ESC(url)}" data-channel="{kind}" data-location="{location}"'+(f' data-event="{kind}_click"' if num else '')+f' aria-label="{ESC(label)}">{ESC(label)}<span aria-hidden="true">{symbol}</span></a>'
def phone_display(num):
 if len(num)==11 and num.startswith('852'): return '+852 '+num[3:7]+' '+num[7:]
 return '+'+num if num else '電話查詢'
def actions(location='body'):return '<div class="actions">'+cta(location=location)+cta('telephone',location=location)+'</div>'
def photo(key,slot,eager=False):
 alt={'hero':'沙井蓋金屬紋理','nozzle':'金屬噴嘴素材近照','cctv':'渠管內壁素材示意','tunnel':'渠管內部素材示意'}[key]
 return f'<img src="/media-assets/{key}.webp" alt="{alt}，非公司工程紀錄" data-media="{slot}" width="1400" height="1000" loading="{"eager" if eager else "lazy"}" decoding="async"'+(' fetchpriority="high"' if eager else '')+'>'
SERVICES=[('drainage','家居通渠','坐廁、鋅盆、浴室或地台去水不暢，先了解受影響的位置。'),('high-pressure','高壓水力清洗','了解高壓清洗用途，以及使用前需要確認的現場條件。'),('cctv','CCTV 渠道檢查','渠道反覆淤塞或原因不明，可先查詢鏡頭檢查。'),('commercial','商業及大廈渠務','商舖、食肆或公共渠道問題，先確認範圍及出入安排。')]
PAGE_VISUALS={'services':'nozzle','drainage':'hero','high-pressure':'nozzle','cctv':'cctv','commercial':'tunnel','pricing':'hero','areas':'hero','about':'cctv','faq':'tunnel','contact':'hero','privacy':'tunnel'}
STEPS=[('提供資料','說明地址、淤塞位置及現場情況。'),('客服了解情況','整理資料，確認查詢及出入安排。'),('確認到場安排','客服確認人手後，提供預計到場時間。'),('到場檢查','師傅了解現場，再說明可行方法及報價。'),('確認後施工','確認工程內容和收費後，才開始施工。')]
PROBLEMS=[('坐廁淤塞','沖水後水位升高還是退水慢？其他去水口是否正常？','drainage'),('鋅盆或廚房去水慢','積水持續多久？有沒有異味或曾清理去水隔？','drainage'),('浴室或地台淤塞','哪個去水口積水？洗澡後會否長時間未能去水？','drainage'),('渠道反覆淤塞','上次何時處理？採用甚麼方法？多久後再次淤塞？','cctv'),('商舖或食肆渠道','哪些去水位置受影響？有沒有油隔及營業時段限制？','commercial'),('大廈公共渠道','受影響的樓層及公共位置在哪裏？管理處是否已知悉？','commercial')]
def render_section(sec,slug,section_index=0):
 key=sec['id'];kind=sec.get('kind','');out=f'<section class="section {"dark-section" if kind=="problems" else ""}" id="{key}" data-section="{ESC(sec["heading"].replace(chr(10)," "))}"><div class="container">'
 visual=PAGE_VISUALS.get(slug) if section_index==0 and slug not in ('index','privacy') else None
 side='<div class="section-heading__side">'+''.join(copy(key+'-intro-'+str(i),b) for i,b in enumerate(sec.get('body',[])))
 if visual:
  side+=f'<figure class="section-heading-media">{photo(visual,slug+"-section",False)}<figcaption>渠務材質示意</figcaption></figure>'
 side+='</div>'
 out+='<div class="section-heading">'+copy(key+'-title',sec['heading'],'h2')+side+'</div>'
 if kind=='services':
  out+='<div class="service-grid">'
  for target,title,body in SERVICES:out+='<article>'+copy(key+'-'+target+'-title',title,'h3')+copy(key+'-'+target+'-body',body)+link(target,'了解'+title)+'</article>'
  out+='</div>'
 if kind=='problems':
  out+='<div class="problem-layout"><aside class="emergency">'+copy('emergency-title','渠道倒灌或污水外溢？','h3')+copy('emergency-text','建議直接致電，不必等文字回覆。')+cta('telephone')+'</aside><div class="problem-list">'
  for i,(title,question,target) in enumerate(PROBLEMS):out+='<details>'+copy('problem-'+str(i),title,'summary')+'<div class="answer">'+copy('problem-'+str(i)+'-answer',question)+link(target,'查看相關服務')+'</div></details>'
  out+='<div class="uncertain">'+copy('uncertain-title','不確定是哪種問題？','h3')+copy('uncertain-body','可先提供現場照片，讓客服了解情況。')+cta()+'</div></div></div>'
 if kind=='facts':
  out+='<dl class="facts"><div><dt>香港渠務經驗</dt><dd>50<span>年以上</span></dd></div><div><dt>通渠師傅</dt><dd>8<span>名</span></dd></div><div><dt>服務車</dt><dd>3<span>輛</span></dd></div></dl>'
  if slug=='index':out+='<p>'+link('about','了解快達通渠')+'</p>'
 if kind=='steps':
  out+='<ol class="steps">'
  for i,(title,body) in enumerate(STEPS):out+='<li>'+copy('step-'+str(i)+'-title',title,'h3')+copy('step-'+str(i)+'-body',body)+'</li>'
  out+='</ol>'
  if slug=='index':out+='<p>'+link('pricing','查看收費及上門安排')+'</p>'
 if kind=='quote-cards':
  out+='<div class="quote-card-grid">'
  for i,card in enumerate(sec.get('cards',[])):
   n=f'{i+1:02d}'
   out+='<article class="quote-card quote-card--'+n+'">'
   out+='<div class="quote-card__media" aria-hidden="true"><span class="quote-card__step">'+n+'</span><span class="quote-card__media-label">'+ESC(card.get('media','現場資料'))+'</span></div>'
   out+='<div class="quote-card__content"><div class="quote-card__badge"><span class="quote-card__icon" aria-hidden="true">'+('<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 1.5"/></svg>' if i==0 else '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5"/><path d="M5 8h6M8 5v6"/></svg>' if i==1 else '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5"/><path d="M5 8h6M5 5h6M5 11h4"/></svg>' if i==2 else '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5"/><path d="m5 8 2 2 4-4"/></svg>')+'</span>'+ESC(card.get('label',''))+'</div>'
   out+='<div class="quote-card__body"><h3>'+ESC(card.get('title',''))+'</h3><ul>'
   for bullet in card.get('bullets',[]):out+='<li>'+ESC(bullet)+'</li>'
   out+='</ul></div><a class="quote-card__link" href="#process">了解下一步<span aria-hidden="true">→</span></a></div></article>'
  out+='</div>'
 if kind=='clarity-cards':
  out+='<div class="clarity-card-grid">'
  for i,card in enumerate(sec.get('cards',[])):
   out+='<article class="clarity-card"><span class="clarity-card__number">'+f'{i+1:02d}'+'</span><h3>'+ESC(card.get('title',''))+'</h3><p>'+ESC(card.get('body',''))+'</p></article>'
  out+='</div>'
 if kind=='faq':
  out+='<div class="faq-list">'
  for i,(q,a) in enumerate(DATA['faq']):out+='<details>'+copy('faq-'+str(i)+'-q',q,'summary')+'<div class="answer">'+copy('faq-'+str(i)+'-a',a)+'</div></details>'
  out+='</div>'
 if kind=='contact':
  out+='<div class="contact-grid">'
  for channel,title,body in [('whatsapp','WhatsApp 查詢','可傳送淤塞位置及現場照片。'),('telephone','電話查詢','現場倒灌或污水外溢，建議直接致電。')]:
   out+=f'<article id="{channel}">'+copy(channel+'-title',title,'h3')+copy(channel+'-body',body)
   if DATA.get(channel):out+=f'<p class="contact-number">+{ESC(DATA[channel])}</p>'+cta(channel)
   else:out+='<p class="contact-pending">聯絡號碼待填</p><p class="small">目前為預覽，尚未啟用此聯絡方式。</p>'
   out+='</article>'
  out+='</div>'
 if kind=='consent':out+='<button type="button" class="button secondary" data-reset-consent hidden>更改統計選擇</button>'
 if sec.get('items'):
  out+='<div class="editorial-list">'
  for i,(title,body) in enumerate(sec['items']):out+='<article>'+copy(key+'-item-'+str(i)+'-title',title,'h3')+copy(key+'-item-'+str(i)+'-body',body)+'</article>'
  out+='</div>'
 if sec.get('list'):
  out+='<ul class="checklist">'+''.join(copy(key+'-list-'+str(i),t,'li') for i,t in enumerate(sec['list']))+'</ul>'
 if sec.get('links'):out+='<div class="related-links">'+''.join(link(target,title) for title,target in sec['links'])+'</div>'
 return out+'</div></section>'
def schema(page):
 url=DATA.get('site_url','').rstrip('/')
 if not url:return ''
 page_url=url+href(page['slug'])
 org={'@type':'Organization','@id':url+'/#organization','name':DATA['brand'],'url':url+'/' }
 if DATA.get('telephone'):
  org['telephone']='+'+DATA['telephone']
  org['contactPoint']={'@type':'ContactPoint','telephone':'+'+DATA['telephone'],'contactType':'customer service','availableLanguage':['zh-HK']}
 website={'@type':'WebSite','@id':url+'/#website','url':url+'/','name':DATA['brand'],'inLanguage':'zh-HK','publisher':{'@id':org['@id']}}
 webpage={'@type':'WebPage','@id':page_url+'#webpage','url':page_url,'name':page['title'],'description':page['description'],'inLanguage':'zh-HK','isPartOf':{'@id':website['@id']},'about':{'@id':org['@id']}}
 graph=[org,website,webpage]
 if page['slug']!='index':
  trail=[('index','首頁')]
  if page.get('parent'):trail.append((page['parent'],PAGES[page['parent']]['name']))
  trail.append((page['slug'],page['name']))
  graph.append({'@type':'BreadcrumbList','@id':page_url+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i+1,'name':n,'item':url+href(sl)} for i,(sl,n) in enumerate(trail)]})
 if page.get('parent')=='services':
  graph.append({'@type':'Service','@id':page_url+'#service','name':page['name'],'description':page['lead'],'url':page_url,'provider':{'@id':org['@id']}})
 if page['slug']=='faq':
  graph.append({'@type':'FAQPage','@id':page_url+'#faq','url':page_url,'name':page['title'],'inLanguage':'zh-HK','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in DATA['faq']]})
 if page['slug']=='pricing':
  graph.append({'@type':'HowTo','@id':page_url+'#howto','name':'快達通渠報價流程','description':page['lead'],'url':page_url,'inLanguage':'zh-HK','step':[{'@type':'HowToStep','position':i+1,'name':title,'text':body,'url':page_url+'#process'} for i,(title,body) in enumerate(STEPS)]})
 return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<','\\u003c')+'</script>'

def _upsert_meta(document, pattern, tag):
 match=re.search(pattern,document,re.I)
 if match:return document[:match.start()]+tag+document[match.end():]
 return document.replace('</head>',tag+'</head>',1)

def inject_home_head(path,public=False):
 page=PAGES['index'];document=path.read_text()
 document=re.sub(r'<title>.*?</title>','<title>'+ESC(page['title'])+'</title>',document,count=1,flags=re.I|re.S)
 document=_upsert_meta(document,r'<meta\s+name=["\']description["\'][^>]*>','<meta name="description" content="'+ESC(page['description'])+'">')
 document=_upsert_meta(document,r'<meta\s+name=["\']author["\'][^>]*>','<meta name="author" content="'+ESC(DATA['brand'])+'">')
 document=_upsert_meta(document,r'<meta\s+name=["\']robots["\'][^>]*>','<meta name="robots" content="'+('index,follow' if public else 'noindex,nofollow')+'">')
 document=_upsert_meta(document,r'<meta\s+name=["\']theme-color["\'][^>]*>','<meta name="theme-color" content="#070808">')
 for prop,value in [('og:title',page['title']),('og:description',page['description']),('og:type','website'),('og:locale','zh_HK'),('og:site_name',DATA['brand'])]:
  document=_upsert_meta(document,rf'<meta\s+property=["\']{re.escape(prop)}["\'][^>]*>','<meta property="'+prop+'" content="'+ESC(value)+'">')
 document=_upsert_meta(document,r'<meta\s+name=["\']twitter:card["\'][^>]*>','<meta name="twitter:card" content="summary">')
 if 'href="/video-poster.jpg"' not in document:
  document=document.replace('</head>','<link rel="preload" as="image" href="/video-poster.jpg">'+'</head>',1)
 if DATA.get('site_url'):
  canonical=DATA['site_url'].rstrip('/')+'/'
  document=_upsert_meta(document,r'<link\s+rel=["\']canonical["\'][^>]*>','<link rel="canonical" href="'+ESC(canonical)+'">')
  document=_upsert_meta(document,r'<meta\s+property=["\']og:url["\'][^>]*>','<meta property="og:url" content="'+ESC(canonical)+'">')
  image=DATA['site_url'].rstrip('/')+'/video-poster.jpg'
  document=_upsert_meta(document,r'<meta\s+property=["\']og:image["\'][^>]*>','<meta property="og:image" content="'+ESC(image)+'">')
  document=_upsert_meta(document,r'<meta\s+name=["\']twitter:image["\'][^>]*>','<meta name="twitter:image" content="'+ESC(image)+'">')
 document=document.replace('</head>',schema(page)+'</head>',1)
 path.write_text(document)
def render(page,public=False):
 slug=page['slug'];home=slug=='index';canonical=DATA.get('site_url','').rstrip('/')+href(slug)
 title=ESC(page['title']);desc=ESC(page['description']);nav=[('/#problems','問題分流'),('/#services','服務'),('/about.html','關於快達通渠'),('/pricing.html','報價流程'),('/#faq','常見問題')]
 head=f'<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101416"><title>{title}</title><meta name="description" content="{desc}"><meta name="author" content="{ESC(DATA["brand"])}"><meta name="robots" content="{"index,follow" if public else "noindex,nofollow"}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/theme.css"><link rel="preload" as="font" type="font/ttf" href="/media-assets/noto-hk.ttf" crossorigin><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="website"><meta property="og:locale" content="zh_HK"><meta property="og:site_name" content="{ESC(DATA["brand"])}"><meta name="twitter:card" content="summary">'
 if DATA.get('site_url'):
  head+=f'<link rel="canonical" href="{ESC(canonical)}"><meta property="og:url" content="{ESC(canonical)}"><meta property="og:image" content="{ESC(DATA["site_url"].rstrip("/")+"/video-poster.jpg")}"><meta name="twitter:image" content="{ESC(DATA["site_url"].rstrip("/")+"/video-poster.jpg")}">' 
 head+=schema(page)+'</head>'
 body=f'<body data-page="{slug}" class="{"home" if home else "inner"}"><a class="skip-link" href="#main">跳至主要內容</a><header class="floating-nav"><div class="nav-inner"><a class="brand-mark" href="/" aria-label="快達通渠首頁"><span class="brand-mark__dot" aria-hidden="true"></span><span>快達通渠</span></a><nav id="site-nav" class="desktop-nav" aria-label="主要導航">'
 for url,n in nav:body+=f'<a href="{url}"'+(' aria-current="page"' if n==page['name'] or (n=='服務' and (slug=='services' or page.get('parent')=='services')) else '')+f'>{n}</a>'
 body+='</nav><div class="nav-actions"><a class="nav-phone" href="tel:+'+ESC(DATA.get('telephone',''))+'" aria-label="致電快達通渠">'+ESC(phone_display(DATA.get('telephone','')) )+'</a>'+cta('whatsapp','WhatsApp','header')+'<button class="menu-toggle" type="button" aria-controls="site-nav" aria-expanded="false"><span class="sr-only">開啟選單</span><span aria-hidden="true"></span><span aria-hidden="true"></span></button></div></div></header><main id="main">'
 if home:
  body+='<div class="hero-stage"><section class="hero" data-section="首頁"><div class="hero-media">'+photo('hero','home-hero',True)+'</div><img class="pipe-art" src="/media-assets/pipe.svg" width="1000" height="700" alt="" aria-hidden="true"><div class="hero-copy container">'
 else:
  visual=page.get('image') or PAGE_VISUALS.get(slug,'hero')
  body+='<section class="page-hero"><div class="page-hero__media" aria-hidden="true">'+photo(visual,slug+'-hero',True)+'</div><div class="container page-hero__inner"><nav class="breadcrumbs" aria-label="所在位置"><a href="/">首頁</a><span aria-hidden="true">／</span>'
  if page.get('parent'):body+=link(page['parent'],PAGES[page['parent']]['name'])+'<span aria-hidden="true">／</span>'
  body+='<span aria-current="page">'+ESC(page['name'])+'</span></nav>'
 body+=copy('eyebrow',page['eyebrow'],'p','eyebrow')+'<h1>'
 for i,line in enumerate(page['heading']):body+=copy('heading-'+str(i),line,'span','title-line'+(' secondary-line' if i else ''))
 body+='</h1>'+copy('lead',page['lead'],'p','lead')
 if not home:body+=actions('hero')
 if home:body+='<ul class="tags" aria-label="常見問題位置">'+''.join('<li>'+t+'</li>' for t in ['坐廁','鋅盆','浴室地台','廚房油隔','沙井','大廈公共渠'])+'</ul>'+actions('hero')+copy('hero-condition','24 小時接受緊急查詢。客服確認安排後，會提供預計到場時間。','p','condition')+'</div><p class="hero-caption">管段及攝影材質示意，非公司工程紀錄</p></section></div>'
 else:body+='<div class="page-hero__tagline" aria-label="查詢提示"><span>先說位置，再安排處理方法</span><span aria-hidden="true">／</span><span>24 小時接受查詢</span></div></div></section>'
 for section_index,sec in enumerate(page['sections']):body+=render_section(sec,slug,section_index)
 if not home:
  if page.get('parent')=='services':body+='<aside class="section related-services"><div class="container"><h2>其他服務</h2><div class="related-links">'+''.join(link(t,n) for t,n,_ in SERVICES if t!=slug)+'</div></div></aside>'
 if slug not in ('contact','privacy'):
  body+='<section class="final-contact section" data-section="聯絡查詢"><div class="container final-grid"><div>'+copy('final-title','有渠道問題？\n聯絡查詢上門安排','h2')+copy('final-body','先說明位置及現場情況。客服確認後，再安排師傅。')+'</div>'+actions('footer')+'</div></section>'
 body+='</main><footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/">快達通渠</a><p>香港通渠及渠務服務<br>24 小時接受緊急查詢</p></div><nav aria-label="服務頁面">'+''.join(link(t,n) for t,n,_ in SERVICES)+'</nav><nav aria-label="網站資訊">'+''.join(link(t,PAGES[t]['name']) for t in ['areas','pricing','about','faq','contact','privacy'])+'</nav></div><div class="container footer-bottom"><p>© 快達通渠</p>'+('<p class="preview-label">網站預覽 · 聯絡資料及正式發布設定待完成</p>' if not public else '')+'<a href="#main">返回頁首</a></div><div class="container credits"><details><summary>素材來源</summary><p>以下素材經裁切及去色處理，非快達通渠的工程、人員或設備紀錄。</p><ul><li>沙井蓋：Tomwsulcer，CC0</li><li><a href="https://commons.wikimedia.org/wiki/File:Water_jet_cutting_nozzles.jpg">金屬噴嘴：Hammelmann Oelde</a>，CC BY-SA 3.0</li><li><a href="https://commons.wikimedia.org/wiki/File:Close_up_view_inside_of_a_culvert_in_Shasta-Trinity_National_Forest.jpg">渠管內壁：Shopstone</a>，CC0</li></ul></details></div></footer><nav class="mobile-contact" aria-label="快捷聯絡">'+cta('telephone',location='mobile')+cta('whatsapp','WhatsApp 查詢','mobile')+'</nav><script src="/site.js" defer></script></body></html>'
 return head+body

def build(public=False):
 for key,env in [('site_url','SITE_URL'),('telephone','SITE_PHONE'),('whatsapp','SITE_WHATSAPP')]:
  if os.environ.get(env):DATA[key]=os.environ[env]
 if DATA['site_url'] and not re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::\d+)?',DATA['site_url'].rstrip('/')):raise SystemExit('SITE_URL must be an HTTPS origin.')
 for key in ('telephone','whatsapp'):
  if DATA[key] and not re.fullmatch(r'[1-9][0-9]{7,14}',DATA[key]):raise SystemExit('Invalid international phone format: '+key)
 if public and not all(DATA[k] for k in ['site_url','telephone','whatsapp']):raise SystemExit('Public build requires SITE_URL, SITE_PHONE and SITE_WHATSAPP. No placeholders will be published.')
 if public and os.environ.get('PUBLISH_CONFIRMED')!='1':raise SystemExit('Public build requires PUBLISH_CONFIRMED=1 after final privacy/content and contact checks.')
 OUT.mkdir(exist_ok=True)
 for page in DATA['pages']:(OUT/(page['slug']+'.html')).write_text(render(page,public))
 react_dist=ROOT.parent/'react-hero'/'dist'
 if (react_dist/'index.html').exists():
  shutil.copyfile(react_dist/'index.html',OUT/'index.html')
  if (react_dist/'assets').exists():shutil.copytree(react_dist/'assets',OUT/'assets',dirs_exist_ok=True)
  if (react_dist/'hero-poster.svg').exists():shutil.copyfile(react_dist/'hero-poster.svg',OUT/'hero-poster.svg')
  if (react_dist/'video-poster.jpg').exists():shutil.copyfile(react_dist/'video-poster.jpg',OUT/'video-poster.jpg')
  if (react_dist/'628ab254756a.mp4').exists():shutil.copyfile(react_dist/'628ab254756a.mp4',OUT/'628ab254756a.mp4')
  else:
   (OUT/'index.html').write_text(render(PAGES['index'],public))
  inject_home_head(OUT/'index.html',public)
 for name in ['theme.css','site.js','favicon.svg']:shutil.copyfile(ROOT/name,OUT/name)
 media=OUT/'media-assets';media.mkdir(exist_ok=True)
 for name in ['noto-hk.ttf','hero.webp','nozzle.webp','cctv.webp','pipe.svg']:shutil.copyfile(ROOT/'assets'/name,media/name)
 robots='User-agent: *\nDisallow: /manage/\nDisallow: /admin/\nDisallow: /api/\n'
 if public:robots+='Sitemap: '+DATA['site_url'].rstrip('/')+'/sitemap.xml\n'
 (OUT/'robots.txt').write_text(robots)
 urls=''.join('<url><loc>'+ESC(DATA['site_url'].rstrip('/')+href(p['slug']))+'</loc></url>' for p in DATA['pages']) if public else ''
 (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>')
 error=dict(slug='404',name='找不到頁面',title='找不到頁面｜快達通渠',description='此頁面不存在。請返回首頁或查詢通渠服務。',eyebrow='404',heading=['找不到這個頁面'],lead='網址可能有誤，或頁面已更新。你可以返回首頁，或前往聯絡頁查詢。',sections=[])
 (OUT/'404.html').write_text(render(error,False))
 manifest={'pages':{p['slug']:p['name'] for p in DATA['pages']},'public':public,'site_url':DATA['site_url'],'version':'2026-09-14'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('Built',len(DATA['pages']),'pages + 404;', 'public' if public else 'preview')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true');args=parser.parse_args();build(args.public)
