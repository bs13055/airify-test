import { House, LogOut, ShieldAlert, Smartphone } from 'lucide-react';
import { navigate, navigateTo } from '../App';
import { clearMockSession, useMockSession } from '../shared/auth/mockSession';

/** 403 — role mismatch. Shown when a signed-in user opens a route their role
 * does not permit (e.g. a health_user opening the Developer Dashboard). */
export function ForbiddenPage() {
  const session = useMockSession();
  return (
    <div className="status-page">
      <div className="status-card">
        <div className="status-icon status-icon-warn" aria-hidden="true"><ShieldAlert size={30} /></div>
        <div className="status-code">403</div>
        <h1 className="status-title">บัญชีนี้ไม่มีสิทธิ์เข้าหน้านี้</h1>
        <p className="status-text">
          หน้านี้สำหรับบัญชีนักพัฒนา (Developer){session ? ` — บัญชีของคุณเป็นบทบาท “${session.role === 'health_user' ? 'ผู้ใช้ Health' : 'นักพัฒนา'}”` : ''}.
          แต่ละบัญชีมีได้เพียงบทบาทเดียว (โหมดสาธิต)
        </p>
        <div className="status-actions">
          <button className="btn btn-primary" onClick={() => navigateTo('health')}>
            <Smartphone size={16} aria-hidden="true" /> ไปที่ Health App
          </button>
          <button className="btn btn-secondary" onClick={() => navigateTo('developers')}>
            <House size={16} aria-hidden="true" /> หน้าแรก Platform
          </button>
          {session && (
            <button className="btn btn-secondary" onClick={() => { clearMockSession(); navigate('/developers/login'); }}>
              <LogOut size={16} aria-hidden="true" /> ออกจากระบบ แล้วเข้าสู่ระบบใหม่
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
