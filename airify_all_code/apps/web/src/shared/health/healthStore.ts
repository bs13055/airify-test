/** Mock Health App store — frequent places, consent flags, and the
 * "share data for development" toggle. Phase-1 demo only: persisted in
 * localStorage on the user's device, no backend, no real personal data.
 */

import { useEffect, useState } from 'react';
import type { RiskLevel } from '../utils/risk';

export interface FreqPlace {
  id: string;
  name: string;
  icon: string; // lucide icon name (rendered by the page)
  lat: number;
  lon: number;
  /** Demo PM2.5 multiplier vs the current-area estimate (deterministic mock). */
  factor: number;
}

/** Demo catalog of places used by the Map + Activity pages. */
export const PLACE_CATALOG: FreqPlace[] = [
  { id: 'home', name: 'บ้าน', icon: 'House', lat: 13.861, lon: 100.514, factor: 0.85 },
  { id: 'work', name: 'ที่ทำงาน', icon: 'Briefcase', lat: 13.724, lon: 100.534, factor: 1.15 },
  { id: 'park', name: 'สวนสาธารณะ', icon: 'Trees', lat: 13.781, lon: 100.545, factor: 0.7 },
  { id: 'gym', name: 'ฟิตเนส', icon: 'Dumbbell', lat: 13.75, lon: 100.5, factor: 0.55 },
];

export function placeById(id: string): FreqPlace | undefined {
  return PLACE_CATALOG.find(p => p.id === id);
}

/** Plain-Thai go / no-go advice for a place risk band (display only, non-medical). */
export function placeAdvice(risk: RiskLevel): { canGo: boolean; verdict: string; protection: string } {
  switch (risk) {
    case 'low':
      return { canGo: true, verdict: 'ไปได้ตามปกติ', protection: 'ทำกิจกรรมกลางแจ้งได้ ไม่ต้องป้องกันเป็นพิเศษ' };
    case 'moderate':
      return { canGo: true, verdict: 'ไปได้ ควรพักเป็นระยะ', protection: 'อยู่กลางแจ้งได้ แต่ถ้านานควรพัก และพกหน้ากากไว้' };
    case 'high':
      return { canGo: true, verdict: 'ไปได้ แต่จำกัดเวลา', protection: 'จำกัดกิจกรรมกลางแจ้ง ~30 นาที และใส่หน้ากาก' };
    case 'very_high':
      return { canGo: false, verdict: 'ควรเลี่ยง', protection: 'เลี่ยงกิจกรรมกลางแจ้งที่ใช้แรง ใส่หน้ากาก N95 ถ้าจำเป็นต้องออก' };
    default:
      return { canGo: false, verdict: 'ไม่แนะนำให้ออก', protection: 'ควรอยู่ในอาคารที่อากาศสะอาด ปิดหน้าต่าง' };
  }
}

export interface Consent {
  locationHistory: boolean;
  exposureTimeline: boolean;
  frequentSuggestions: boolean;
}
export interface HealthPrefs {
  frequentPlaceIds: string[];
  consent: Consent;
  shareData: boolean;
}

const KEY = 'airify_health_prefs';
const DEFAULT_PREFS: HealthPrefs = {
  frequentPlaceIds: ['home', 'work'],
  consent: { locationHistory: true, exposureTimeline: true, frequentSuggestions: true },
  shareData: false,
};

const listeners = new Set<() => void>();
function emit() { listeners.forEach(l => l()); }

export function getHealthPrefs(): HealthPrefs {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const p = JSON.parse(raw) as Partial<HealthPrefs>;
      return {
        frequentPlaceIds: Array.isArray(p.frequentPlaceIds) ? p.frequentPlaceIds : DEFAULT_PREFS.frequentPlaceIds,
        consent: { ...DEFAULT_PREFS.consent, ...(p.consent || {}) },
        shareData: !!p.shareData,
      };
    }
  } catch { /* ignore */ }
  return { ...DEFAULT_PREFS, consent: { ...DEFAULT_PREFS.consent } };
}

function save(next: HealthPrefs) {
  try { localStorage.setItem(KEY, JSON.stringify(next)); } catch { /* ignore */ }
  emit();
}

export function addFrequentPlace(id: string) {
  const p = getHealthPrefs();
  if (!p.frequentPlaceIds.includes(id)) save({ ...p, frequentPlaceIds: [...p.frequentPlaceIds, id] });
}
export function removeFrequentPlace(id: string) {
  const p = getHealthPrefs();
  save({ ...p, frequentPlaceIds: p.frequentPlaceIds.filter(x => x !== id) });
}
export function setConsent(key: keyof Consent, value: boolean) {
  const p = getHealthPrefs();
  save({ ...p, consent: { ...p.consent, [key]: value } });
}
export function setShareData(value: boolean) {
  save({ ...getHealthPrefs(), shareData: value });
}
/** Delete all mock/demo saved data (frequent places + timeline consent) on this device. */
export function resetHealthData() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
  emit();
}

export function useHealthPrefs(): HealthPrefs {
  const [prefs, setPrefs] = useState<HealthPrefs>(getHealthPrefs);
  useEffect(() => {
    const cb = () => setPrefs(getHealthPrefs());
    listeners.add(cb);
    window.addEventListener('storage', cb);
    return () => { listeners.delete(cb); window.removeEventListener('storage', cb); };
  }, []);
  return prefs;
}
