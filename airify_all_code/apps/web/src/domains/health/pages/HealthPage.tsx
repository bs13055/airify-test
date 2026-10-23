import { useEffect, useState } from 'react';
import {
  Activity, ArrowRight, ArrowUpRight, Bell, Bookmark, BookmarkPlus, Briefcase, ChartColumn,
  Check, ChevronRight, CircleUser, Clock, Crosshair, Database, Download, Dumbbell, Gauge,
  History, House, Info, Layers, LogOut, Map as MapIcon, MapPin, Maximize2, Moon, Navigation,
  Palette, Plus, Settings, Share2, ShieldCheck, Sun, Trash2, Trees, TrendingDown, TrendingUp,
  TriangleAlert, Wind, X,
} from 'lucide-react';
import { navigate } from '../../../App';
import type { Theme } from '../../../App';
import { RISK_CLASS, riskFromExposureLevel, riskFromPm25, scoreFromPm25 } from '../../../shared/utils/risk';
import type { RiskLevel } from '../../../shared/utils/risk';
import { SafetyNote } from '../../../shared/components/SafetyNote';
import { clearMockSession, useMockSession } from '../../../shared/auth/mockSession';
import {
  PLACE_CATALOG, addFrequentPlace, placeAdvice, placeById, removeFrequentPlace, resetHealthData,
  setConsent, setShareData, useHealthPrefs,
} from '../../../shared/health/healthStore';
import type { FreqPlace } from '../../../shared/health/healthStore';
import { DECISION_ACTIVITIES, RESTING_IR } from '../data/activities';
import type { Exposure, Prediction, Timeline } from '../types';
import { buildApiUrl } from '../../../shared/api/apiBase';

interface Props { theme: Theme; onToggleTheme: () => void; initialTab?: string | null; }

type TabId = 'today' | 'places' | 'timeline' | 'profile';
const TABS: { id: TabId; label: string; icon: typeof Sun }[] = [
  { id: 'today', label: 'วันนี้', icon: Sun },
  { id: 'places', label: 'พื้นที่', icon: MapPin },
  { id: 'timeline', label: 'ประวัติ', icon: ChartColumn },
  { id: 'profile', label: 'บัญชี', icon: CircleUser },
];
function resolveTab(raw: string | null | undefined): TabId {
  return raw && TABS.some(t => t.id === raw) ? (raw as TabId) : 'today';
}
function hashQuery(): URLSearchParams {
  try { return new URLSearchParams(window.location.hash.split('?')[1] || ''); } catch { return new URLSearchParams(); }
}

interface Place { id: string; name: string; lat: number; lon: number }
const PLACES: Place[] = [
  { id: 'nonthaburi', name: 'นนทบุรี', lat: 13.861, lon: 100.514 },
  { id: 'bangkok', name: 'กรุงเทพฯ (สีลม)', lat: 13.724, lon: 100.534 },
  { id: 'chiangmai', name: 'เชียงใหม่', lat: 18.788, lon: 98.985 },
  { id: 'khonkaen', name: 'ขอนแก่น', lat: 16.439, lon: 102.828 },
];

const RISK_TH: Record<RiskLevel, string> = { low: 'ปลอดภัย', moderate: 'ปานกลาง', high: 'เริ่มมีผล', very_high: 'มีผลต่อสุขภาพ', severe: 'อันตราย' };
const ACTION_TH: Record<RiskLevel, string> = {
  low: 'อากาศดี ออกไปทำกิจกรรมกลางแจ้งได้ตามปกติ',
  moderate: 'พอไปได้ ถ้าอยู่กลางแจ้งนาน ๆ ควรพักเป็นระยะ',
  high: 'เริ่มมีผลต่อสุขภาพ ถ้าต้องออกนอกบ้าน ควรลดกิจกรรมกลางแจ้งนาน ๆ และใส่หน้ากาก',
  very_high: 'ควรเลี่ยงกิจกรรมกลางแจ้งที่ใช้แรงมาก และใส่หน้ากาก N95 เมื่อออกนอกบ้าน',
  severe: 'ควรอยู่ในอาคารที่อากาศสะอาด ปิดหน้าต่าง และงดกิจกรรมกลางแจ้ง',
};
const CONFIDENCE_TH: Record<string, { label: string; tone: RiskLevel }> = {
  high: { label: 'สูง', tone: 'low' }, medium: { label: 'ปานกลาง', tone: 'moderate' }, low: { label: 'ต่ำ', tone: 'high' },
};
const PLACE_ICONS: Record<string, typeof House> = { House, Briefcase, Trees, Dumbbell };
const MARKER_POS: Record<string, { left: string; top: string }> = {
  me: { left: '32%', top: '58%' }, home: { left: '22%', top: '38%' }, work: { left: '70%', top: '32%' },
  park: { left: '58%', top: '72%' }, gym: { left: '46%', top: '52%' }, safer: { left: '68%', top: '66%' },
};

function decisionBand(pm25: number, sensitivity: number): { th: string; tone: RiskLevel; reason: string } {
  const eff = pm25 * sensitivity;
  if (eff < 22) return { th: 'ทำได้', tone: 'low', reason: 'อากาศโดยรวมยังโอเคสำหรับกิจกรรมนี้' };
  if (eff < 40) return { th: 'ควรระวัง', tone: 'moderate', reason: 'ทำได้ แต่ควรลดเวลาและพิจารณาใส่หน้ากาก' };
  return { th: 'ควรระวัง', tone: 'very_high', reason: 'ค่าฝุ่นสูง แนะนำเลื่อนหรือใส่หน้ากาก N95 หากจำเป็นต้องทำ' };
}
const twoDigit = (h: number) => `${String(((h % 24) + 24) % 24).padStart(2, '0')}:00`;
const fetchJson = async <T,>(path: string): Promise<T> => {
  const response = await fetch(buildApiUrl(path));
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
};
const fetchPrediction = (p: Place, forecast: string) =>
  fetchJson<Prediction>(`/v1/prediction/estimate?lat=${p.lat}&lon=${p.lon}&forecast_type=${forecast}`);

