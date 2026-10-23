import {
  Activity, BookOpen, FileCode, House, KeyRound, LogOut, Moon, Plus,
  RefreshCw, Rocket, Sun, Trash2, TriangleAlert,
} from 'lucide-react';
import { navigate, navigateTo } from '../../../App';
import type { Lang, Theme } from '../../../App';
import { clearMockSession, useMockSession } from '../../../shared/auth/mockSession';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { ForbiddenPage } from '../../../pages/ForbiddenPage';

interface Props {
  theme: Theme;
  onToggleTheme: () => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  onToggleLang: () => void;
}

/** All values here are mock/demo — no real keys, usage, or persistence. */
const KEYS = [
  { id: 'k1', masked: 'airify_dev_8x2k••••••••', status: 'active' as const, last: '2 ชม.ที่แล้ว' },
  { id: 'k2', masked: 'airify_dev_k29f••••••••', status: 'active' as const, last: 'เมื่อวาน' },
  { id: 'k3', masked: 'airify_dev_p04a••••••••', status: 'active' as const, last: 'ยังไม่เคยใช้' },
];
const ENDPOINTS = [
  { path: '/v1/prediction/estimate', pct: 61 },
  { path: '/v1/exposure/estimate', pct: 27 },
  { path: '/v1/timeline/demo', pct: 9 },
  { path: '/v1/model/card', pct: 3 },
];
const PROJECTS = [
  { name: 'Airify Health Demo App', env: 'sandbox', keys: 2 },
  { name: 'City Dashboard Prototype', env: 'sandbox', keys: 1 },
];

