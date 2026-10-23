import { useEffect, useState } from 'react';
import {
  ArrowRight, ArrowUpRight, Gauge, KeyRound, Languages, LogIn, LogOut, Moon, Smartphone, Sun, UserPlus,
} from 'lucide-react';
import { navigate, navigateTo } from '../../../App';
import type { Lang, Theme } from '../../../App';
import { clearMockSession, useMockSession, type MockSession } from '../../../shared/auth/mockSession';
import { StatusBadge, type Status } from '../../../shared/components/StatusBadge';
import { AppStoreCTA } from '../../../shared/components/AppStoreCTA';
import { buildApiUrl } from '../../../shared/api/apiBase';
import { PLATFORM_APIS, DATASETS, USE_CASES } from '../data/catalog';

const ACTIVITIES = ['walking', 'running', 'motorbike_commute', 'car_commute', 'indoor', 'outdoor_sitting'];
const USER_GROUPS = ['adult_general', 'children_0_18', 'sensitive_group'];
const MODEL_VERSION = 'airify-prediction-lite-plus-v0.1';

interface Props {
  theme: Theme;
  onToggleTheme: () => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  onToggleLang: () => void;
}

/** Bilingual portal copy (Thai-first). Technical terms stay in English by design. */
const COPY = {
  th: {
    navPlatform: 'แพลตฟอร์ม', navHealthApp: 'Health App', navBuild: 'สร้างอะไรได้', navApis: 'APIs', navStart: 'เริ่มต้น', navFlow: 'การทำงาน',
    openHealth: 'เปิด Health App', exploreApi: 'เริ่มทดลอง API',
    heroChip: 'Airify Platform · โหมดสาธิต', heroKicker: 'Developer Portal',
    heroSub: 'แพลตฟอร์มข้อมูล PM2.5 และการรับฝุ่นส่วนบุคคล สำหรับนักพัฒนา เมือง และผลิตภัณฑ์สุขภาพสิ่งแวดล้อม',
    heroBody: 'เปลี่ยนข้อมูลสิ่งแวดล้อมให้เป็น API และประสบการณ์ที่พร้อมช่วยตัดสินใจ — โหมดสาธิต ยังไม่ใช่การใช้งานจริง และไม่ใช่คำแนะนำทางการแพทย์',
    ctaTry: 'เริ่มทดลอง API', ctaHealth: 'ดู Health App Preview', ctaSample: 'ดูข้อมูลตัวอย่าง',
    respTitle: 'ตัวอย่าง Response', flowMini: 'ขั้นตอนการทำงาน',
    overviewEyebrow: 'ภาพรวม', overviewTitle: 'Airify คืออะไร',
    overviewBody: 'Airify คือโครงสร้างพื้นฐาน PM2.5 Exposure Intelligence ที่เปลี่ยนข้อมูลสิ่งแวดล้อมให้เป็น API และประสบการณ์ที่พร้อมช่วยตัดสินใจ และรองรับผลิตภัณฑ์อย่าง Airify Health',
    overviewPoints: ['ทำนายค่าฝุ่นรอบตัวแบบ nowcast + พยากรณ์', 'ประเมินการรับฝุ่นส่วนบุคคล (งบรับฝุ่น)', 'แปลงข้อมูลเป็นคำแนะนำเชิงตัดสินใจ'],
    previewEyebrow: 'ผลิตภัณฑ์จากแพลตฟอร์ม', previewTitle: 'Health App Preview',
    previewIntro: 'Airify Platform อยู่เบื้องหลังแอปสุขภาพสำหรับคนทั่วไป — ตัวอย่างจริงของสิ่งที่คุณสร้างได้จาก API ชุดเดียวกัน',
    previewBullets: [
      'งบรับฝุ่นวันนี้ — ใช้ไปแล้วกี่เปอร์เซ็นต์',
      'PM2.5 nowcast พร้อมระดับความมั่นใจ',
      'เช็กพื้นที่ที่จะไปก่อนออกจากบ้าน',
      'กิจกรรมที่ทำได้ / ควรเลื่อน',
      'ประวัติการรับฝุ่น 7 วัน',
    ],
    previewCtaApp: 'เปิด Health App', previewCtaApi: 'ดู API ที่อยู่เบื้องหลัง',
    buildEyebrow: 'ใช้ทำอะไรได้', buildTitle: 'สร้างอะไรได้บ้าง',
    apiEyebrow: 'ความสามารถ', apiTitle: 'API / Capability Catalog',
    apiIntro: 'แยกชัดเจนระหว่างสิ่งที่ใช้ได้ในโหมดสาธิต และสิ่งที่อยู่ระหว่างวางแผน',
    availDemo: 'ใช้ได้ในโหมดสาธิต', availPlanned: 'อยู่ระหว่างวางแผน', who: 'เหมาะกับ',
    datasetTitle: 'Dataset Catalog', datasetIntro: '7 ชุดข้อมูล — 3 สาธิต, 4 วางแผน',
    startEyebrow: 'เริ่มต้นใช้งาน', startTitle: 'Quick Start',
    steps: ['เลือก endpoint', 'ทดลอง request', 'อ่าน response', 'นำไปต่อยอดในแอปของคุณ'],
    send: 'ส่ง Request', apiHint: 'ยิง request จริงไปยัง demo API ผ่านโดเมนปัจจุบัน',
    flowEyebrow: 'การทำงาน', flowTitle: 'Health App ใช้แพลตฟอร์มอย่างไร',
    flow: ['ตำแหน่ง', 'ค่า PM2.5', 'งบรับฝุ่น', 'คำแนะนำกิจกรรม', 'การตัดสินใจ'],
    honestyEyebrow: 'ความโปร่งใส', honestyTitle: 'โหมดสาธิตและข้อจำกัด',
    honesty: ['ระบบนี้เป็นโหมดสาธิต/ข้อมูลจำลอง ยังไม่ใช่การใช้งานจริง', 'บาง API อยู่ระหว่างวางแผน ยังไม่พร้อมใช้', 'ไม่ใช่คำแนะนำหรือการวินิจฉัยทางการแพทย์', 'มีไว้เพื่อสาธิตและตรวจสอบแนวคิดผลิตภัณฑ์'],
    modelTitle: 'ความโปร่งใสของโมเดล', viewModel: 'ดู Model Card (JSON)', reloadModel: 'โหลด Model Card ใหม่',
    trained: 'ยังไม่เทรน — ใช้ตรรกะสาธิตแบบกำหนดผลได้', validated: 'ยังไม่ผ่านการตรวจสอบ',
    loginTitle: 'พร้อมเริ่มต้นใช้งาน?',
    loginSub: 'สร้างโปรเจกต์ · รับ API Key · ดู Usage — ระบบบัญชีนักพัฒนากำลังจะเปิดใช้งาน',
    loginBtn: 'เข้าสู่ระบบ', registerBtn: 'สมัครบัญชีนักพัฒนา', navLogin: 'เข้าสู่ระบบ', navDashboard: 'Dashboard', dashGo: 'ไปที่ Dashboard',
    loginNote: 'โหมดสาธิต: เข้าสู่ระบบแบบจำลอง ยังไม่มีการตรวจสอบบัญชีจริงและไม่มีการเก็บรหัสผ่าน',
    footer: 'ข้อมูลสาธิตเท่านั้น ยังไม่ใช่การใช้งานจริง ไม่ผ่านการตรวจสอบ เป็นการประเมินสิ่งแวดล้อม ไม่ใช่การวินิจฉัยทางการแพทย์ และไม่ใช่ clinical decision support',
    footerVersion: 'Airify Demo V1 · mock data',
    statusLabel: { demo: 'สาธิต', planned: 'วางแผน', mock: 'จำลอง', live: 'พร้อมใช้' } as Record<Status, string>,
  },
  en: {
    navPlatform: 'Platform', navHealthApp: 'Health App', navBuild: 'Build', navApis: 'APIs', navStart: 'Start', navFlow: 'How it works',
    openHealth: 'Open Health App', exploreApi: 'Explore API',
    heroChip: 'Airify Platform · Demo', heroKicker: 'Developer Portal',
    heroSub: 'A platform for PM2.5 and personal-exposure data — for developers, cities, and environmental-health products.',
    heroBody: 'Turn environmental data into decision-ready APIs and experiences — demo mode, not production, and not medical advice.',
    ctaTry: 'Explore the API', ctaHealth: 'See Health App Preview', ctaSample: 'View sample data',
    respTitle: 'Example response', flowMini: 'Data flow',
    overviewEyebrow: 'Overview', overviewTitle: 'What is Airify',
    overviewBody: 'Airify is PM2.5 Exposure Intelligence infrastructure that turns environmental data into decision-ready APIs and experiences, and powers products like Airify Health.',
    overviewPoints: ['Hyperlocal nowcast + forecast', 'Personal exposure (intake budget)', 'Decision-ready guidance'],
    previewEyebrow: 'Built on the platform', previewTitle: 'Health App Preview',
    previewIntro: 'Airify Platform powers a consumer Health App — a real example of what you can build on the same APIs.',
    previewBullets: [
      'Daily intake budget — % used today',
      'PM2.5 nowcast with confidence',
      'Check your destination before you leave',
      'Activities: go / be careful / postpone',
      '7-day exposure history',
    ],
    previewCtaApp: 'Open Health App', previewCtaApi: 'See the API behind it',
    buildEyebrow: 'Use cases', buildTitle: 'What you can build',
    apiEyebrow: 'Capabilities', apiTitle: 'API / Capability Catalog',
    apiIntro: 'Clearly separated: available in demo vs. planned.',
    availDemo: 'Available in demo', availPlanned: 'Planned', who: 'For',
    datasetTitle: 'Dataset Catalog', datasetIntro: '7 datasets — 3 demo, 4 planned',
    startEyebrow: 'Getting started', startTitle: 'Quick Start',
    steps: ['Pick an endpoint', 'Try a request', 'Read the response', 'Build it into your app'],
    send: 'Send Request', apiHint: 'Live request against the demo API on the current domain.',
    flowEyebrow: 'How it works', flowTitle: 'How Health App uses the platform',
    flow: ['Location', 'PM2.5 estimate', 'Exposure budget', 'Activity guidance', 'User decision'],
    honestyEyebrow: 'Transparency', honestyTitle: 'Demo mode & limitations',
    honesty: ['This is demo / mock mode — not production.', 'Some APIs are planned and not yet available.', 'Not medical advice or diagnosis.', 'Built for demonstration and product validation.'],
    modelTitle: 'Model transparency', viewModel: 'View Model Card (JSON)', reloadModel: 'Reload Model Card',
    trained: 'Not trained — deterministic demo logic only', validated: 'Validated: false',
    loginTitle: 'Ready to build?',
    loginSub: 'Create a project · Get an API key · Track usage — developer accounts are coming.',
    loginBtn: 'Log in', registerBtn: 'Create developer account', navLogin: 'Log in', navDashboard: 'Dashboard', dashGo: 'Go to Dashboard',
    loginNote: 'Demo mode: mock sign-in only — no real account check and no password stored.',
    footer: 'Demo data only. Not production. Not validated. Environmental estimate only — not medical diagnosis, not clinical decision support.',
    footerVersion: 'Airify Demo V1 · mock data',
    statusLabel: { demo: 'Demo', planned: 'Planned', mock: 'Mock', live: 'Live' } as Record<Status, string>,
  },
};