export function HealthPage({ theme, onToggleTheme, initialTab }: Props) {
  const session = useMockSession();
  const prefs = useHealthPrefs();
  const mapDeepLink = hashQuery().get('map') === '1';
  const [tab, setTab] = useState<TabId>(() => (mapDeepLink ? 'places' : resolveTab(initialTab)));
  const [place, setPlace] = useState<Place>(PLACES[0]);
  const [duration, setDuration] = useState('30');
  const [nowcast, setNowcast] = useState<Prediction | null>(null);
  const [forecast1h, setForecast1h] = useState<Prediction | null>(null);
  const [forecast2h, setForecast2h] = useState<Prediction | null>(null);
  const [exposure, setExposure] = useState<Exposure | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapOpen, setMapOpen] = useState(mapDeepLink);
  const [mapSel, setMapSel] = useState<string>('me');
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [showAddPlace, setShowAddPlace] = useState(false);
  const [show30Day, setShow30Day] = useState(() => hashQuery().get('open') === 'timeline30');
  const [shareModal, setShareModal] = useState(() => hashQuery().get('open') === 'share');
  const [deleteModal, setDeleteModal] = useState(false);
  const [showIntakeInfo, setShowIntakeInfo] = useState(false);
  const [placeDetailOpen, setPlaceDetailOpen] = useState(false);
  const [addPlaceName, setAddPlaceName] = useState('');
  const [pdpaModal, setPdpaModal] = useState(false);
  const [customPlaces, setCustomPlaces] = useState<{ id: string; name: string; lat: number; lon: number; factor: number }[]>([]);
  const [addPlaceErr, setAddPlaceErr] = useState<string | null>(null);

  const fetchAll = async (p = place) => {
    setLoading(true); setError(null);
    try {
      const [nc, f1, f2, exp, tl] = await Promise.all([
        fetchPrediction(p, 'nowcast'),
        fetchPrediction(p, '1h_forecast'),
        fetchPrediction(p, '2h_forecast'),
        fetchJson<Exposure>(`/v1/exposure/estimate?lat=${p.lat}&lon=${p.lon}&activity=walking&duration_minutes=${duration}`),
        fetchJson<Timeline>(`/v1/timeline/demo?lat=${p.lat}&lon=${p.lon}&days=7`),
      ]);
      setNowcast(nc); setForecast1h(f1); setForecast2h(f2); setExposure(exp); setTimeline(tl);
    } catch { setError('ระบบข้อมูลยังไม่พร้อมใช้งานชั่วคราว กรุณาลองใหม่อีกครั้ง'); }
    setLoading(false);
  };

  // Login gate: Health App is account-first.
  useEffect(() => { if (session === null) navigate('/health/login'); }, [session]);
  useEffect(() => { if (session?.role === 'health_user') fetchAll(); }, [session]); // eslint-disable-line react-hooks/exhaustive-deps

  const switchTab = (id: TabId) => { setTab(id); window.scrollTo({ top: 0 }); };
  const flashSaved = (msg: string) => { setSavedMsg(msg); window.setTimeout(() => setSavedMsg(null), 2600); };

  /* ---- gates (after all hooks) ---- */
  if (!session) {
    return <div className="ha-gate"><Wind size={30} aria-hidden="true" /><p>กำลังไปหน้าเข้าสู่ระบบ…</p></div>;
  }
  if (session.role !== 'health_user') {
    return (
      <div className="ha-gate">
        <div className="ha-gate-card">
          <div className="status-icon status-icon-warn" aria-hidden="true"><TriangleAlert size={28} /></div>
          <h1 className="status-title">บัญชีนี้เป็นบัญชีนักพัฒนา</h1>
          <p className="status-text">กรุณาใช้บัญชี Health App เพื่อเข้าใช้งานแอปนี้ หรือไปที่ Developer Dashboard</p>
          <div className="status-actions">
            <button className="btn btn-primary" onClick={() => navigate('/developers/dashboard')}><Gauge size={16} aria-hidden="true" /> ไป Developer Dashboard</button>
            <button className="btn btn-secondary" onClick={() => { clearMockSession(); navigate('/health/login'); }}><LogOut size={16} aria-hidden="true" /> ออกจากระบบ</button>
          </div>
        </div>
      </div>
    );
  }

  /* ---- derivations ---- */
  const today = new Date().toLocaleDateString('th-TH', { weekday: 'long', day: 'numeric', month: 'long' });
  const pm25 = nowcast?.pm25_estimate ?? null;
  const heroRisk = pm25 !== null ? riskFromPm25(pm25) : 'low';
  const score = pm25 !== null ? scoreFromPm25(pm25) : 0;
  const exposureRisk = exposure ? riskFromExposureLevel(exposure.exposure_level) : null;
  const ir = exposure?.assumptions?.inhalation_rate_m3_hr;
  const conf = nowcast ? (CONFIDENCE_TH[nowcast.confidence] ?? { label: nowcast.confidence, tone: 'moderate' as RiskLevel }) : null;
  const intakePct = exposure?.daily_intake_percent ?? null;
  const outdoorHours = ir ? Math.max(1, Math.round((ir / RESTING_IR))) : 5;

  const hourNow = new Date().getHours();
  const timeOpts = (nowcast && forecast1h && forecast2h) ? [
    { i: 0, label: 'ตอนนี้', t: twoDigit(hourNow), pm: nowcast.pm25_estimate },
    { i: 1, label: 'อีก 1 ชม.', t: twoDigit(hourNow + 1), pm: forecast1h.pm25_estimate },
    { i: 2, label: 'อีก 2 ชม.', t: twoDigit(hourNow + 2), pm: forecast2h.pm25_estimate },
  ] : [];
  const best = timeOpts.length ? timeOpts.reduce((a, b) => (b.pm < a.pm ? b : a)) : null;
  const worst = timeOpts.length ? timeOpts.reduce((a, b) => (b.pm > a.pm ? b : a)) : null;

  const placePm = (factor: number) => (pm25 !== null ? Math.max(3, Math.round(pm25 * factor)) : null);
  const freqPlaces: FreqPlace[] = prefs.frequentPlaceIds.map(placeById).filter((p): p is FreqPlace => !!p);
  const addablePlaces = PLACE_CATALOG.filter(p => !prefs.frequentPlaceIds.includes(p.id));
  const saferPm = pm25 !== null ? Math.max(3, Math.round(pm25 * 0.65)) : null;

  interface Marker { id: string; name: string; pm: number | null; risk: RiskLevel; kind: 'me' | 'freq' | 'safer' | 'custom'; place?: FreqPlace }
  const markers: Marker[] = [
    { id: 'me', name: place.name, pm: pm25, risk: heroRisk, kind: 'me' },
    ...freqPlaces.map<Marker>(p => { const pm = placePm(p.factor); return { id: p.id, name: p.name, pm, risk: pm !== null ? riskFromPm25(pm) : 'low', kind: 'freq', place: p }; }),
    ...customPlaces.map<Marker>(cp => { const pm = placePm(cp.factor); return { id: cp.id, name: cp.name, pm, risk: pm !== null ? riskFromPm25(pm) : 'low', kind: 'custom' }; }),
    { id: 'safer', name: 'บริเวณอากาศดีกว่า', pm: saferPm, risk: saferPm !== null ? riskFromPm25(saferPm) : 'low', kind: 'safer' },
  ];
  const selMarker = markers.find(m => m.id === mapSel) ?? markers[0];

  const saveFrequent = (id: string) => {
    addFrequentPlace(id);
    const p = placeById(id);
    flashSaved(`บันทึก “${p?.name ?? 'พื้นที่'}” เป็นพื้นที่ที่ไปบ่อยแล้ว (สาธิต)`);
  };

  /* ================= Tab: วันนี้ ================= */
  const TodayTab = (
    <>
      <div className="h-loc-summary">
        <div>
          <div className="h-loc-title"><MapPin size={15} aria-hidden="true" style={{ verticalAlign: '-2px' }} /> {place.name}</div>
          <div className="h-sub">{today} · พื้นที่ตัวอย่าง</div>
        </div>
        <span className="h-demo-chip">{nowcast?.data_status === 'demo_fallback' ? 'Demo fallback' : 'Core Engine · Local'}</span>
      </div>

      {/* Combined air quality + exposure summary card */}
      <div className={`h-hero ${RISK_CLASS[heroRisk]}`}>
        <div className="h-hero-top"><span>คุณภาพอากาศ ณ ตำแหน่งของคุณ</span><span className="h-hero-badge">{loading && !nowcast ? '…' : RISK_TH[heroRisk]}</span></div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 8 }}>
          <span className="h-hero-score">{loading && !nowcast ? '–' : (pm25 ?? '–')}</span><span className="h-hero-label">µg/m³ PM2.5</span>
        </div>
        <div className="h-hero-bar"><div className="h-hero-bar-fill" style={{ width: `${score}%` }} /></div>
        <div className="h-hero-action">{pm25 !== null ? ACTION_TH[heroRisk] : 'กำลังประเมินค่าฝุ่นรอบตัวคุณ…'}</div>
        {nowcast && <div className="h-hero-intake-note">แหล่งผลลัพธ์: {nowcast.method ?? 'prediction service'} · {nowcast.data_status}</div>}

        {/* Inline exposure intake */}
        {intakePct !== null && (
          <div className="h-hero-intake">
            <div className="h-hero-intake-row">
              <span className="h-hero-intake-label">ปริมาณการสูดรับมลพิษสะสม</span>
              <button className="h-info-btn" onClick={(e) => { e.stopPropagation(); setShowIntakeInfo(true); }} aria-label="ดูรายละเอียด"><Info size={14} aria-hidden="true" /></button>
            </div>
            <div className="h-hero-intake-val">ประมาณ {intakePct}% <span>ของเกณฑ์อ้างอิงส่วนบุคคลของคุณ</span></div>
            <div className="h-hero-intake-bar"><div className="h-hero-intake-fill" style={{ width: `${Math.min(100, intakePct)}%` }} /></div>
            {nowcast && <div className="h-hero-intake-note">ค่าประเมินมีความคลาดเคลื่อนประมาณ ± {nowcast.uncertainty} µg/m³</div>}
          </div>
        )}
      </div>

      {pm25 !== null && (
        <div className="h-card">
          <div className="h-card-title"><Activity size={14} aria-hidden="true" className="h-title-icon" /> สิ่งที่ทำได้วันนี้</div>
          <div className="h-decision-list">
            {DECISION_ACTIVITIES.map(a => { const d = decisionBand(pm25, a.sensitivity); return (
              <div key={a.id} className={`h-decision-card ${RISK_CLASS[d.tone]}`}>
                <div className="h-decision-icon" aria-hidden="true">{a.icon}</div>
                <div className="h-decision-main"><div className="h-decision-label">{a.label}</div><div className="h-decision-reason">{d.reason}</div></div>
                <span className="h-decision-status">{d.th}</span>
              </div>
            ); })}
          </div>
        </div>
      )}

      <div className="h-card">
        <div className="h-card-title"><Clock size={14} aria-hidden="true" className="h-title-icon" /> ช่วงเวลาที่ดีกว่า</div>
        {best && worst ? (
          <>
            <div className="h-time-cols">
              <div className={`h-time-col ${RISK_CLASS[riskFromPm25(best.pm)]}`}><div className="h-sub">แนะนำช่วง</div><div className="h-time-clock">{best.t}</div><div className="h-sub">{best.label} · {best.pm} µg/m³</div></div>
              <div className={`h-time-col ${RISK_CLASS[riskFromPm25(worst.pm)]}`}><div className="h-sub">ควรเลี่ยง</div><div className="h-time-clock">{worst.t}</div><div className="h-sub">{worst.label} · {worst.pm} µg/m³</div></div>
            </div>
            <div className="h-sub" style={{ marginTop: 10 }}>{best.i > 0 && best.pm < timeOpts[0].pm ? `ถ้ารอได้ แนะนำช่วง ${best.t} เพราะค่าฝุ่นมีแนวโน้มลดลง` : 'ตอนนี้เป็นช่วงที่ค่าฝุ่นค่อนข้างดีของวันนี้แล้ว'}</div>
          </>
        ) : <div className="h-sub">{loading ? 'กำลังดูแนวโน้ม…' : 'ยังไม่มีข้อมูล'}</div>}
      </div>

      <button className="h-cta-wide" onClick={() => switchTab('places')}><Navigation size={18} aria-hidden="true" /><span>วันนี้จะไปที่ไหน? เปิดแผนที่พื้นที่</span><ArrowRight size={16} aria-hidden="true" /></button>
      <div className="h-safety-th">ข้อมูลนี้เป็นการประเมินเพื่อช่วยตัดสินใจ ไม่ใช่คำแนะนำหรือการวินิจฉัยทางการแพทย์</div>
    </>
  );

  /* ================= Tab: พื้นที่ (Map-first 70/30) ================= */
  const PlacesTab = (
    <>
      {/* ~70%: primary combined map */}
      <button className="h-mapview" onClick={() => { setMapSel('me'); setMapOpen(true); }} aria-label="เปิดแผนที่เต็มจอ">
        <div className="h-mapview-top">
          <div><div className="h-mapview-place">{place.name}</div><div className="h-sub">พื้นที่ของคุณ · โหมดสาธิต</div></div>
          {pm25 !== null && <span className={`risk-badge ${RISK_CLASS[heroRisk]}`}>{pm25} µg/m³ · {RISK_TH[heroRisk]}</span>}
        </div>
        <div className={`h-mapview-surface ${RISK_CLASS[heroRisk]}`}>
          <div className="h-map-grid" aria-hidden="true" /><div className="h-map-road h-map-road-1" aria-hidden="true" /><div className="h-map-road h-map-road-2" aria-hidden="true" /><div className="ha-map-heat" aria-hidden="true" />
          <span className="ha-map-marker" style={{ ...MARKER_POS.me }}><span className={`ha-map-dot ${RISK_CLASS[heroRisk]}`}><MapPin size={18} aria-hidden="true" /></span><span className="ha-map-tag">คุณ</span></span>
          <span className="h-mapview-expand"><Maximize2 size={16} aria-hidden="true" /> แตะเพื่อเปิดเต็มจอ</span>
        </div>
      </button>

      {savedMsg && <div className="h-saved-toast"><Check size={15} aria-hidden="true" /> {savedMsg}</div>}

      {/* ~30%: compact recommendation + frequent places */}
      <div className="h-maprec">
        <div className="h-maprec-action"><ShieldCheck size={16} aria-hidden="true" className={`risk-value ${RISK_CLASS[heroRisk]}`} /> {pm25 !== null ? ACTION_TH[heroRisk] : 'กำลังประเมิน…'}</div>
        <div className="h-maprec-title">พื้นที่ที่ไปบ่อย</div>
        <div className="h-freq-row">
          {freqPlaces.map(p => {
            const pm = placePm(p.factor); const r = pm !== null ? riskFromPm25(pm) : 'low'; const Icon = PLACE_ICONS[p.icon] ?? House;
            return (
              <button key={p.id} className={`h-freq-chip ${RISK_CLASS[r]}`} onClick={() => { setMapSel(p.id); setMapOpen(true); }}>
                <Icon size={16} aria-hidden="true" /><span className="h-freq-name">{p.name}</span><span className="h-freq-pm risk-value">{pm ?? '–'}</span>
              </button>
            );
          })}
          {customPlaces.map(cp => {
            const pm = placePm(cp.factor); const r = pm !== null ? riskFromPm25(pm) : 'low';
            return (
              <button key={cp.id} className={`h-freq-chip ${RISK_CLASS[r]}`} onClick={() => { setMapSel(cp.id); setMapOpen(true); }}>
                <MapPin size={16} aria-hidden="true" /><span className="h-freq-name">{cp.name}</span><span className="h-freq-pm risk-value">{pm ?? '–'}</span>
              </button>
            );
          })}
          {addablePlaces.length > 0 && <button className="h-freq-chip h-freq-add" onClick={() => setShowAddPlace(v => !v)}><Plus size={16} aria-hidden="true" /> เพิ่มสถานที่</button>}
        </div>
        {showAddPlace && (
          <div className="h-add-list">
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: 6 }}>เพิ่มสถานที่ที่ไปบ่อย</div>
              <input className="input-field" type="text" placeholder="ตั้งชื่อสถานที่ เช่น บ้าน, ที่ทำงาน, มหาวิทยาลัย" value={addPlaceName} onChange={e => { setAddPlaceName(e.target.value); setAddPlaceErr(null); }} style={{ marginBottom: 6 }} />
              {addPlaceErr && <div style={{ fontSize: '0.75rem', color: 'var(--color-danger)', marginBottom: 6 }}>{addPlaceErr}</div>}
              <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                const trimmed = addPlaceName.trim();
                if (!trimmed) { setAddPlaceErr('กรุณาตั้งชื่อสถานที่ก่อนเพิ่ม'); return; }
                const newId = `custom_${Date.now()}`;
                const factor = 0.8 + Math.random() * 0.4;
                setCustomPlaces(prev => [...prev, { id: newId, name: trimmed, lat: place.lat, lon: place.lon, factor }]);
                setAddPlaceName('');
                setShowAddPlace(false);
                flashSaved(`บันทึก "${trimmed}" เป็นพื้นที่ที่ไปบ่อยแล้ว (สาธิต)`);
              }}><BookmarkPlus size={15} aria-hidden="true" /> เพิ่ม "{addPlaceName.trim() || '...'}"</button>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 4 }}>ตำแหน่งนี้เป็นข้อมูลตัวอย่างสำหรับเดโม — ยังไม่ใช้ GPS จริง</div>
            </div>
            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 8, marginTop: 4 }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginBottom: 6 }}>หรือเลือกจากรายการ:</div>
              {addablePlaces.map(p => { const Icon = PLACE_ICONS[p.icon] ?? House; return (
                <button key={p.id} className="h-cta-btn" onClick={() => { saveFrequent(p.id); setShowAddPlace(false); }}><Icon size={15} aria-hidden="true" /> เพิ่ม {p.name}</button>
              ); })}
            </div>
          </div>
        )}
      </div>
      <div className="h-safety-th">แผนที่สาธิต — ยังไม่ใช่ข้อมูลตำแหน่งจริง ไม่ใช่คำแนะนำทางการแพทย์</div>
    </>
  );

  /* ================= Tab: Timeline ================= */
  const selectedDayData = timeline?.timeline.find(d => d.date === selectedDay) ?? null;
  const days = timeline?.timeline ?? [];
  const maxScale = Math.max(60, ...days.map(d => d.pm25_avg));
  let trend: { dir: 'up' | 'down' | 'flat'; text: string } | null = null;
  let advice = '';
  if (days.length >= 4) {
    const half = Math.floor(days.length / 2);
    const early = days.slice(0, half).reduce((s, d) => s + d.pm25_avg, 0) / half;
    const late = days.slice(half).reduce((s, d) => s + d.pm25_avg, 0) / (days.length - half);
    const avg = days.reduce((s, d) => s + d.pm25_avg, 0) / days.length;
    trend = late > early + 2 ? { dir: 'up', text: 'ช่วงหลังค่าฝุ่นสูงขึ้น — ควรลดกิจกรรมกลางแจ้งและใส่หน้ากากเมื่อจำเป็น' }
      : late < early - 2 ? { dir: 'down', text: 'ช่วงหลังค่าฝุ่นลดลง — แนวโน้มดีขึ้น ออกกิจกรรมกลางแจ้งได้มากขึ้น' }
        : { dir: 'flat', text: 'ช่วง 7 วันที่ผ่านมา ค่าฝุ่นอยู่ในระดับใกล้เคียงกัน' };
    advice = avg >= 30
      ? 'การได้รับ PM2.5 ต่อเนื่องอาจเพิ่มความเสี่ยงต่อสุขภาพ — ลดกิจกรรมกลางแจ้งช่วงค่าฝุ่นสูง เลือกเส้นทางที่อากาศดีกว่า ปรึกษาผู้เชี่ยวชาญด้านสุขภาพหากมีอาการผิดปกติ'
      : 'สัปดาห์นี้การรับฝุ่นอยู่ในระดับที่จัดการได้ — รักษาแนวทางนี้ต่อไป เลือกช่วงเวลาที่อากาศดีสำหรับกิจกรรมกลางแจ้ง';
  }
  const highestDay = days.length ? days.reduce((a, b) => (b.pm25_avg > a.pm25_avg ? b : a)) : null;
  const avg7 = days.length ? Math.round(days.reduce((s, d) => s + d.pm25_avg, 0) / days.length) : null;

  const Chart = (compact = false) => (
    <div className="h-chart-wrap">
      <div className="h-chart-yaxis">{compact ? 'PM2.5' : 'ปริมาณการรับฝุ่น (ค่าเฉลี่ย PM2.5 µg/m³)'}</div>
      <div className="h-chart">
        <div className="h-chart-bands" aria-hidden="true">
          <div className="risk-severe" style={{ height: `${((maxScale - 50) / maxScale) * 100}%` }} />
          <div className="risk-very-high" style={{ height: `${(10 / maxScale) * 100}%` }} />
          <div className="risk-high" style={{ height: `${(10 / maxScale) * 100}%` }} />
          <div className="risk-moderate" style={{ height: `${(15 / maxScale) * 100}%` }} />
          <div className="risk-low" style={{ height: `${(15 / maxScale) * 100}%` }} />
        </div>
        <div className="h-chart-bars">
          {days.map(d => { const r = riskFromPm25(d.pm25_avg); const isSel = d.date === selectedDay; return (
            <button key={d.date} className="h-chart-barcol" onClick={() => setSelectedDay(isSel ? null : d.date)} aria-pressed={isSel} title={`${d.date}: ${d.pm25_avg} µg/m³`}>
              <span className="h-chart-val">{d.pm25_avg}</span>
              <span className={`h-chart-bar ${RISK_CLASS[r]}${isSel ? ' selected' : ''}`} style={{ height: `${Math.max(4, (d.pm25_avg / maxScale) * 100)}%` }} />
              <span className="h-chart-x">{new Date(d.date + 'T00:00:00').toLocaleDateString('th-TH', { weekday: 'short' })}</span>
            </button>
          ); })}
        </div>
      </div>
      <div className="h-chart-xaxis">วันที่ (7 วันล่าสุด)</div>
      <div className="h-chart-legend">
        {(['low', 'moderate', 'high', 'very_high', 'severe'] as RiskLevel[]).map(r => (
          <span key={r} className="h-legend-item"><span className={`h-legend-dot ${RISK_CLASS[r]}`} /> {RISK_TH[r]}</span>
        ))}
      </div>
    </div>
  );

  const TimelineTab = (
    <>
      <div className="h-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><div className="h-card-title" style={{ marginBottom: 0 }}><History size={14} aria-hidden="true" className="h-title-icon" /> ประวัติ 7 วัน</div><span className="h-demo-chip" style={{ marginLeft: 'auto' }}>ข้อมูลสาธิต</span></div>
        {timeline ? (
          <div style={{ marginTop: 12 }}>
            {Chart(false)}
            {selectedDayData ? (
              <div className="h-row" style={{ marginTop: 6, borderBottom: 'none' }}><span className="h-row-label">{new Date(selectedDayData.date + 'T00:00:00').toLocaleDateString('th-TH', { weekday: 'long', day: 'numeric', month: 'short' })}</span><span className="h-row-value">{selectedDayData.pm25_avg} µg/m³ · หายใจเข้า ≈ {selectedDayData.daily_exposure_estimate_ug} µg</span></div>
            ) : <div className="h-sub" style={{ marginTop: 6 }}>แตะแท่งเพื่อดูรายละเอียดของแต่ละวัน · สีของแท่งบอกระดับความเสี่ยง</div>}
            <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}><span className="h-pill">ค่าเฉลี่ย 7 วัน: {timeline.summary.avg_pm25} µg/m³</span></div>
            <div className="h-sub" style={{ marginTop: 8, fontSize: '0.78rem' }}>เส้นอ้างอิง: WHO 15 µg/m³ | มาตรฐานไทย 50 µg/m³</div>
          </div>
        ) : <div className="h-sub" style={{ marginTop: 10 }}>{loading ? 'กำลังโหลด…' : 'ยังไม่มีข้อมูล'}</div>}
      </div>

      {trend && (
        <div className="h-card">
          <div className="h-card-title">แนวโน้มสัปดาห์นี้</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {trend.dir === 'up' && <TrendingUp size={22} aria-hidden="true" style={{ color: 'var(--risk-high)' }} />}
            {trend.dir === 'down' && <TrendingDown size={22} aria-hidden="true" style={{ color: 'var(--risk-low)' }} />}
            {trend.dir === 'flat' && <ArrowRight size={22} aria-hidden="true" style={{ color: 'var(--color-text-muted)' }} />}
            <span style={{ fontSize: '0.9rem', fontWeight: 700 }}>{trend.text}</span>
          </div>
          <div className="h-budget-note" style={{ marginTop: 10 }}>{advice}</div>
        </div>
      )}

      <div className="h-card">
        <div className="h-card-title"><ChartColumn size={14} aria-hidden="true" className="h-title-icon" /> แดชบอร์ดการรับฝุ่นส่วนตัว</div>
        <div className="h-sub">สรุปการรับฝุ่นย้อนหลังพร้อมคำแนะนำเฉพาะคุณ</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
          <button className="h-pill" style={{ background: 'var(--color-primary)', color: '#fff' }}>7 วัน</button>
          <button className="h-pill" onClick={() => setShow30Day(true)}>30 วัน</button>
          <button className="h-pill h-cta-disabled" disabled>กำหนดเอง</button>
          <button className="h-pill h-cta-disabled" disabled>1 ปี (เร็ว ๆ นี้)</button>
        </div>
        <div className="h-sub" style={{ marginTop: 8 }}>ข้อมูลสาธิต — เวอร์ชันจริงจะสะสมจากการใช้งานของคุณ</div>
      </div>
      <div className="h-safety-th">ประวัติทั้งหมดเป็นข้อมูลสาธิตแบบกำหนดผลได้ ไม่ใช่การวัดจริง</div>
    </>
  );

  /* ================= Tab: บัญชี (Settings + Privacy) ================= */
  const ConsentRow = ({ k, label, hint }: { k: 'locationHistory' | 'exposureTimeline' | 'frequentSuggestions'; label: string; hint: string }) => (
    <div className="h-consent-row">
      <div><div className="h-consent-label">{label}</div><div className="h-sub">{hint}</div></div>
      <button className={`h-switch ${prefs.consent[k] ? 'on' : ''}`} role="switch" aria-checked={prefs.consent[k]} aria-label={label} onClick={() => setConsent(k, !prefs.consent[k])}><span className="h-switch-knob" /></button>
    </div>
  );

  const ProfileTab = (
    <>
      <div className="h-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="h-avatar" aria-hidden="true"><CircleUser size={30} /></div>
          <div style={{ minWidth: 0 }}><div style={{ fontWeight: 800, fontSize: '1rem' }}>สวัสดี, {session.displayName}</div><div className="h-sub" style={{ wordBreak: 'break-all' }}>{session.email}</div></div>
          <span className="h-demo-chip" style={{ marginLeft: 'auto' }}>เซสชันสาธิต</span>
        </div>
        <button className="h-cta-btn" style={{ marginTop: 12, width: '100%' }} onClick={() => { clearMockSession(); navigate('/health/login'); }}><LogOut size={16} aria-hidden="true" /> ออกจากระบบ</button>
      </div>

      <div className="h-card">
        <div className="h-card-title"><Settings size={14} aria-hidden="true" className="h-title-icon" /> การตั้งค่า</div>
        <div className="h-row"><span className="h-row-label"><Palette size={14} aria-hidden="true" style={{ verticalAlign: '-2px', marginRight: 6 }} /> ธีม</span>
          <button className="h-cta-btn" style={{ width: 'auto' }} onClick={onToggleTheme} aria-label="สลับธีม">{theme === 'dark' ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}{theme === 'dark' ? 'โหมดสว่าง' : 'โหมดมืด'}</button>
        </div>
        <div className="h-row"><span className="h-row-label">ภาษา</span><span className="h-row-value">ไทย (เริ่มต้น)</span></div>
        <div className="h-row" style={{ borderBottom: 'none' }}><span className="h-row-label">เวอร์ชัน</span><span className="h-row-value">Demo V1 · mock</span></div>
      </div>

      <div className="h-card">
        <div className="h-card-title"><ShieldCheck size={14} aria-hidden="true" className="h-title-icon" /> ความยินยอมการใช้ข้อมูล</div>
        <ConsentRow k="locationHistory" label="อนุญาตการเข้าถึงตำแหน่ง" hint="ใช้ตำแหน่งเพื่อประเมินค่าฝุ่นในพื้นที่ของคุณ" />
        <ConsentRow k="exposureTimeline" label="อนุญาตการเก็บประวัติการเดินทาง" hint="ใช้สร้าง Timeline การรับฝุ่นส่วนตัวของคุณ" />
        <ConsentRow k="frequentSuggestions" label="การใช้ข้อมูลเพื่อการแนะนำ" hint="ใช้ข้อมูลของคุณเพื่อปรับคำแนะนำให้เหมาะกับพฤติกรรมและพื้นที่" />
      </div>

      <div className="h-card">
        <div className="h-card-title"><Share2 size={14} aria-hidden="true" className="h-title-icon" /> แชร์ข้อมูลเพื่อพัฒนา Airify</div>
        <div className="h-consent-row" style={{ paddingTop: 0 }}>
          <div><div className="h-consent-label">การแชร์ข้อมูลแบบไม่ระบุตัวตน</div><div className="h-sub">ข้อมูลที่ไม่ระบุตัวตนอาจถูกใช้เพื่อพัฒนาระบบเตือนภัยฝุ่น การวิเคราะห์เชิงสาธารณะ และงานวิจัย/นวัตกรรมด้านสุขภาพและสิ่งแวดล้อมในอนาคต</div></div>
          <button className={`h-switch ${prefs.shareData ? 'on' : ''}`} role="switch" aria-checked={prefs.shareData} aria-label="แชร์ข้อมูลเพื่อพัฒนา" onClick={() => { if (!prefs.shareData) setShareModal(true); else setShareData(false); }}><span className="h-switch-knob" /></button>
        </div>
        {prefs.shareData && <div className="h-sub" style={{ marginTop: 4, color: 'var(--risk-low)' }}><Check size={13} aria-hidden="true" /> เปิดอยู่ — ปิดได้ทุกเมื่อ ไม่จำเป็นสำหรับการใช้งานพื้นฐาน</div>}
      </div>

      <div className="h-card">
        <div className="h-card-title"><Database size={14} aria-hidden="true" className="h-title-icon" /> ข้อมูลที่บันทึก</div>
        <div className="h-row"><span className="h-row-label">พื้นที่ที่บันทึก</span><span className="h-row-value">{freqPlaces.length} แห่ง (สาธิต)</span></div>
        <div className="h-row"><span className="h-row-label">ประวัติการรับฝุ่น</span><span className="h-row-value">7 วัน (สาธิต)</span></div>
        <div className="h-row"><span className="h-row-label">ประวัติการเดินทาง</span><span className="h-row-value">ไม่มี (ยังไม่เก็บ)</span></div>
        <div className="h-row"><span className="h-row-label">การตั้งค่าคำแนะนำ</span><span className="h-row-value">ค่าเริ่มต้น</span></div>
        <div className="h-row" style={{ borderBottom: 'none' }}><span className="h-row-label">ความยินยอมในการใช้ข้อมูล</span><span className="h-row-value">ตั้งค่าแล้ว</span></div>
        <div className="h-cta-grid" style={{ marginTop: 12 }}>
          <button className="h-cta-btn h-cta-disabled" disabled aria-disabled="true"><Download size={15} aria-hidden="true" /> ส่งออกข้อมูล (เร็ว ๆ นี้)</button>
          <button className="h-cta-btn h-danger" onClick={() => setDeleteModal(true)}><Trash2 size={15} aria-hidden="true" /> ลบข้อมูลของฉัน</button>
        </div>
        <button className="h-cta-btn" style={{ width: '100%', marginTop: 8 }} onClick={() => setPdpaModal(true)}><ShieldCheck size={15} aria-hidden="true" /> อ่านนโยบายข้อมูลส่วนบุคคล</button>
      </div>

      <SafetyNote className="health-safety">
        โหมดสาธิตนี้ไม่เก็บข้อมูลส่วนบุคคลจริง เซสชันและพื้นที่ที่บันทึกเป็น mock บนเครื่องคุณเท่านั้น เวอร์ชันจริงจะต้องมีนโยบายความเป็นส่วนตัวและบันทึกความยินยอมอย่างเป็นทางการ
      </SafetyNote>
    </>
  );

  const CONTENT: Record<TabId, JSX.Element> = { today: TodayTab, places: PlacesTab, timeline: TimelineTab, profile: ProfileTab };

  return (
    <div className="ha-shell">
      <header className="ha-appbar ha-appbar-min">
        <span className="ha-brand"><Wind size={18} aria-hidden="true" className="ha-brand-icon" /> Airify Health</span>
        <span className="h-demo-chip">โหมดสาธิต</span>
      </header>

      <main className="ha-content">
        {error && <div className="h-card" style={{ borderLeft: '4px solid var(--color-danger)' }}><div style={{ fontSize: '0.85rem', color: 'var(--color-danger)', fontWeight: 600 }}>{error}</div></div>}
        {CONTENT[tab]}
      </main>

      <nav className="ha-tabbar" aria-label="เมนูหลัก Airify Health">
        {TABS.map(t => { const Icon = t.icon; return (
          <button key={t.id} className={tab === t.id ? 'active' : ''} onClick={() => switchTab(t.id)} aria-current={tab === t.id ? 'page' : undefined} aria-label={t.label}><Icon size={21} aria-hidden="true" /><span>{t.label}</span></button>
        ); })}
      </nav>

      {/* Full-screen map (mock) with fade+scale animation */}
      {mapOpen && (
        <div className="ha-map-overlay" role="dialog" aria-modal="true" aria-label="แผนที่พื้นที่">
          <header className="ha-map-top">
            <button className="ha-map-back" onClick={() => setMapOpen(false)} aria-label="ปิดแผนที่"><X size={18} aria-hidden="true" /></button>
            <div className="ha-map-title"><MapIcon size={16} aria-hidden="true" /> แผนที่พื้นที่</div>
            <span className={`risk-badge ${RISK_CLASS[selMarker.risk]}`}>{selMarker.pm ?? '–'} · {RISK_TH[selMarker.risk]}</span>
          </header>
          <div className={`ha-map-surface ${RISK_CLASS[selMarker.risk]}`}>
            <div className="h-map-grid" aria-hidden="true" /><div className="h-map-road h-map-road-1" aria-hidden="true" /><div className="h-map-road h-map-road-2" aria-hidden="true" /><div className="h-map-road h-map-road-3" aria-hidden="true" /><div className="ha-map-heat" aria-hidden="true" />
            {markers.map(m => {
              const pos = MARKER_POS[m.id] ?? { left: '50%', top: '50%' };
              const Icon = m.kind === 'me' ? MapPin : m.kind === 'safer' ? ShieldCheck : (PLACE_ICONS[m.place?.icon ?? 'House'] ?? House);
              const tag = m.kind === 'me' ? 'คุณ' : m.kind === 'safer' ? 'ดีกว่า' : m.name;
              return (
                <button key={m.id} className={`ha-map-marker ${mapSel === m.id ? 'sel' : ''}`} style={{ ...pos }} onClick={() => setMapSel(m.id)} aria-label={m.name}>
                  <span className={`ha-map-dot ${RISK_CLASS[m.risk]}`}><Icon size={16} aria-hidden="true" /></span><span className="ha-map-tag">{tag}</span>
                </button>
              );
            })}
            <span className="ha-map-demo"><Layers size={12} aria-hidden="true" /> แผนที่สาธิต — ยังไม่ใช่ข้อมูลตำแหน่งจริง</span>
            <button className="ha-map-recenter" onClick={() => setMapSel('me')} aria-label="กลับไปตำแหน่งของคุณ"><Crosshair size={18} aria-hidden="true" /></button>
          </div>
          <div className="ha-map-sheet">
            <div className="ha-map-sheet-grip" aria-hidden="true" />
            <div className="ha-map-sheet-head">
              <div><div className="ha-map-place">{selMarker.name}</div><div className="h-sub">PM2.5 โดยประมาณ · โหมดสาธิต</div></div>
              <div className={`ha-map-pm risk-value ${RISK_CLASS[selMarker.risk]}`}>{selMarker.pm ?? '–'}<span> µg/m³</span></div>
            </div>
            <div className={`h-mapsheet-verdict ${RISK_CLASS[selMarker.risk]}`}>
              {placeAdvice(selMarker.risk).canGo ? <Check size={16} aria-hidden="true" /> : <TriangleAlert size={16} aria-hidden="true" />}
              <span><strong>{RISK_TH[selMarker.risk]} · {placeAdvice(selMarker.risk).verdict}</strong> — {placeAdvice(selMarker.risk).protection}</span>
            </div>
            <div className="h-cta-grid">
              <button className="h-cta-btn" onClick={() => { setMapSel(selMarker.id); setPlaceDetailOpen(true); }}><Navigation size={16} aria-hidden="true" /> ดูรายละเอียด</button>
              {selMarker.kind === 'freq' ? (
                <button className="h-cta-btn h-danger" onClick={() => { if (selMarker.place) { removeFrequentPlace(selMarker.place.id); flashSaved(`นำ “${selMarker.name}” ออกแล้ว`); setMapSel('me'); } }}><Trash2 size={16} aria-hidden="true" /> นำออกจากที่ไปบ่อย</button>
              ) : selMarker.kind === 'custom' ? (
                <button className="h-cta-btn h-danger" onClick={() => { setCustomPlaces(prev => prev.filter(cp => cp.id !== selMarker.id)); flashSaved(`นำ "${selMarker.name}" ออกแล้ว`); setMapSel('me'); }}><Trash2 size={16} aria-hidden="true" /> นำออก</button>
              ) : selMarker.kind === 'safer' ? (
                <button className="h-cta-btn h-cta-disabled" disabled aria-disabled="true"><Bookmark size={16} aria-hidden="true" /> พื้นที่แนะนำ</button>
              ) : (
                <button className="h-cta-btn h-cta-disabled" disabled aria-disabled="true"><MapPin size={16} aria-hidden="true" /> ตำแหน่งของคุณ</button>
              )}
            </div>
            {savedMsg && <div className="h-saved-toast" style={{ marginTop: 10 }}><Check size={15} aria-hidden="true" /> {savedMsg}</div>}
          </div>
        </div>
      )}

      {/* 30-day mock summary */}
      {show30Day && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="สรุป 30 วัน" onClick={() => setShow30Day(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head"><div className="h-card-title" style={{ marginBottom: 0 }}><ChartColumn size={15} aria-hidden="true" className="h-title-icon" /> สรุป 30 วัน</div><button className="ha-map-back" onClick={() => setShow30Day(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button></div>
            <span className="h-demo-chip">ข้อมูลสาธิต/mock</span>
            <div className="h-stat-grid" style={{ marginTop: 12 }}>
              <div className="h-stat"><div className="h-stat-num risk-value">{avg7 ?? '–'}</div><div className="h-sub">ค่าเฉลี่ยการรับฝุ่น (µg/m³)</div></div>
              <div className="h-stat"><div className="h-stat-num" style={{ color: 'var(--risk-high)' }}>{highestDay ? highestDay.pm25_avg : '–'}</div><div className="h-sub">วันที่รับฝุ่นสูงสุด{highestDay ? ` (${new Date(highestDay.date + 'T00:00:00').toLocaleDateString('th-TH', { day: 'numeric', month: 'short' })})` : ''}</div></div>
              <div className="h-stat"><div className="h-stat-num" style={{ fontSize: '1.1rem' }}>ที่ทำงาน</div><div className="h-sub">พื้นที่เสี่ยงที่ไปบ่อยสุด</div></div>
            </div>
            <div className="h-budget-note" style={{ marginTop: 12 }}>คำแนะนำ: ช่วงที่ค่าฝุ่นสูงมักตรงกับพื้นที่ “ที่ทำงาน” — ลองเลือกเส้นทาง/ช่วงเวลาที่อากาศดีกว่า และพกหน้ากากในวันค่าฝุ่นสูง</div>
            <div className="h-sub" style={{ marginTop: 8 }}>ข้อมูล 30 วันเป็น mock — เวอร์ชันจริงจะสะสมจากการใช้งานของคุณเอง</div>
          </div>
        </div>
      )}

      {/* Share-data consent modal */}
      {shareModal && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="แชร์ข้อมูลเพื่อพัฒนา" onClick={() => setShareModal(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head"><div className="h-card-title" style={{ marginBottom: 0 }}><Share2 size={15} aria-hidden="true" className="h-title-icon" /> แชร์ข้อมูลเพื่อพัฒนา Airify</div><button className="ha-map-back" onClick={() => setShareModal(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button></div>
            <ul className="h-modal-list">
              <li><Info size={14} aria-hidden="true" /> ทำไม Airify ขอข้อมูล: เพื่อพัฒนาความแม่นยำของการประเมินฝุ่นและคำแนะนำ</li>
              <li><Database size={14} aria-hidden="true" /> ข้อมูลที่แชร์: ค่าฝุ่นและการรับฝุ่นแบบรวม ไม่รวมชื่อ/อีเมล/ตำแหน่งที่ระบุตัวตน</li>
              <li><ShieldCheck size={14} aria-hidden="true" /> เป็นข้อมูลแบบไม่ระบุตัวตน/รวมกลุ่ม (anonymized/aggregated)</li>
              <li><Bell size={14} aria-hidden="true" /> ปิดได้ทุกเมื่อจากหน้านี้</li>
              <li><TriangleAlert size={14} aria-hidden="true" /> ไม่ใช้เพื่อการวินิจฉัยทางการแพทย์</li>
            </ul>
            <div className="h-sub">โหมดสาธิต: ยังไม่มีการส่งข้อมูลจริง เวอร์ชันจริงจะมีนโยบายความเป็นส่วนตัวและบันทึกความยินยอมอย่างเป็นทางการ</div>
            <div className="h-cta-grid" style={{ marginTop: 14 }}>
              <button className="h-cta-btn" onClick={() => setShareModal(false)}>ยกเลิก</button>
              <button className="btn btn-primary" onClick={() => { setShareData(true); setShareModal(false); flashSaved('ขอบคุณ! เปิดการแชร์ข้อมูลแบบไม่ระบุตัวตนแล้ว (สาธิต)'); }}><Check size={16} aria-hidden="true" /> ยินยอมและเปิด</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete data confirm modal */}
      {deleteModal && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="ลบข้อมูล" onClick={() => setDeleteModal(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head"><div className="h-card-title" style={{ marginBottom: 0 }}><Trash2 size={15} aria-hidden="true" className="h-title-icon" /> ลบข้อมูลของฉัน</div><button className="ha-map-back" onClick={() => setDeleteModal(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button></div>
            <div className="h-sub" style={{ lineHeight: 1.7 }}>การลบนี้จะล้างพื้นที่ที่บันทึกและการตั้งค่า Timeline ในโหมดสาธิตบนเครื่องนี้ (mock) — บัญชีเข้าสู่ระบบของคุณจะยังอยู่</div>
            <div className="h-cta-grid" style={{ marginTop: 14 }}>
              <button className="h-cta-btn" onClick={() => setDeleteModal(false)}>ยกเลิก</button>
              <button className="btn btn-primary h-btn-danger" onClick={() => { resetHealthData(); setDeleteModal(false); flashSaved('ลบข้อมูลสาธิตบนเครื่องนี้แล้ว'); }}><Trash2 size={16} aria-hidden="true" /> ยืนยันลบข้อมูล</button>
            </div>
          </div>
        </div>
      )}

      {/* Intake info modal */}
      {showIntakeInfo && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="รายละเอียดการรับฝุ่น" onClick={() => setShowIntakeInfo(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head">
              <div className="h-card-title" style={{ marginBottom: 0 }}><Info size={15} aria-hidden="true" className="h-title-icon" /> ปริมาณการสูดรับมลพิษสะสม</div>
              <button className="ha-map-back" onClick={() => setShowIntakeInfo(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button>
            </div>
            <div className="h-modal-list" style={{ listStyle: 'none', padding: 0 }}>
              <div className="h-guidance-item"><div className="h-guidance-icon"><Info size={14} aria-hidden="true" /></div><span>คำนวณจากค่าฝุ่นในพื้นที่ × ระยะเวลาสัมผัส × อัตราการหายใจตามโปรไฟล์ของคุณ</span></div>
              <div className="h-guidance-item"><div className="h-guidance-icon"><Gauge size={14} aria-hidden="true" /></div><span>อ้างอิงจาก WHO, EPA Exposure Factors และงานวิจัยด้านสุขภาพที่เกี่ยวข้อง</span></div>
              {nowcast && <div className="h-guidance-item"><div className="h-guidance-icon"><TriangleAlert size={14} aria-hidden="true" /></div><span>เป็นค่าประมาณ — มีความคลาดเคลื่อนประมาณ ± {nowcast.uncertainty} µg/m³ (ยิ่งไกลจากสถานีวัด ความคลาดเคลื่อนอาจสูงขึ้น)</span></div>}
              <div className="h-guidance-item"><div className="h-guidance-icon"><ShieldCheck size={14} aria-hidden="true" /></div><span>ไม่ใช่การวินิจฉัยโรค — ข้อมูลนี้เป็นค่าประมาณจากโมเดลสาธิต ไม่ใช่คำแนะนำทางการแพทย์</span></div>
            </div>
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={() => setShowIntakeInfo(false)}>เข้าใจแล้ว</button>
          </div>
        </div>
      )}

      {/* Place detail modal (stays on Places page) */}
      {placeDetailOpen && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="รายละเอียดพื้นที่" onClick={() => setPlaceDetailOpen(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head">
              <div className="h-card-title" style={{ marginBottom: 0 }}><MapPin size={15} aria-hidden="true" className="h-title-icon" /> {selMarker.name}</div>
              <button className="ha-map-back" onClick={() => setPlaceDetailOpen(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button>
            </div>
            <div className={`h-mapsheet-verdict ${RISK_CLASS[selMarker.risk]}`}>
              {placeAdvice(selMarker.risk).canGo ? <Check size={16} aria-hidden="true" /> : <TriangleAlert size={16} aria-hidden="true" />}
              <span><strong>{RISK_TH[selMarker.risk]}</strong> — {placeAdvice(selMarker.risk).verdict}</span>
            </div>
            <div style={{ marginTop: 12 }}>
              <div className="h-row"><span className="h-row-label">PM2.5 โดยประมาณ</span><span className={`h-row-value risk-value ${RISK_CLASS[selMarker.risk]}`}>{selMarker.pm ?? '–'} µg/m³</span></div>
              <div className="h-row"><span className="h-row-label">ระดับความเสี่ยง</span><span className="h-row-value">{RISK_TH[selMarker.risk]}</span></div>
              <div className="h-row"><span className="h-row-label">คำแนะนำ</span><span className="h-row-value">{ACTION_TH[selMarker.risk]}</span></div>
              {selMarker.kind !== 'safer' && saferPm !== null && <div className="h-row"><span className="h-row-label">บริเวณอากาศดีกว่า</span><span className="h-row-value risk-value" style={{ color: 'var(--risk-low)' }}>{saferPm} µg/m³</span></div>}
              <div className="h-row" style={{ borderBottom: 'none' }}><span className="h-row-label">สาเหตุที่ดีกว่า/แย่กว่า</span><span className="h-row-value">{selMarker.pm !== null && saferPm !== null && selMarker.pm > saferPm ? 'มีแหล่งกำเนิดฝุ่นใกล้กว่า (ถนนหลัก, ก่อสร้าง)' : 'ห่างจากแหล่งกำเนิดฝุ่นมากกว่า'}</span></div>
            </div>
            <div className="h-sub" style={{ marginTop: 10 }}>ค่าประเมินจากโมเดลสาธิต ไม่ใช่การวัดจริง — ไม่ใช่คำแนะนำทางการแพทย์</div>
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={() => setPlaceDetailOpen(false)}>ปิด</button>
          </div>
        </div>
      )}

      {/* PDPA policy modal */}
      {pdpaModal && (
        <div className="h-modal-overlay" role="dialog" aria-modal="true" aria-label="นโยบายข้อมูลส่วนบุคคล" onClick={() => setPdpaModal(false)}>
          <div className="h-modal" onClick={e => e.stopPropagation()}>
            <div className="h-modal-head">
              <div className="h-card-title" style={{ marginBottom: 0 }}><ShieldCheck size={15} aria-hidden="true" className="h-title-icon" /> นโยบายข้อมูลส่วนบุคคล</div>
              <button className="ha-map-back" onClick={() => setPdpaModal(false)} aria-label="ปิด"><X size={16} aria-hidden="true" /></button>
            </div>
            <div className="h-sub" style={{ lineHeight: 1.8, marginTop: 8 }}>
              เอกสารนโยบายข้อมูลส่วนบุคคลฉบับเต็มจะถูกจัดทำก่อนใช้งานจริง
              <br /><br />
              สิ่งที่เวอร์ชันสาธิตนี้ไม่ได้ทำ:
              <br />• ไม่เก็บข้อมูลส่วนบุคคลจริง
              <br />• ไม่ส่งข้อมูลไปยังเซิร์ฟเวอร์ภายนอก
              <br />• ไม่เก็บตำแหน่งที่ระบุตัวตนได้
              <br />• ไม่ใช้เพื่อการวินิจฉัยทางการแพทย์
              <br /><br />
              เวอร์ชันจริงจะต้องมี PDPA compliance review อย่างเป็นทางการก่อนเปิดให้บริการ
            </div>
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={() => setPdpaModal(false)}>เข้าใจแล้ว</button>
          </div>
        </div>
      )}
    </div>
  );
}