export function DeveloperDashboardPage({ theme, onToggleTheme, lang, onToggleLang }: Props) {
  const session = useMockSession();

  // Not logged in → login gate. Wrong role (health_user) → 403.
  if (!session) {
    return (
      <div className="status-page">
        <div className="status-card">
          <div className="status-icon" aria-hidden="true"><KeyRound size={30} /></div>
          <h1 className="status-title">ต้องเข้าสู่ระบบก่อน</h1>
          <p className="status-text">Developer Dashboard สำหรับบัญชีนักพัฒนา — เข้าสู่ระบบหรือสมัครบัญชีเพื่อจัดการ API Key และ Usage</p>
          <div className="status-actions">
            <button className="btn btn-primary" onClick={() => navigate('/developers/login')}>เข้าสู่ระบบ</button>
            <button className="btn btn-secondary" onClick={() => navigate('/developers/register')}>สมัครบัญชีนักพัฒนา</button>
          </div>
        </div>
      </div>
    );
  }
  if (session.role !== 'developer_user') return <ForbiddenPage />;

  const logout = () => { clearMockSession(); navigateTo('developers'); };

  return (
    <div className="dash-page">
      {/* Dashboard top bar — distinct from the public portal navbar */}
      <header className="dash-nav">
        <div className="dash-nav-inner">
          <button className="dev-nav-brand" onClick={() => navigateTo('developers')} aria-label="Airify Platform home">
            Airify<span>· Dashboard</span>
          </button>
          <div className="dash-nav-actions">
            <span className="dash-account" title={session.email}>{session.displayName}</span>
            <button className="dev-toggle" onClick={onToggleLang} aria-label="Toggle language">{lang === 'th' ? 'EN' : 'TH'}</button>
            <button className="dev-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
              {theme === 'dark' ? <Sun size={15} aria-hidden="true" /> : <Moon size={15} aria-hidden="true" />}
            </button>
            <button className="dev-nav-primary dash-logout" onClick={logout}><LogOut size={15} aria-hidden="true" /> ออกจากระบบ</button>
          </div>
        </div>
      </header>

      <main className="dash-main">
        <div className="dash-head">
          <div>
            <h1 className="dash-title">สวัสดี, {session.displayName}</h1>
            <p className="dash-sub">ภาพรวมบัญชีนักพัฒนาและการใช้งาน API</p>
          </div>
          <StatusBadge status="demo" label="Demo Mode" />
        </div>

        {/* Overview cards */}
        <section className="dash-overview">
          <div className="dash-stat"><span className="dash-stat-num">2</span><span className="dash-stat-label">Projects</span></div>
          <div className="dash-stat"><span className="dash-stat-num">3</span><span className="dash-stat-label">Active API Keys</span></div>
          <div className="dash-stat"><span className="dash-stat-num">Developer</span><span className="dash-stat-label">Plan / Tier</span></div>
          <div className="dash-stat"><span className="dash-stat-num">Demo</span><span className="dash-stat-label">Mode</span></div>
        </section>

        <div className="dash-cols">
          {/* API Keys */}
          <section className="card dash-card">
            <div className="dash-card-head">
              <h2 className="dash-card-title"><KeyRound size={16} aria-hidden="true" /> API Keys</h2>
              <StatusBadge status="mock" label="mock" />
            </div>
            <div className="dash-keys">
              {KEYS.map(k => (
                <div key={k.id} className="dash-key">
                  <code className="dash-key-code">{k.masked}</code>
                  <span className="dash-key-meta"><StatusBadge status="live" label="active" /> · ใช้ล่าสุด {k.last}</span>
                  <div className="dash-key-actions">
                    <button className="dash-mini-btn" disabled aria-disabled="true" title="โหมดสาธิต"><RefreshCw size={14} aria-hidden="true" /> Rotate</button>
                    <button className="dash-mini-btn dash-mini-danger" disabled aria-disabled="true" title="โหมดสาธิต"><Trash2 size={14} aria-hidden="true" /> Revoke</button>
                  </div>
                </div>
              ))}
            </div>
            <button className="btn btn-secondary" disabled aria-disabled="true" style={{ marginTop: 12 }}><Plus size={15} aria-hidden="true" /> Create key (โหมดสาธิต)</button>
            <div className="dash-warn"><TriangleAlert size={14} aria-hidden="true" /> อย่า commit API key ลงในโค้ด/Git — เก็บใน environment variables เท่านั้น (คีย์ด้านบนเป็นค่า mock)</div>
          </section>

          {/* Usage & Rate limit */}
          <section className="card dash-card">
            <div className="dash-card-head">
              <h2 className="dash-card-title"><Activity size={16} aria-hidden="true" /> Usage &amp; Rate Limit</h2>
              <StatusBadge status="demo" label="demo" />
            </div>
            <div className="dash-usage-top">
              <div>
                <div className="dash-usage-num">847 <span>/ 10,000</span></div>
                <div className="dash-sub">requests วันนี้ · เหลือ 9,153</div>
              </div>
              <div className="dash-usage-right">
                <div className="dash-sub">Rate: 42 / 60 ต่อนาที</div>
                <div className="dash-sub">Reset: 14:00 UTC</div>
              </div>
            </div>
            <div className="dash-bar"><div className="dash-bar-fill" style={{ width: '8.5%' }} /></div>
            <div className="dash-sub" style={{ margin: '12px 0 6px', fontWeight: 700 }}>สัดส่วนการเรียกต่อ endpoint</div>
            {ENDPOINTS.map(e => (
              <div key={e.path} className="dash-endpoint">
                <code>{e.path}</code>
                <div className="dash-endpoint-bar"><div style={{ width: `${e.pct}%` }} /></div>
                <span className="dash-sub">{e.pct}%</span>
              </div>
            ))}
            <div className="dash-sub" style={{ marginTop: 10 }}>Error rate (4xx/5xx): <strong>0.4%</strong> · โหมดสาธิต</div>
          </section>
        </div>

        <div className="dash-cols">
          {/* Projects */}
          <section className="card dash-card">
            <div className="dash-card-head">
              <h2 className="dash-card-title"><Rocket size={16} aria-hidden="true" /> Projects</h2>
              <StatusBadge status="mock" label="mock" />
            </div>
            {PROJECTS.map(p => (
              <div key={p.name} className="dash-project">
                <div>
                  <div className="dash-project-name">{p.name}</div>
                  <div className="dash-sub">{p.env} · {p.keys} keys</div>
                </div>
                <StatusBadge status="demo" label={p.env} />
              </div>
            ))}
            <button className="btn btn-secondary" disabled aria-disabled="true" style={{ marginTop: 10 }}><Plus size={15} aria-hidden="true" /> New project (โหมดสาธิต)</button>
          </section>

          {/* Documentation shortcuts */}
          <section className="card dash-card">
            <div className="dash-card-head">
              <h2 className="dash-card-title"><BookOpen size={16} aria-hidden="true" /> เอกสารและทางลัด</h2>
            </div>
            <div className="dash-links">
              <button className="dash-link-btn" onClick={() => navigateTo('developers')}><FileCode size={15} aria-hidden="true" /> API Catalog</button>
              <button className="dash-link-btn" onClick={() => navigateTo('developers')}><Rocket size={15} aria-hidden="true" /> Quick Start</button>
              <button className="dash-link-btn" onClick={() => navigateTo('developers')}><FileCode size={15} aria-hidden="true" /> Data Contract</button>
              <button className="dash-link-btn" onClick={() => navigateTo('developers')}><FileCode size={15} aria-hidden="true" /> Model Card</button>
            </div>
            <button className="dash-link-btn" style={{ marginTop: 10 }} onClick={() => navigateTo('developers')}><House size={15} aria-hidden="true" /> กลับหน้า Developer Portal</button>
          </section>
        </div>

        <p className="dash-foot">ข้อมูลทั้งหมดในหน้านี้เป็น <strong>โหมดสาธิต/mock</strong> — ไม่มีการออก API key จริง ไม่มี usage จริง และไม่มีการเก็บข้อมูลจริง</p>
      </main>
    </div>
  );
}
