'use strict';
for (const form of document.querySelectorAll('form[data-confirm]')) {
  form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
}
let dirty = false;
for (const form of document.querySelectorAll('[data-dirty-form]')) {
  form.addEventListener('input', () => {dirty = true;});
  form.addEventListener('change', () => {dirty = true;});
  form.addEventListener('submit', () => {dirty = false;});
}
window.addEventListener('beforeunload', event => {
  if (dirty) {event.preventDefault();event.returnValue = '';}
});
const shell = document.querySelector('.shell');
for (const trigger of document.querySelectorAll('[data-nav-open]')) trigger.addEventListener('click', () => shell?.classList.add('nav-open'));
for (const trigger of document.querySelectorAll('[data-nav-close]')) trigger.addEventListener('click', () => shell?.classList.remove('nav-open'));
for (const link of document.querySelectorAll('.sidebar nav a')) link.addEventListener('click', () => shell?.classList.remove('nav-open'));
