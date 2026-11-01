(() => {
  'use strict';
  const tabs = Array.from(document.querySelectorAll('.af-plan-switch [role="tab"]'));
  const message = document.getElementById('plan-message');
  function selectPlans(tab, moveFocus = false) {
    for (const item of tabs) {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
    }
    if (message) { message.hidden = true; message.replaceChildren(); }
    if (moveFocus) tab.focus();
  }
  for (const [index, tab] of tabs.entries()) {
    tab.addEventListener('click', () => selectPlans(tab));
    tab.addEventListener('keydown', (event) => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      selectPlans(tabs[next], true);
    });
  }
  document.querySelectorAll('[data-select-plans]').forEach((link) => link.addEventListener('click', () => {
    const tab = document.getElementById(`${link.dataset.selectPlans}-tab`);
    if (tab) selectPlans(tab);
  }));
  const descriptions = {
    premium: 'Airify Premium เป็นแผนบริการในอนาคต ยังไม่เปิดรับสมัครหรือชำระเงิน คุณสามารถทดลองฟีเจอร์ปัจจุบันได้ฟรีที่ Try Airify Now',
    developer: 'Developer API อยู่ระหว่างเตรียมให้บริการ ยังไม่เปิดออก API Key หรือเรียกเก็บค่าบริการ ติดตามรายละเอียดการพัฒนาได้บน GitHub ของโครงการ',
    business: 'Business API เป็นแผนบริการสำหรับองค์กรในอนาคต ยังไม่เปิดรับคำสั่งซื้อหรือมีฝ่ายขาย ติดต่อทีมพัฒนาผ่าน GitHub ของโครงการได้'
  };
  document.querySelectorAll('[data-plan]').forEach((button) => button.addEventListener('click', () => {
    if (!message) return;
    const text = document.createElement('p'); text.textContent = descriptions[button.dataset.plan];
    const link = document.createElement('a'); const premium = button.dataset.plan === 'premium';
    link.href = premium ? 'try.html' : 'https://github.com/bs13055/Airify';
    link.textContent = premium ? 'เปิด Try Airify Now' : 'ดูโครงการบน GitHub';
    if (!premium) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
    message.replaceChildren(text, link); message.hidden = false;
    message.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' });
  }));
  const header = document.querySelector('.af-header');
  const navigationLinks = Array.from(document.querySelectorAll('.af-menu a[href^="#"]'));
  const navigationSections = navigationLinks.map((link) => document.getElementById(link.hash.slice(1))).filter(Boolean);
  function setActiveSection(id) {
    for (const link of navigationLinks) {
      if (link.hash === `#${id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  }
  function syncNavigation() {
    if (!navigationSections.length) return;
    const marker = (header?.getBoundingClientRect().bottom || 0) + 48;
    let active = navigationSections[0].id;
    for (const section of navigationSections) {
      if (section.getBoundingClientRect().top <= marker) active = section.id;
    }
    // The shorter footer may never reach the header before the page ends.
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) {
      active = navigationSections[navigationSections.length - 1].id;
    }
    setActiveSection(active);
  }
  let navigationFrame = 0;
  function queueNavigationSync() {
    if (navigationFrame) return;
    navigationFrame = requestAnimationFrame(() => {
      navigationFrame = 0;
      syncNavigation();
    });
  }
  window.addEventListener('scroll', queueNavigationSync, { passive: true });
  window.addEventListener('resize', queueNavigationSync);
  window.addEventListener('hashchange', queueNavigationSync);
  window.addEventListener('load', queueNavigationSync);
  queueNavigationSync();
  navigationLinks.forEach((link) => link.addEventListener('click', (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    setActiveSection(link.hash.slice(1));
    const nav = document.getElementById('airifyNav');
    if (!nav || !window.bootstrap) return;
    const collapse = window.bootstrap.Collapse.getOrCreateInstance(nav, { toggle: false });
    if (nav.classList.contains('show') || nav.classList.contains('collapsing')) {
      event.preventDefault();
      // Finish closing the phone/tablet menu before positioning the section.
      nav.addEventListener('hidden.bs.collapse', () => {
        const section = document.getElementById(link.hash.slice(1));
        if (!section) return;
        if (location.hash !== link.hash) history.pushState(null, '', link.hash);
        const top = section.getBoundingClientRect().top + window.scrollY - (header?.offsetHeight || 0) - 18;
        window.scrollTo({ top: Math.max(0, top), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
        setActiveSection(section.id);
      }, { once: true });
      if (nav.classList.contains('collapsing')) nav.addEventListener('shown.bs.collapse', () => collapse.hide(), { once: true });
      else collapse.hide();
    }
  }));
})();