const scrollToId = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });

function PlatformNav({ theme, onToggleTheme, lang, onToggleLang, t, session }:
  { theme: Theme; onToggleTheme: () => void; lang: Lang; onToggleLang: () => void; t: typeof COPY['th']; session: MockSession | null }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  const isDev = session?.role === 'developer_user';
  return (
    <header className={`dev-nav ${scrolled ? 'dev-nav-scrolled' : ''}`}>
      <div className="dev-nav-inner">
        <button className="dev-nav-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Airify Platform home">
          Airify<span>· Platform</span>
        </button>
        <nav className="dev-nav-links" aria-label="Platform sections">
          <button onClick={() => scrollToId('overview')}>{t.navPlatform}</button>
          <button onClick={() => scrollToId('build')}>{t.navBuild}</button>
          <button onClick={() => scrollToId('apis')}>{t.navApis}</button>
          <button onClick={() => scrollToId('start')}>{t.navStart}</button>
          <button onClick={() => scrollToId('flow')}>{t.navFlow}</button>
        </nav>
        <div className="dev-nav-cta">
          <button className="dev-toggle" onClick={onToggleLang} aria-label="Toggle language TH/EN">
            <Languages size={14} aria-hidden="true" /> {lang === 'th' ? 'EN' : 'TH'}
          </button>
          <button className="dev-toggle" onClick={onToggleTheme} aria-label="Toggle light/dark theme">
            {theme === 'dark' ? <Sun size={15} aria-hidden="true" /> : <Moon size={15} aria-hidden="true" />}
          </button>
          {isDev ? (
            <button className="dev-nav-primary" onClick={() => navigate('/developers/dashboard')}>
              <Gauge size={14} aria-hidden="true" /> {t.navDashboard}
            </button>
          ) : (
            <>
              <button className="dev-nav-ghost" onClick={() => navigate('/developers/login')}>
                <LogIn size={14} aria-hidden="true" /> {t.navLogin}
              </button>
              <button className="dev-nav-primary" onClick={() => navigate('/developers/register')}>
                <UserPlus size={14} aria-hidden="true" /> {lang === 'th' ? 'สมัคร' : 'Sign up'}
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

/** Static, clearly-labeled phone mockup of the Health App (representative demo values). */
function HealthPhonePreview() {
  return (
    <div className="dev-phone" aria-hidden="true">
      <div className="dev-phone-notch" />
      <div className="dev-phone-screen">
        <div className="dev-phone-top">
          <div>
            <div className="dev-phone-today">วันนี้</div>
            <div className="dev-phone-loc">นนทบุรี · demo</div>
          </div>
          <span className="dev-phone-chip">ปานกลาง</span>
        </div>
        <div className="dev-phone-hero">
          <div className="dev-phone-hero-label">วันนี้อากาศแถวคุณ</div>
          <div className="dev-phone-hero-score">27<span>µg/m³</span></div>
          <div className="dev-phone-hero-bar"><span style={{ width: '45%' }} /></div>
        </div>
        <div className="dev-phone-card">
          <div className="dev-phone-card-title">งบรับฝุ่นวันนี้</div>
          <div className="dev-phone-budget">64<span>% ของงบต่อวัน</span></div>
          <div className="dev-phone-track"><span style={{ width: '64%' }} /></div>
          <div className="dev-phone-meta">ค่าอ้างอิงสาธิต · adult_general</div>
        </div>
        <div className="dev-phone-row2">
          <div className="dev-phone-mini">
            <div className="dev-phone-mini-label">วิ่ง 30 นาที</div>
            <div className="dev-phone-mini-num">ควรระวัง</div>
            <div className="dev-phone-mini-unit">ลดเวลา + หน้ากาก</div>
          </div>
          <div className="dev-phone-mini">
            <div className="dev-phone-mini-label">ช่วงที่ดีกว่า</div>
            <div className="dev-phone-mini-num">18:00</div>
            <div className="dev-phone-mini-unit">ฝุ่นมีแนวโน้มลดลง</div>
          </div>
        </div>
        <div className="dev-phone-history">
          {[42, 30, 55, 38, 61, 27, 44].map((h, i) => (
            <span key={i} style={{ height: `${h}%` }} />
          ))}
        </div>
        <div className="dev-phone-nav">
          <span className="active">วันนี้</span>
          <span>พื้นที่</span>
          <span>กิจกรรม</span>
          <span>Timeline</span>
          <span>บัญชี</span>
        </div>
      </div>
    </div>
  );
}

export function DevelopersPage({ theme, onToggleTheme, lang, onToggleLang }: Props) {
  const t = COPY[lang];
  const session = useMockSession();
  const [lat, setLat] = useState('13.7563');
  const [lon, setLon] = useState('100.5018');
  const [activity, setActivity] = useState('walking');
  const [duration, setDuration] = useState('30');
  const [forecastType, setForecastType] = useState('nowcast');
  const [userGroup, setUserGroup] = useState('adult_general');
  const [result, setResult] = useState<object | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [modelCard, setModelCard] = useState<object | null>(null);
  const [error, setError] = useState<string | null>(null);

  const endpoint = `/v1/developer/sample?lat=${lat}&lon=${lon}&activity=${activity}&duration_minutes=${duration}&forecast_type=${forecastType}&user_group=${userGroup}`;

  const fetchSample = async () => {
    setError(null);
    const t0 = performance.now();
    try {
      const r = await fetch(buildApiUrl(endpoint));
      setResult(await r.json());
      setLatency(Math.round(performance.now() - t0));
    } catch {
      setError(lang === 'th' ? 'ระบบข้อมูลยังไม่พร้อมใช้งานชั่วคราว กรุณาลองใหม่อีกครั้ง' : 'Data service temporarily unavailable. Please try again.');
    }
  };
  const fetchModelCard = async () => {
    setError(null);
    try {
      const r = await fetch(buildApiUrl('/v1/model/card'));
      setModelCard(await r.json());
    } catch {
      setError(lang === 'th' ? 'ระบบข้อมูลยังไม่พร้อมใช้งานชั่วคราว กรุณาลองใหม่อีกครั้ง' : 'Data service temporarily unavailable. Please try again.');
    }
  };

  const heroJson = `{
  "location": { "lat": ${lat}, "lon": ${lon} },
  "prediction": { "pm25_estimate": 27, "confidence": "high", "data_status": "demo" },
  "exposure": { "daily_intake_percent": 64, "exposure_level": "moderate" }
}`;

  const demoApis = PLATFORM_APIS.filter(a => a.status === 'demo');
  const plannedApis = PLATFORM_APIS.filter(a => a.status !== 'demo');
  const renderApiCard = (a: typeof PLATFORM_APIS[number]) => {
    const c = a[lang];
    return (
      <div key={c.name + a.path} className="glass dev-api-card">
        <div className="dev-api-head">
          <span className="dev-cap-icon" aria-hidden="true">{a.icon}</span>
          <StatusBadge status={a.status} label={t.statusLabel[a.status]} />
        </div>
        <h4>{c.name}</h4>
        <p>{c.desc}</p>
        <code className="dev-api-path">{a.path}</code>
        <div className="dev-api-who"><span>{t.who}:</span> {c.who}</div>
      </div>
    );
  };

  return (
    <div className="dev-page">
      <PlatformNav theme={theme} onToggleTheme={onToggleTheme} lang={lang} onToggleLang={onToggleLang} t={t} session={session} />

      {/* 1. Hero — full-bleed band, inner container */}
      <section className="dev-band dev-band-hero">
        <div className="dev-orbs" aria-hidden="true">
          <div className="dev-orb dev-orb-1" />
          <div className="dev-orb dev-orb-2" />
          <div className="dev-orb dev-orb-3" />
        </div>
        <div className="dev-container dev-hero-split">
          <div className="dev-hero-left">
            <span className="dev-hero-chip">{t.heroChip}</span>
            <h2>Airify Platform</h2>
            <div className="dev-hero-kicker">{t.heroKicker}</div>
            <div className="dev-hero-sub">{t.heroSub}</div>
            <p className="dev-hero-body">{t.heroBody}</p>
            <div className="dev-hero-actions">
              <button className="btn btn-hero-primary" onClick={() => scrollToId('start')}>
                {t.ctaTry} <ArrowRight size={16} aria-hidden="true" />
              </button>
              <button className="btn btn-hero-ghost" onClick={() => scrollToId('health-preview')}>
                <Smartphone size={16} aria-hidden="true" /> {t.ctaHealth}
              </button>
              <button className="btn btn-hero-ghost" onClick={() => scrollToId('apis')}>{t.ctaSample}</button>
            </div>
          </div>
          <div className="dev-hero-panel">
            <div className="dev-hero-flow">
              <span className="dev-hero-flow-label">{t.flowMini}</span>
              <div className="dev-hero-flow-steps">
                {t.flow.map((f, i) => (
                  <span key={f} className="dev-hero-flow-step">{f}{i < t.flow.length - 1 && <em>→</em>}</span>
                ))}
              </div>
            </div>
            <div className="dev-hero-resp-title">{t.respTitle}</div>
            <pre className="dev-hero-json">{heroJson}</pre>
            <div className="dev-hero-chips">
              {PLATFORM_APIS.slice(0, 5).map(a => <span key={a.path + a.icon} className="dev-hero-chip-mini">{a[lang].name}</span>)}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Platform Overview */}
      <section id="overview" className="dev-band">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.overviewEyebrow}</div>
          <h3 className="dev-section-h3">{t.overviewTitle}</h3>
          <p className="dev-section-intro" style={{ maxWidth: '68ch' }}>{t.overviewBody}</p>
          <div className="dev-overview-points">
            {t.overviewPoints.map(p => <div key={p} className="dev-overview-point"><span>✓</span> {p}</div>)}
          </div>
        </div>
      </section>

      {/* 3. Health App Preview — restored */}
      <section id="health-preview" className="dev-band dev-band-alt">
        <div className="dev-container dev-health-preview">
          <div className="dev-health-copy">
            <div className="dev-eyebrow">{t.previewEyebrow}</div>
            <h3 className="dev-section-h3">{t.previewTitle}</h3>
            <p className="dev-section-intro" style={{ maxWidth: '52ch' }}>{t.previewIntro}</p>
            <ul className="dev-feature-list">
              {t.previewBullets.map(b => (
                <li key={b}><span aria-hidden="true">✓</span> {b}</li>
              ))}
            </ul>
            <div className="dev-hero-actions" style={{ marginTop: 18 }}>
              <button className="btn btn-primary" onClick={() => navigateTo('health')}>
                <Smartphone size={16} aria-hidden="true" /> {t.previewCtaApp} <ArrowRight size={15} aria-hidden="true" />
              </button>
              <button className="btn btn-secondary" onClick={() => scrollToId('start')}>{t.previewCtaApi}</button>
            </div>
            <p className="dev-section-intro" style={{ marginTop: 12 }}>
              {lang === 'th'
                ? 'การประเมินสิ่งแวดล้อมเท่านั้น ไม่ใช่การวินิจฉัยทางการแพทย์'
                : 'Environmental estimate only. Not medical diagnosis.'}
            </p>
          </div>
          <div className="dev-health-device">
            <HealthPhonePreview />
          </div>
        </div>
      </section>

      {/* 4. What You Can Build */}
      <section id="build" className="dev-band">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.buildEyebrow}</div>
          <h3 className="dev-section-h3">{t.buildTitle}</h3>
          <div className="dev-use-grid">
            {USE_CASES.map(u => (
              <div key={u.icon + u[lang].title} className="glass dev-use-card">
                <div className="dev-cap-icon" aria-hidden="true">{u.icon}</div>
                <h4>{u[lang].title}</h4>
                <p>{u[lang].desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 5. API / Capability Catalog */}
      <section id="apis" className="dev-band dev-band-alt">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.apiEyebrow}</div>
          <h3 className="dev-section-h3">{t.apiTitle}</h3>
          <p className="dev-section-intro">{t.apiIntro}</p>
          <div className="dev-avail-label"><StatusBadge status="demo" label={t.statusLabel.demo} /> {t.availDemo}</div>
          <div className="dev-api-grid">{demoApis.map(renderApiCard)}</div>
          <div className="dev-avail-label" style={{ marginTop: 18 }}><StatusBadge status="planned" label={t.statusLabel.planned} /> {t.availPlanned}</div>
          <div className="dev-api-grid">{plannedApis.map(renderApiCard)}</div>

          <div className="glass dev-section" style={{ marginTop: 18 }}>
            <div className="dev-eyebrow">Data</div>
            <h3>{t.datasetTitle}</h3>
            <p className="dev-section-intro">{t.datasetIntro}</p>
            {DATASETS.map(d => (
              <div key={d[lang].name} className="dev-kv">
                <span>
                  <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{d[lang].name}</span>
                  <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{d[lang].desc}</span>
                </span>
                <StatusBadge status={d.status} label={t.statusLabel[d.status]} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Quick Start + live playground */}
      <section id="start" className="dev-band">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.startEyebrow}</div>
          <h3 className="dev-section-h3">{t.startTitle}</h3>
          <div className="glass dev-section">
            <div className="dev-steps">
              {t.steps.map((s, i) => (
                <div key={s} className="dev-step"><span className="dev-step-num">{i + 1}</span> {s}</div>
              ))}
            </div>
            <p className="dev-section-intro" style={{ marginTop: 14 }}>{t.apiHint}</p>
            <div className="dev-endpoint-bar">
              <span className="dev-method">GET</span>
              <span>{endpoint}</span>
            </div>
            <div className="dev-play-inputs">
              <input className="input-field" placeholder="lat" aria-label="lat" value={lat} onChange={e => setLat(e.target.value)} />
              <input className="input-field" placeholder="lon" aria-label="lon" value={lon} onChange={e => setLon(e.target.value)} />
              <select className="input-field" aria-label="activity" value={activity} onChange={e => setActivity(e.target.value)}>
                {ACTIVITIES.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
              <input className="input-field" type="number" placeholder="duration_minutes" aria-label="duration_minutes" value={duration} onChange={e => setDuration(e.target.value)} />
              <select className="input-field" aria-label="forecast_type" value={forecastType} onChange={e => setForecastType(e.target.value)}>
                <option value="nowcast">nowcast</option>
                <option value="1h_forecast">1h_forecast</option>
                <option value="2h_forecast">2h_forecast</option>
              </select>
              <select className="input-field" aria-label="user_group" value={userGroup} onChange={e => setUserGroup(e.target.value)}>
                {USER_GROUPS.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <button className="btn btn-primary" style={{ width: '100%', marginTop: 12 }} onClick={fetchSample}>{t.send}</button>
            {error && <p style={{ marginTop: 10, fontSize: '0.85rem', color: 'var(--color-danger)', fontWeight: 600 }}>{error}</p>}
            {result && (
              <div style={{ marginTop: 14 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                  <span className="status-badge status-ok">200 OK</span>
                  {latency !== null && <span className="status-badge status-planned">{latency} ms</span>}
                  <span className="status-badge status-demo">application/json</span>
                </div>
                <pre className="dev-json">{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 7. How Health App uses the platform */}
      <section id="flow" className="dev-band dev-band-alt">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.flowEyebrow}</div>
          <h3 className="dev-section-h3">{t.flowTitle}</h3>
          <div className="dev-flow">
            {t.flow.map((f, i) => (
              <div key={f} className="dev-flow-item">
                <div className="dev-flow-step">{f}</div>
                {i < t.flow.length - 1 && <span className="dev-flow-arrow" aria-hidden="true">→</span>}
              </div>
            ))}
          </div>
          <div className="dev-hero-actions" style={{ marginTop: 6 }}>
            <button className="btn btn-primary" onClick={() => navigateTo('health')}>
              {t.openHealth} <ArrowUpRight size={15} aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>

      {/* 8. Model transparency + Demo honesty */}
      <section className="dev-band">
        <div className="dev-container">
          <div className="dev-eyebrow">{t.honestyEyebrow}</div>
          <h3 className="dev-section-h3">{t.modelTitle}</h3>
          <div className="dev-model-panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <strong>Airify PI-ML Lite</strong>
              <span className="dev-inline-code">{MODEL_VERSION}</span>
              <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                <StatusBadge status="demo" label={t.statusLabel.demo} />
                <StatusBadge status="mock" label={t.validated} />
              </span>
            </div>
            <div className="dev-kv" style={{ marginTop: 8 }}>
              <span className="k">Outputs</span>
              <span className="v"><code>pm25_estimate</code> <code>confidence</code> <code>uncertainty</code> <code>model_version</code> <code>data_status</code></span>
            </div>
            <div className="dev-kv">
              <span className="k">Training</span>
              <span className="v">{t.trained}</span>
            </div>
            <button className="btn btn-secondary" style={{ marginTop: 12 }} onClick={fetchModelCard}>
              {modelCard ? t.reloadModel : t.viewModel}
            </button>
            {modelCard && <pre className="dev-json" style={{ marginTop: 10, maxHeight: 300 }}>{JSON.stringify(modelCard, null, 2)}</pre>}
          </div>
          <h3 className="dev-section-h3" style={{ marginTop: 20 }}>{t.honestyTitle}</h3>
          <ul className="dev-gov-list" style={{ marginTop: 10 }}>
            {t.honesty.map(h => <li key={h}>{h}</li>)}
          </ul>
        </div>
      </section>

      {/* 9. Developer Login CTA — real navigation to /#/login & /#/register */}
      <section className="dev-band dev-band-cta">
        <div className="dev-container dev-login-cta">
          <KeyRound size={30} aria-hidden="true" className="dev-login-icon" />
          <h3 className="dev-section-h3">{t.loginTitle}</h3>
          <p className="dev-section-intro">{t.loginSub}</p>
          {session?.role === 'developer_user' ? (
            <>
              <div className="dev-hero-actions" style={{ justifyContent: 'center' }}>
                <button className="btn btn-primary" onClick={() => navigate('/developers/dashboard')}>
                  <Gauge size={16} aria-hidden="true" /> {t.dashGo}
                </button>
                <button className="btn btn-secondary" onClick={() => { clearMockSession(); }}>
                  <LogOut size={16} aria-hidden="true" /> {lang === 'th' ? 'ออกจากระบบ' : 'Log out'}
                </button>
              </div>
              <p className="dev-section-intro" style={{ marginTop: 10 }}>
                {lang === 'th' ? `เข้าสู่ระบบแล้วในชื่อ ${session.displayName} (เซสชันสาธิต)` : `Signed in as ${session.displayName} (demo session)`}
              </p>
            </>
          ) : (
            <>
              <div className="dev-hero-actions" style={{ justifyContent: 'center' }}>
                <button className="btn btn-primary" onClick={() => navigate('/developers/login')}>
                  <LogIn size={16} aria-hidden="true" /> {t.loginBtn}
                </button>
                <button className="btn btn-secondary" onClick={() => navigate('/developers/register')}>
                  <UserPlus size={16} aria-hidden="true" /> {t.registerBtn}
                </button>
              </div>
              <p className="dev-section-intro" style={{ marginTop: 10 }}>{t.loginNote}</p>
            </>
          )}
          <AppStoreCTA title={lang === 'th' ? 'หรือลองใช้ Airify Health App' : 'Or try the Airify Health App'} />
        </div>
      </section>

      {/* 10. Footer */}
      <footer className="dev-footer">
        <div className="dev-container">
          <div className="dev-footer-row">
            <span className="dev-nav-brand" style={{ cursor: 'default' }}>Airify<span>· Platform</span></span>
            <nav className="dev-footer-links" aria-label="Footer">
              <button onClick={() => scrollToId('apis')}>APIs</button>
              <button onClick={() => scrollToId('start')}>Quick Start</button>
              <button onClick={() => navigateTo('health')}>Health App</button>
            </nav>
          </div>
          <p className="dev-footer-note">⚠️ {t.footer}</p>
          <p className="dev-footer-note">{t.footerVersion}</p>
        </div>
      </footer>
    </div>
  );
}
