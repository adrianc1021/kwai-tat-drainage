'use strict';

(() => {
  const header = document.querySelector('.site-header');
  const hero = document.querySelector('.hero');
  const ruler = document.querySelector('.ruler');
  const value = document.querySelector('.ruler-value');
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#site-nav');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const closeMenu = () => {
    if (!menu || !nav) return;
    menu.setAttribute('aria-expanded', 'false');
    nav.classList.remove('open');
    menu.textContent = '選單';
  };

  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
      menu.textContent = open ? '關閉' : '選單';
    });
    menu.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
    nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  }

  const sections = [...document.querySelectorAll('[data-section]')];
  let ticking = false;

  function paint() {
    ticking = false;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const progress = Math.min(1, scrollY / max);
    ruler?.style.setProperty('--read', `${progress * 100}%`);
    if (value) value.textContent = `${Math.round(progress * 100)}%`;
    if (header && hero) {
      const dark = hero.getBoundingClientRect().bottom < 110;
      header.classList.toggle('light', dark);
    }
    for (const section of sections) {
      section.classList.toggle(
        'in-view',
        section.getBoundingClientRect().top < innerHeight * 0.6 && section.getBoundingClientRect().bottom > innerHeight * 0.2,
      );
    }
  }

  addEventListener('scroll', () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(paint);
    }
  }, { passive: true });
  addEventListener('resize', paint, { passive: true });
  paint();

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add('seen');
    });
  }, { threshold: 0.15 });
  document.querySelectorAll('.section-heading,.service-grid,.editorial-list,.steps,.contact-grid').forEach((element) => observer.observe(element));

  document.querySelectorAll('[data-channel]').forEach((link) => {
    link.addEventListener('click', () => {
      if (!link.href.includes('#telephone') && !link.href.includes('#whatsapp')) return;
      const hash = new URL(link.href, window.location.href).hash;
      const target = hash ? document.querySelector(hash) : null;
      if (!target) return;
      target.scrollIntoView({ behavior: reducedMotion.matches ? 'auto' : 'smooth' });
      target.focus({ preventScroll: true });
    });
  });
})();
