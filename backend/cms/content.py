from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings

from .models import MediaAsset, SiteSettings


# Keep this list aligned with the generated public build. The CMS never invents
# a page; it only exposes pages that already exist in the published website.
PAGE_NAMES = {
    'index': '首頁',
    'services': '服務範圍',
    'drainage': '家居通渠',
    'high-pressure': '高壓水力清洗',
    'cctv': 'CCTV 渠道檢查',
    'commercial': '商業及大廈渠務',
    'pricing': '報價流程',
    'areas': '服務地區',
    'cases': '工程案例',
    'tips': '通渠小知識',
    'about': '關於快達通渠',
    'faq': '常見問題',
    'contact': '聯絡查詢',
    'privacy': '私隱說明',
}


def site_dir():
    configured = getattr(settings, 'SITE_DIR', None)
    if configured:
        return Path(configured)
    return settings.PROJECT_DIR / 'production' / 'site'


def source(slug):
    return BeautifulSoup((site_dir() / f'{slug}.html').read_text(), 'html.parser')


def blocks(soup):
    # Text-only fields preserve DOM structure and never accept executable markup.
    candidates = soup.select('main h1, main h2, main h3, main p, main summary, main li')
    return {
        f'text_{i}': tag for i, tag in enumerate(candidates)
        if not tag.select('a, input, select, textarea, button, h2, h3, p, ul, ol')
    }


def initial(slug):
    soup = source(slug)
    description = soup.select_one('meta[name=description]')
    return {
        'title': soup.title.string if soup.title else '',
        'description': description.get('content', '') if description else '',
        'blocks': {
            key: {'label': tag.name, 'value': tag.get_text('\n', strip=True)}
            for key, tag in blocks(soup).items()
        },
        'images': {},
    }


def slots(slug):
    """Return image slots that exist in the current public build."""
    if slug == 'index':
        return {'hero_poster': ('首頁主視覺圖片', '.hero-media img')}
    soup = source(slug)
    values = {}
    for i, img in enumerate(soup.select('main img')):
        values[f'image_{i}'] = (
            img.get('alt') or f'內文圖片 {i + 1}',
            f'main img:nth-of-type({i + 1})',
        )
    return values


def render(slug, snapshot, tracking=False):
    soup = source(slug)
    title = soup.title
    description = soup.select_one('meta[name=description]')
    if title:
        title.string = snapshot.get('title', title.string)
    if description:
        description['content'] = snapshot.get('description', '')

    for key, tag in blocks(soup).items():
        value = snapshot.get('blocks', {}).get(key, {}).get('value')
        if value is not None and value != tag.get_text('\n', strip=True):
            tag.clear()
            for i, line in enumerate(value.split('\n')):
                if i:
                    tag.append(soup.new_tag('br'))
                tag.append(line)

    available_slots = slots(slug)
    for key, placement in snapshot.get('images', {}).items():
        if key not in available_slots:
            continue
        asset = MediaAsset.objects.filter(pk=placement.get('asset')).first()
        if not asset:
            continue
        imgs = soup.select('main img')
        if key.startswith('image_'):
            index = int(key.split('_', 1)[1])
            target = imgs[index] if index < len(imgs) else None
        else:
            target = soup.select_one(available_slots[key][1])
        if not target:
            continue
        img = soup.new_tag(
            'img',
            src=f'/media/{asset.pk}.webp',
            alt=placement.get('alt') or asset.alt or asset.title,
            width=str(asset.width),
            height=str(asset.height),
        )
        img['class'] = ['cms-image', f"crop-{placement.get('crop', 'center')}"]
        img['loading'] = 'eager' if key in ('hero', 'hero_poster') else 'lazy'
        if key in ('hero', 'hero_poster'):
            img['fetchpriority'] = 'high'
        target.replace_with(img)

    config = SiteSettings.objects.first()
    if config:
        announcement = soup.select_one('.announcement-copy')
        if announcement and config.announcement:
            announcement.string = config.announcement
        footer_note = soup.select_one('.footer-note')
        if footer_note and config.footer_note:
            footer_note.string = config.footer_note
        for link in soup.select('a[href]'):
            if link['href'] == 'contact.html#whatsapp' and config.whatsapp:
                link['href'] = 'https://wa.me/' + config.whatsapp
                link['aria-label'] = 'WhatsApp 查詢'
                link['data-event'] = 'whatsapp_click'
            elif link['href'] == 'contact.html#telephone' and config.telephone:
                link['href'] = 'tel:+' + config.telephone
                link['aria-label'] = '致電查詢'
                link['data-event'] = 'telephone_click'
        for link in soup.select('a[href="contact.html#whatsapp"]'):
            link['data-event'] = 'whatsapp_click'
        for link in soup.select('a[href="contact.html#telephone"]'):
            link['data-event'] = 'telephone_click'
        for key, value in [('telephone', config.telephone), ('whatsapp', config.whatsapp)]:
            target = soup.select_one(f'#{key} .pending')
            if target and value:
                target.string = '+' + value
        if config.telephone or config.whatsapp:
            for p in soup.select('#telephone p:not(.pending), #whatsapp p:not(.pending)'):
                p.string = '可透過以上聯絡方式了解安排；接收查詢不等於已確認派員。'

    if config and (config.telephone or config.whatsapp):
        foot = soup.select_one('.footer-grid > div:last-child p')
        if foot:
            foot.clear()
            foot.append('電話：' + ('+' + config.telephone if config.telephone else '【待確認】'))
            foot.append(soup.new_tag('br'))
            foot.append('WhatsApp：' + ('+' + config.whatsapp if config.whatsapp else '【待確認】'))

    for meta in soup.select('meta[http-equiv="Content-Security-Policy"]'):
        meta.decompose()
    soup.head.append(soup.new_tag('link', rel='stylesheet', href='/assets/portal/public.css'))
    if tracking:
        soup.head.append(soup.new_tag('script', src='/assets/portal/analytics.js', defer=True))
        banner = soup.new_tag('aside', attrs={
            'class': 'analytics-consent',
            'aria-label': '訪問統計設定',
            'data-consent': '',
        })
        banner.append('是否允許匿名訪問統計？只記錄頁面及查詢按鈕，不收集表單內容。')
        for label, choice in [('允許', 'yes'), ('略過', 'no')]:
            button = soup.new_tag('button', type='button', attrs={'data-choice': choice})
            button.string = label
            banner.append(button)
        a = soup.new_tag('a', href='/privacy.html#analytics-policy')
        a.string = '資料說明'
        banner.append(a)
        soup.body.append(banner)
    if slug == 'privacy':
        section = soup.new_tag('section', attrs={'class': 'container section', 'id': 'analytics-policy'})
        h = soup.new_tag('h2')
        h.string = '後端訪問統計'
        section.append(h)
        p = soup.new_tag('p')
        p.string = ('後端版在管理員啟用並取得你的允許後，使用 30 分鐘的隨機訪問識別 cookie '
                    '記錄頁面代號、裝置類別及查詢點擊。資料保留上限 90 日，不記錄 IP、完整網址、'
                    '搜尋參數、電話或表單內容。管理員及草稿預覽不計入。')
        section.append(p)
        b = soup.new_tag('button', type='button', attrs={'data-reset-consent': ''})
        b.string = '更改統計選擇'
        if tracking:
            section.append(b)
        if soup.main:
            soup.main.append(section)
    return str(soup)
