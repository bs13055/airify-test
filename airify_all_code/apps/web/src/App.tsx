import { useCallback, useEffect, useState } from 'react';
import { HealthPage } from './domains/health/pages/HealthPage';
import { DevelopersPage } from './domains/developers/pages/DevelopersPage';
import { DeveloperDashboardPage } from './domains/developers/pages/DeveloperDashboardPage';
import { HealthAuthPage } from './pages/HealthAuthPage';
import { DeveloperAuthPage } from './pages/DeveloperAuthPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { setMockSession } from './shared/auth/mockSession';

// QA/demo: synchronously select a mock session from `?mock=developer|health`
// BEFORE the first render, so direct LOCAL links always open with the requested
// role (and the Health login gate does not race the redirect).
(function seedMockFromQuery() {
  try {
    const m = new URLSearchParams(window.location.search).get('mock');
    if (m === 'developer' || m === 'health') {
      setMockSession(m === 'developer'
        ? { email: 'dev@airify.demo', displayName: 'Dev Demo', role: 'developer_user' }
        : { email: 'user@airify.demo', displayName: 'คุณสาธิต', role: 'health_user' });
    }
  } catch { /* ignore */ }
})();

/** Product surfaces + separate Health / Developer auth routes. */
export type Route =
  | 'developers' | 'health'
  | 'health-login' | 'health-register'
  | 'dev-login' | 'dev-register'
  | 'dashboard' | 'notfound';

export interface Nav { route: Route; query: URLSearchParams; }

/** Parse the hash into a route + its query string. Empty/legacy shell hashes
 * collapse to the Developer Portal; unknown paths → 404. Health and Developer
 * auth now live at dedicated paths (`#/health/login`, `#/developers/login`, …). */
export function parseHash(): Nav {
  const raw = window.location.hash.replace(/^#/, '');
  const qIdx = raw.indexOf('?');
  const path = (qIdx >= 0 ? raw.slice(0, qIdx) : raw).replace(/^\/+|\/+$/g, '').toLowerCase();
  const query = new URLSearchParams(qIdx >= 0 ? raw.slice(qIdx + 1) : '');
  let route: Route;
  if (path === 'health/login') route = 'health-login';
  else if (path === 'health/register') route = 'health-register';
  else if (path === 'developers/login') route = 'dev-login';
  else if (path === 'developers/register') route = 'dev-register';
  else if (path === 'developers/dashboard' || path === 'dashboard') route = 'dashboard';
  else if (path === 'health') route = 'health';
  else if (path === 'login') route = query.get('type') === 'developer' ? 'dev-login' : 'health-login';
  else if (path === 'register') route = query.get('type') === 'developer' ? 'dev-register' : 'health-register';
  else if (path === '' || path === 'developers' || path === 'demo' || path === 'analytics' || path === 'about') route = 'developers';
  else route = 'notfound';
  return { route, query };
}

/** Navigate to a hash target (accepts `/x`, `#/x`, or `x`). */
export function navigate(hash: string): void {
  let h = hash.startsWith('#') ? hash.slice(1) : hash;
  if (!h.startsWith('/')) h = `/${h}`;
  window.location.hash = h;
}

/** Navigate to one of the two main product surfaces (kept for existing callers). */
export function navigateTo(route: 'developers' | 'health'): void {
  navigate(`/${route}`);
}

/** Resolve a validated internal returnUrl to a hash target, else the fallback. */
export function resolveReturn(query: URLSearchParams, fallback: string): string {
  const ru = query.get('returnUrl');
  if (ru && !ru.includes('://') && !ru.startsWith('//')) {
    let h = ru;
    if (h.startsWith('/#')) h = h.slice(1);
    if (h.startsWith('#')) h = h.slice(1);
    if (h.startsWith('/')) return h;
  }
  return fallback;
}

/* ------------------------------------------------------------------ *
 * Shared preferences: theme (light/dark) + language (th/en). No deps.
 * ------------------------------------------------------------------ */
export type Theme = 'light' | 'dark';
export type Lang = 'th' | 'en';

const THEME_KEY = 'airify-theme';
const LANG_KEY = 'airify-lang';

function readTheme(): Theme {
  try {
    const q = new URLSearchParams(window.location.search).get('theme');
    if (q === 'light' || q === 'dark') return q;
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch { /* ignore */ }
  return 'light';
}

function readLang(): Lang {
  try {
    const q = new URLSearchParams(window.location.search).get('lang');
    if (q === 'th' || q === 'en') return q;
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === 'th' || saved === 'en') return saved;
  } catch { /* ignore */ }
  return 'th';
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch { /* ignore */ }
  }, [theme]);
  const toggle = useCallback(() => setTheme(t => (t === 'dark' ? 'light' : 'dark')), []);
  return [theme, toggle];
}

