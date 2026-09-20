'use strict';

(() => {
  document.documentElement.classList.add('js-ready');
  const header = document.querySelector('.floating-nav');
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#site-nav');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const closeMenu = () => {
    if (!menu || !nav) return;
    menu.setAttribute('aria-expanded', 'false');
    nav.classList.remove('open');
  };

  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        closeMenu();
        menu.focus();
      }
    });
    nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  }

  const sections = [...document.querySelectorAll('[data-section]')];
  let ticking = false;

  function paint() {
    ticking = false;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const progress = Math.min(1, scrollY / max);
    if (header) header.classList.toggle('floating-nav--scrolled', scrollY > 72);
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
      if (entry.isIntersecting) {
        entry.target.classList.add('seen');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.page-hero__inner,.section-heading,.service-grid,.editorial-list,.facts,.steps,.checklist,.contact-grid,.quote-card-grid,.clarity-card-grid,.media-card-grid').forEach((element) => observer.observe(element));

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
