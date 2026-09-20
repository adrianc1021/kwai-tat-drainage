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