export function useLang(): [Lang, (l: Lang) => void, () => void] {
  const [lang, setLangState] = useState<Lang>(readLang);
  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try { localStorage.setItem(LANG_KEY, l); } catch { /* ignore */ }
  }, []);
  const toggle = useCallback(() => setLangState(l => {
    const next: Lang = l === 'th' ? 'en' : 'th';
    try { localStorage.setItem(LANG_KEY, next); } catch { /* ignore */ }
    return next;
  }), []);
  return [lang, setLang, toggle];
}

export default function App() {
  const [nav, setNav] = useState<Nav>(parseHash);
  const [theme, toggleTheme] = useTheme();
  const [lang, setLang, toggleLang] = useLang();

  useEffect(() => {
    const sync = () => { setNav(parseHash()); window.scrollTo({ top: 0 }); };
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, []);

  // Rewrite empty/legacy shell hashes to the canonical Developer Portal, and
  // rewrite the old ?type= login/register links to the new dedicated paths.
  useEffect(() => {
    const raw = window.location.hash.replace(/^#/, '');
    const qIdx = raw.indexOf('?');
    const path = (qIdx >= 0 ? raw.slice(0, qIdx) : raw).replace(/^\/+|\/+$/g, '').toLowerCase();
    const query = new URLSearchParams(qIdx >= 0 ? raw.slice(qIdx + 1) : '');
    if (path === 'login' || path === 'register') {
      const isDev = query.get('type') === 'developer';
      const base = isDev ? `/developers/${path === 'login' ? 'login' : 'register'}` : `/health/${path === 'login' ? 'login' : 'register'}`;
      const ru = query.get('returnUrl');
      window.history.replaceState(null, '', `#${base}${ru ? `?returnUrl=${encodeURIComponent(ru)}` : ''}`);
      return;
    }
    const isLegacyEmpty = path === '' || path === 'demo' || path === 'analytics' || path === 'about';
    if (isLegacyEmpty && window.location.hash !== '#/developers') {
      window.history.replaceState(null, '', '#/developers');
    }
  }, [nav.route]);

  const themeProps = { theme, onToggleTheme: toggleTheme };
  const langProps = { lang, setLang, onToggleLang: toggleLang };

  switch (nav.route) {
    case 'health':
      return <HealthPage {...themeProps} initialTab={nav.query.get('tab')} />;
    case 'health-login':
      return <HealthAuthPage mode="login" {...themeProps} query={nav.query} />;
    case 'health-register':
      return <HealthAuthPage mode="register" {...themeProps} query={nav.query} />;
    case 'dev-login':
      return <DeveloperAuthPage mode="login" {...themeProps} query={nav.query} />;
    case 'dev-register':
      return <DeveloperAuthPage mode="register" {...themeProps} query={nav.query} />;
    case 'dashboard':
      return <DeveloperDashboardPage {...themeProps} {...langProps} />;
    case 'notfound':
      return <NotFoundPage {...themeProps} />;
    default:
      return <DevelopersPage {...themeProps} {...langProps} />;
  }
}
