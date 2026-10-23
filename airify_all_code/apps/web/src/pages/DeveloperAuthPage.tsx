import { useState, type FormEvent } from 'react';
import { ArrowLeft, LogIn, Moon, ShieldCheck, Sun, Terminal, UserPlus } from 'lucide-react';
import { navigate, navigateTo, resolveReturn } from '../App';
import type { Theme } from '../App';
import { setMockSession } from '../shared/auth/mockSession';

interface Props {
  mode: 'login' | 'register';
  theme: Theme;
  onToggleTheme: () => void;
  query: URLSearchParams;
}

const emailLooksValid = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

/** Developer Portal auth — professional platform two-panel form (dark aside). */
export function DeveloperAuthPage({ mode, theme, onToggleTheme, query }: Props) {
  const isRegister = mode === 'register';
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [consent, setConsent] = useState(false);
  const [remember, setRemember] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const switchHref = () => {
    const ru = query.get('returnUrl');
    const q = ru ? `?returnUrl=${encodeURIComponent(ru)}` : '';
    return `/developers/${isRegister ? 'login' : 'register'}${q}`;
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!emailLooksValid(email)) { setErr('กรุณากรอกอีเมลให้ถูกต้อง'); return; }
    if (!password.trim()) { setErr('กรุณากรอกรหัสผ่าน'); return; }
    if (isRegister) {
      if (!displayName.trim()) { setErr('กรุณากรอกชื่อที่แสดง'); return; }
      if (password !== confirm) { setErr('รหัสผ่านและการยืนยันไม่ตรงกัน'); return; }
      if (!consent) { setErr('กรุณายอมรับว่านี่เป็นโหมดสาธิตก่อนสมัคร'); return; }
    }
    setMockSession({ displayName: isRegister ? displayName : undefined, email, role: 'developer_user' });
    navigate(resolveReturn(query, '/developers/dashboard'));
  };

  return (
    <div className="auth-page">
      <header className="auth-topbar">
        <button className="auth-back" onClick={() => navigateTo('developers')} aria-label="กลับ">
          <ArrowLeft size={16} aria-hidden="true" /> กลับ
        </button>
        <span className="auth-demo-badge">โหมดสาธิต</span>
        <button className="h-icon-btn" onClick={onToggleTheme} aria-label="สลับธีมสว่าง/มืด">
          {theme === 'dark' ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
        </button>
      </header>

      <div className="auth-grid">
        <aside className="auth-aside auth-aside-dev">
          <div className="auth-brand"><Terminal size={20} aria-hidden="true" /> Airify Platform · Developer Portal</div>
          <h1 className="auth-aside-title">{isRegister ? 'สร้างบัญชีนักพัฒนา' : 'เข้าสู่ Developer Portal'}</h1>
          <p className="auth-aside-sub">จัดการ Projects, API Keys, Rate Limit และ Usage Dashboard</p>
          <ul className="auth-benefits">
            <li><ShieldCheck size={16} aria-hidden="true" /> สร้าง Projects และออก API Keys</li>
            <li><ShieldCheck size={16} aria-hidden="true" /> ดู Usage และ Rate Limit</li>
            <li><ShieldCheck size={16} aria-hidden="true" /> เข้าถึง API Catalog และ Data Contract</li>
          </ul>
        </aside>

        <main className="auth-card">
          <div className="auth-kicker">Airify Platform · Developer Portal</div>
          <h2 className="auth-title">{isRegister ? 'สมัครบัญชีนักพัฒนา' : 'เข้าสู่ระบบ Developer Portal'}</h2>
          <p className="auth-subtitle">{isRegister ? 'สร้างบัญชีเพื่อจัดการ API และ Usage' : 'จัดการโปรเจกต์ API Key และดู Usage ของคุณ'}</p>

          <form onSubmit={submit} noValidate>
            {isRegister && (
              <>
                <label className="auth-label" htmlFor="dv-name">ชื่อที่แสดง</label>
                <input id="dv-name" className="input-field" type="text" autoComplete="name" placeholder="เช่น Dev Team"
                  value={displayName} onChange={e => { setDisplayName(e.target.value); setErr(null); }} />
              </>
            )}
            <label className="auth-label" htmlFor="dv-email">อีเมล</label>
            <input id="dv-email" className="input-field" type="email" autoComplete="email" placeholder="dev@example.com"
              value={email} onChange={e => { setEmail(e.target.value); setErr(null); }} />

            <label className="auth-label" htmlFor="dv-password">รหัสผ่าน</label>
            <input id="dv-password" className="input-field" type="password" autoComplete={isRegister ? 'new-password' : 'current-password'} placeholder="••••••••"
              value={password} onChange={e => { setPassword(e.target.value); setErr(null); }} />

            {isRegister ? (
              <>
                <label className="auth-label" htmlFor="dv-confirm">ยืนยันรหัสผ่าน</label>
                <input id="dv-confirm" className="input-field" type="password" autoComplete="new-password" placeholder="••••••••"
                  value={confirm} onChange={e => { setConfirm(e.target.value); setErr(null); }} />
                <label className="auth-check">
                  <input type="checkbox" checked={consent} onChange={e => { setConsent(e.target.checked); setErr(null); }} />
                  <span>ฉันเข้าใจว่านี่เป็นโหมดสาธิต และยินยอมให้ใช้ข้อมูลจำลองเพื่อทดลองผลิตภัณฑ์</span>
                </label>
              </>
            ) : (
              <label className="auth-check">
                <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
                <span>จดจำฉันไว้</span>
              </label>
            )}

            {err && <p className="auth-error">{err}</p>}

            <button type="submit" className="btn btn-primary auth-submit" style={{ width: '100%', justifyContent: 'center', textAlign: 'center' }}>
              {isRegister ? <UserPlus size={16} aria-hidden="true" /> : <LogIn size={16} aria-hidden="true" />}
              {isRegister ? 'สมัครบัญชีนักพัฒนา' : 'เข้าสู่ระบบ'}
            </button>
          </form>

          <p className="auth-alt">
            {isRegister ? 'มีบัญชีอยู่แล้ว?' : 'ยังไม่มีบัญชี?'}{' '}
            <button className="auth-link" onClick={() => navigate(switchHref())}>{isRegister ? 'เข้าสู่ระบบ' : 'สมัครบัญชีนักพัฒนา'}</button>
          </p>
          <p className="auth-note">โหมดสาธิต: ยังไม่มีการตรวจสอบบัญชีจริงและไม่มีการเก็บรหัสผ่าน</p>
        </main>
      </div>
    </div>
  );
}
