/** Health domain static data — activity set, decision activities, and bottom-nav
 * sections. Thai-first labels for the Airify Health App (general public). Activity
 * `id` values stay aligned to the backend exposure contract; only labels are Thai. */

export interface ActivityOption { id: string; label: string; icon: string }

/** Activities the exposure calculator can log (ids match the backend contract). */
export const ACTIVITIES: ActivityOption[] = [
  { id: 'walking', label: 'เดิน', icon: '🚶' },
  { id: 'running', label: 'วิ่ง', icon: '🏃' },
  { id: 'motorbike_commute', label: 'มอเตอร์ไซค์', icon: '🛵' },
  { id: 'car_commute', label: 'รถยนต์', icon: '🚗' },
  { id: 'indoor', label: 'อยู่ในบ้าน', icon: '🏠' },
  { id: 'outdoor_sitting', label: 'นั่งกลางแจ้ง', icon: '🪑' },
];

/** Indoor/resting inhalation-rate baseline (m³/hr) for the "activity impact" display. */
export const RESTING_IR = 0.5;

/** User-facing daily decisions shown as activity risk cards. `sensitivity` scales
 * the current PM2.5 into an effective exposure for the decision band — purely a
 * frontend display heuristic, NOT a medical threshold. */
export interface DecisionActivity { id: string; label: string; icon: string; sensitivity: number }

export const DECISION_ACTIVITIES: DecisionActivity[] = [
  { id: 'run_outdoor', label: 'วิ่งกลางแจ้ง', icon: '🏃', sensitivity: 1.45 },
  { id: 'commute', label: 'เดินทางไปทำงาน', icon: '🛵', sensitivity: 1.0 },
  { id: 'children_outdoor', label: 'พาเด็กออกนอกบ้าน', icon: '🧒', sensitivity: 1.6 },
  { id: 'open_window', label: 'เปิดหน้าต่าง', icon: '🪟', sensitivity: 1.1 },
  { id: 'indoor_exercise', label: 'ออกกำลังกายในบ้าน', icon: '🧘', sensitivity: 0.45 },
];

export interface NavSection { id: string; label: string; icon: string }

export const SECTIONS: NavSection[] = [
  { id: 'today', label: 'วันนี้', icon: '☀️' },
  { id: 'places', label: 'พื้นที่', icon: '📍' },
  { id: 'history', label: 'ประวัติ', icon: '📅' },
  { id: 'profile', label: 'บัญชี', icon: '👤' },
];
