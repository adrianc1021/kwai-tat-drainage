'use strict';
(async () => {
  const banner = document.querySelector('[data-consent]');
  if (!banner) return;
  let allowed = false, csrf = '';
  const page = location.pathname.split('/').pop().replace('.html','') || 'index';
  const device = innerWidth < 700 ? 'mobile' : innerWidth < 1100 ? 'tablet' : 'desktop';
  const send = (path,body) => fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},credentials:'same-origin',body:JSON.stringify(body),keepalive:true});
  const track = event => {if (allowed) send('/api/event/',{event,page,device}).catch(()=>{});};
  try {
    const response = await fetch('/api/token/',{credentials:'same-origin',cache:'no-store'});
    if (!response.ok) return;
    const data = await response.json();csrf = data.token;allowed = data.consent === 'yes';
    banner.hidden = Boolean(data.consent);
    if (allowed) track('page_view');
    for (const button of banner.querySelectorAll('[data-choice]')) button.addEventListener('click',async () => {
      button.disabled = true;
      try {
        const result = await send('/api/consent/',{choice:button.dataset.choice});
        if (!result.ok) throw new Error('consent');
        allowed = button.dataset.choice === 'yes';banner.hidden = true;
        if (allowed) track('page_view');
      } catch {button.disabled = false;}
    });
    for (const link of document.querySelectorAll('[data-event]')) link.addEventListener('click', () => track(link.dataset.event));
    document.querySelector('[data-reset-consent]')?.addEventListener('click', async () => {
      const result = await send('/api/consent/',{choice:'reset'});
      if(result.ok){allowed = false;banner.hidden = false;banner.querySelector('button').focus();}
    });
  } catch {banner.hidden = true;}
})();
