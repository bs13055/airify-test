import { Compass, House, Moon, Smartphone, Sun } from 'lucide-react';
import { navigateTo } from '../App';
import type { Theme } from '../App';

interface Props {
  theme: Theme;
  onToggleTheme: () => void;
}

/** 404 — unknown hash route. */
export function NotFoundPage({ theme, onToggleTheme }: Props) {
  return (
    <div className="status-page">
      <button className="h-icon-btn status-theme" onClick={onToggleTheme} aria-label="สลับธีมสว่าง/มืด">
        {theme === 'dark' ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
      </button>
      <div className="status-card">
        <div className="status-icon" aria-hidden="true"><Compass size={30} /></div>
        <div className="status-code">404</div>
        <h1 className="status-title">ไม่พบหน้าที่คุณกำลังหา</h1>
        <p className="status-text">ลิงก์อาจไม่ถูกต้องหรือหน้านี้ยังไม่มีในเวอร์ชันสาธิต</p>
        <div className="status-actions">
          <button className="btn btn-primary" onClick={() => navigateTo('developers')}>
            <House size={16} aria-hidden="true" /> ไปที่ Developer Portal
          </button>
          <button className="btn btn-secondary" onClick={() => navigateTo('health')}>
            <Smartphone size={16} aria-hidden="true" /> เปิด Health App
          </button>
        </div>
      </div>
    </div>
  );
}
