/** Developer Portal static content — platform APIs, dataset catalog, and use cases.
 * Bilingual (Thai-first / English) copy for the Airify Platform gateway. Demo/mock
 * mode: statuses are honest (demo vs planned); nothing here is production. */

import type { Status } from '../../../shared/components/StatusBadge';

export type Lang = 'th' | 'en';
interface Localized { name: string; desc: string; who: string }

export interface PlatformApi {
  icon: string;
  status: Status;
  path: string;
  th: Localized;
  en: Localized;
}

/** Capability / API catalog. Clearly separated by status (demo vs planned). */
export const PLATFORM_APIS: PlatformApi[] = [
  {
    icon: '📈', status: 'demo', path: '/v1/prediction/estimate',
    th: { name: 'PM2.5 Prediction API', desc: 'ค่าฝุ่นรอบตัวแบบ nowcast และพยากรณ์ 1–2 ชั่วโมง พร้อมค่าความมั่นใจและความไม่แน่นอน', who: 'แอปสุขภาพ · ระบบแจ้งเตือน · dashboard เมือง' },
    en: { name: 'PM2.5 Prediction API', desc: 'Hyperlocal nowcast plus 1h/2h forecasts, each with confidence and uncertainty.', who: 'Health apps · alerting · city dashboards' },
  },
  {
    icon: '🫁', status: 'demo', path: '/v1/exposure/estimate',
    th: { name: 'Exposure Budget API', desc: 'ประเมินฝุ่นที่ร่างกายรับต่อวัน (งบรับฝุ่น) ตามกิจกรรมและกลุ่มผู้ใช้ — โหมดสาธิต ไม่ใช่ค่ามาตรฐานทางการแพทย์', who: 'แอปสุขภาพ · แผนกิจกรรม · well-being' },
    en: { name: 'Exposure Budget API', desc: 'Activity-aware inhaled PM2.5 and a daily intake budget by user group. Demo, not a medical limit.', who: 'Health apps · activity planning · well-being' },
  },
  {
    icon: '🧭', status: 'demo', path: '/v1/exposure/estimate',
    th: { name: 'Activity Guidance API', desc: 'แปลงค่าฝุ่นเป็นคำแนะนำเชิงตัดสินใจ เช่น ทำได้ / ควรระวัง / ควรเลื่อน สำหรับกิจกรรมกลางแจ้ง', who: 'แอปไลฟ์สไตล์ · คำแนะนำเส้นทาง/กิจกรรม' },
    en: { name: 'Activity Guidance API', desc: 'Turns exposure into decisions — go / be careful / postpone — for everyday outdoor activities.', who: 'Lifestyle apps · route & activity guidance' },
  },
  {
    icon: '📅', status: 'demo', path: '/v1/timeline/demo',
    th: { name: 'Timeline API', desc: 'ประวัติค่าฝุ่นและการรับฝุ่นย้อนหลัง 7 วัน พร้อมสรุปค่าเฉลี่ย', who: 'dashboard · รายงาน · การวิเคราะห์แนวโน้ม' },
    en: { name: 'Timeline API', desc: '7-day PM2.5 and exposure history with a rolling summary.', who: 'Dashboards · reporting · trend analysis' },
  },
  {
    icon: '🎯', status: 'demo', path: '/v1/prediction/estimate',
    th: { name: 'Confidence / Data Trust API', desc: 'ระดับความมั่นใจของข้อมูล (สูง/ปานกลาง/ต่ำ) และค่าความไม่แน่นอน เพื่อความโปร่งใส', who: 'ทีมที่ต้องการความโปร่งใสของข้อมูล' },
    en: { name: 'Confidence / Data Trust API', desc: 'Per-estimate confidence (high/medium/low) and uncertainty for transparent products.', who: 'Teams that need data transparency' },
  },
  {
    icon: '🗂️', status: 'planned', path: '/v1/datasets · planned',
    th: { name: 'Dataset Catalog API', desc: 'รายการชุดข้อมูล PM2.5 และการรับฝุ่นสำหรับต่อยอด — อยู่ระหว่างวางแผน', who: 'นักวิจัย · ทีมเมือง · data product' },
    en: { name: 'Dataset Catalog API', desc: 'Discoverable PM2.5 & exposure datasets to build on — planned, not yet available.', who: 'Researchers · city teams · data products' },
  },
];

export interface Dataset { status: Status; th: { name: string; desc: string }; en: { name: string; desc: string } }

