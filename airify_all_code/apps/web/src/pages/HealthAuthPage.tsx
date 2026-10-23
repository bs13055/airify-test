import { useState, type FormEvent } from 'react';
import { ArrowRight, Bookmark, ChartColumn, LogIn, ShieldCheck, UserPlus, Wind } from 'lucide-react';
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

/** Health App auth — friendly, mobile-first, app-styled (NOT the developer/platform form). */
export function HealthAuthPage({ mode, query }: Props) {
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
    return `/health/${isRegister ? 'login' : 'register'}${q}`;
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
    // Mock only — password validated non-empty then discarded (never stored).
    setMockSession({ displayName: isRegister ? displayName : undefined, email, role: 'health_user' });
    navigate(resolveReturn(query, '/health?tab=today'));
  };

  return (
    <div className="ha-auth">
      <div className="ha-auth-card">
        <div className="ha-auth-brand"><span className="ha-auth-logo"><Wind size={22} aria-hidden="true" /></span> Airify Health</div>
        <span className="h-demo-chip ha-auth-demo">โหมดสาธิต</span>

        <h1 className="ha-auth-title">{isRegister ? 'สมัครใช้งาน Airify Health' : 'ยินดีต้อนรับสู่ Airify Health'}</h1>
        <p className="ha-auth-sub">
          {isRegister
            ? 'สร้างบัญชีเพื่อบันทึกพื้นที่ที่ไปบ่อย ติดตามการรับฝุ่นของคุณ และดูคำแนะนำรายวัน'
            : 'เข้าสู่ระบบเพื่อดูค่าฝุ่นรอบตัว คำแนะนำกิจกรรม และประวัติการรับฝุ่นของคุณ'}
        </p>

        <ul className="ha-auth-benefits">
          <li><ShieldCheck size={15} aria-hidden="true" /> รู้ทันฝุ่นรอบตัวและควรทำอะไรในแต่ละวัน</li>
          <li><Bookmark size={15} aria-hidden="true" /> บันทึกพื้นที่ที่ไปบ่อย เช่น บ้าน / ที่ทำงาน</li>
          <li><ChartColumn size={15} aria-hidden="true" /> ติดตามการรับฝุ่นย้อนหลัง</li>
        </ul>

        <form onSubmit={submit} noValidate className="ha-auth-form">
          {isRegister && (
            <>
              <label className="auth-label" htmlFor="ha-name">ชื่อที่แสดง</label>
              <input id="ha-name" className="input-field" type="text" autoComplete="name" placeholder="เช่น สมชาย"
                value={displayName} onChange={e => { setDisplayName(e.target.value); setErr(null); }} />
            </>
          )}
          <label className="auth-label" htmlFor="ha-email">อีเมล</label>
          <input id="ha-email" className="input-field" type="email" autoComplete="email" placeholder="you@example.com"
            value={email} onChange={e => { setEmail(e.target.value); setErr(null); }} />

          <label className="auth-label" htmlFor="ha-password">รหัสผ่าน</label>
          <input id="ha-password" className="input-field" type="password" autoComplete={isRegister ? 'new-password' : 'current-password'} placeholder="••••••••"
            value={password} onChange={e => { setPassword(e.target.value); setErr(null); }} />

          {isRegister ? (
            <>
              <label className="auth-label" htmlFor="ha-confirm">ยืนยันรหัสผ่าน</label>
              <input id="ha-confirm" className="input-field" type="password" autoComplete="new-password" placeholder="••••••••"
                value={confirm} onChange={e => { setConfirm(e.target.value); setErr(null); }} />

              <div style={{ margin: '12px 0 6px', fontSize: '0.82rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>ข้อมูลสุขภาพ (ใช้ประเมินการสูดรับมลพิษให้ใกล้เคียงกับโปรไฟล์ของคุณ)</div>
              <label className="auth-label" htmlFor="ha-gender">เพศ</label>
              <select id="ha-gender" className="input-field" defaultValue="">
                <option value="" disabled>เลือกเพศ</option>
                <option value="male">ชาย</option>
                <option value="female">หญิง</option>
                <option value="other">อื่น ๆ</option>
                <option value="prefer_not">ไม่ระบุ</option>
              </select>
              <label className="auth-label" htmlFor="ha-birth-year">ปีเกิด (พ.ศ.)</label>
              <input id="ha-birth-year" className="input-field" type="number" placeholder="เช่น 2535" min="2450" max="2570" />
              <label className="auth-label" htmlFor="ha-weight">น้ำหนักตัว (กก.) — ไม่บังคับ</label>
              <input id="ha-weight" className="input-field" type="number" placeholder="เช่น 65" min="20" max="200" />
              <label className="auth-label" htmlFor="ha-activity">ระดับกิจกรรมทั่วไป — ไม่บังคับ</label>
              <select id="ha-activity" className="input-field" defaultValue="">
                <option value="">ไม่ระบุ</option>
                <option value="sedentary">นั่งทำงานเป็นหลัก</option>
                <option value="light">ออกกำลังกายเบา ๆ</option>
                <option value="moderate">ออกกำลังกายปานกลาง</option>
                <option value="active">ออกกำลังกายหนัก / ทำงานกลางแจ้ง</option>
              </select>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '4px 0 8px' }}>ใช้เพื่อประเมินการสูดรับมลพิษให้ใกล้เคียงกับโปรไฟล์ของคุณมากขึ้น</div>

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

          <button type="submit" className="btn btn-primary ha-auth-submit" style={{ width: '100%', justifyContent: 'center', textAlign: 'center' }}>
            {isRegister ? <UserPlus size={17} aria-hidden="true" /> : <LogIn size={17} aria-hidden="true" />}
            {isRegister ? 'สมัครใช้งาน' : 'เข้าสู่ระบบ'}
          </button>
        </form>

        <p className="auth-alt">
          {isRegister ? 'มีบัญชีอยู่แล้ว?' : 'ยังไม่มีบัญชี?'}{' '}
          <button className="auth-link" onClick={() => navigate(switchHref())}>{isRegister ? 'เข้าสู่ระบบ' : 'สมัครใช้งาน'}</button>
        </p>
        <p className="auth-note">โหมดสาธิต: ยังไม่มีการตรวจสอบบัญชีจริงและไม่มีการเก็บรหัสผ่าน</p>
        <button className="ha-auth-platform" onClick={() => navigateTo('developers')}>
          Airify Platform สำหรับนักพัฒนา <ArrowRight size={13} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