/** Dataset catalog — 7 rows: 3 demo, 4 planned (matches the demo engine surface). */
export const DATASETS: Dataset[] = [
  { status: 'demo', th: { name: 'Hyperlocal PM2.5 Grid', desc: 'พื้นผิวค่าฝุ่นสาธิตแบบกำหนดผลได้สำหรับทุกพิกัด' }, en: { name: 'Hyperlocal PM2.5 Grid', desc: 'Deterministic demo PM2.5 surface for any lat/lon.' } },
  { status: 'demo', th: { name: 'PM2.5 Daily Intake Criteria v0.1', desc: 'งบรับฝุ่นรายวันแบบอ้างอิงเชิงปฏิบัติ แยกตามกลุ่มผู้ใช้ — สาธิต ไม่ใช่ค่ามาตรฐานทางการแพทย์' }, en: { name: 'PM2.5 Daily Intake Criteria v0.1', desc: 'Operational-reference daily intake budgets by user group. Demo, not a medical safe limit.' } },
  { status: 'demo', th: { name: 'Health Criteria Dataset', desc: 'เกณฑ์บริบทสุขภาพเชิงไม่ใช่การแพทย์และระดับอ้างอิง' }, en: { name: 'Health Criteria Dataset', desc: 'Structured non-medical health-context criteria and reference tiers.' } },
  { status: 'planned', th: { name: 'Exposure Summary Dataset', desc: 'สรุปการรับฝุ่นรายวันแบบรวม' }, en: { name: 'Exposure Summary Dataset', desc: 'Aggregated daily exposure summaries.' } },
  { status: 'planned', th: { name: 'Risk Tile Dataset', desc: 'ไทล์ความเสี่ยงสำหรับ dashboard เมือง' }, en: { name: 'Risk Tile Dataset', desc: 'Map-ready risk tiles for city dashboards.' } },
  { status: 'planned', th: { name: 'Model Benchmark Dataset', desc: 'ชุดอ้างอิงสำหรับประเมินโมเดลในอนาคต' }, en: { name: 'Model Benchmark Dataset', desc: 'Reference set for future model evaluation.' } },
  { status: 'planned', th: { name: 'Research Export Dataset', desc: 'ข้อมูลรวมแบบไม่ระบุตัวตนสำหรับงานวิจัย' }, en: { name: 'Research Export Dataset', desc: 'Anonymized aggregate export for research use.' } },
];

export interface UseCase { icon: string; th: { title: string; desc: string }; en: { title: string; desc: string } }

/** "What you can build" — audience-facing product ideas on top of the platform. */
export const USE_CASES: UseCase[] = [
  { icon: '📱', th: { title: 'แอปสุขภาพ', desc: 'ผู้ช่วยตัดสินใจเรื่องฝุ่นในชีวิตประจำวัน เช่น Airify Health' }, en: { title: 'Health apps', desc: 'A daily PM2.5 decision companion like Airify Health.' } },
  { icon: '🔔', th: { title: 'ระบบแจ้งเตือนรายพื้นที่', desc: 'เตือนเมื่อค่าฝุ่นในพื้นที่เริ่มมีผลต่อสุขภาพ' }, en: { title: 'Area alerts', desc: 'Notify people when local PM2.5 starts to matter.' } },
  { icon: '🏙️', th: { title: 'Dashboard เมือง', desc: 'ภาพรวมค่าฝุ่นและความเสี่ยงสำหรับทีมเมือง' }, en: { title: 'City dashboards', desc: 'PM2.5 and risk overviews for city teams.' } },
  { icon: '🧭', th: { title: 'คำแนะนำเส้นทาง/กิจกรรม', desc: 'แนะนำเวลาและกิจกรรมที่รับฝุ่นน้อยลง' }, en: { title: 'Route & activity guidance', desc: 'Recommend lower-exposure times and activities.' } },
  { icon: '🏫', th: { title: 'แจ้งเตือนโรงเรียน/ชุมชน', desc: 'ช่วยโรงเรียนและชุมชนตัดสินใจกิจกรรมกลางแจ้ง' }, en: { title: 'School / community alerts', desc: 'Help schools and communities decide on outdoor activity.' } },
  { icon: '📦', th: { title: 'ผลิตภัณฑ์ข้อมูลสิ่งแวดล้อม', desc: 'ต่อยอดชุดข้อมูล PM2.5 และการรับฝุ่นเป็นผลิตภัณฑ์' }, en: { title: 'Environmental data products', desc: 'Build products on PM2.5 & exposure datasets.' } },
];
