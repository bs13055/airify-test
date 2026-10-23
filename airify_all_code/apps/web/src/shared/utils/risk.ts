/** Demo risk scale — environmental exposure guidance display ONLY.
 *
 * These bands color-code demo PM2.5/exposure values for the UI.
 * They are NOT health standards, NOT medical thresholds, NOT diagnosis,
 * and NOT clinical decision support.
 */

export type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high' | 'severe';

export const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  very_high: 'Very High',
  severe: 'Severe',
};

/** CSS class that sets --risk-color / --risk-bg / --risk-hero (see global.css). */
export const RISK_CLASS: Record<RiskLevel, string> = {
  low: 'risk-low',
  moderate: 'risk-moderate',
  high: 'risk-high',
  very_high: 'risk-very-high',
  severe: 'risk-severe',
};

/** Display bands for demo PM2.5 values (µg/m³). Demo engine emits ~5–60. */
export function riskFromPm25(pm25: number): RiskLevel {
  if (pm25 < 15) return 'low';
  if (pm25 < 30) return 'moderate';
  if (pm25 < 40) return 'high';
  if (pm25 < 50) return 'very_high';
  return 'severe';
}

/** Map the backend `exposure_level` field (low/moderate/high/very_high) onto the scale. */
export function riskFromExposureLevel(level: string): RiskLevel {
  if (level === 'low' || level === 'moderate' || level === 'high' || level === 'very_high' || level === 'severe') {
    return level;
  }
  return 'moderate';
}

/** Frontend-derived 0–100 demo display score (pm25 scaled over the demo range). */
export function scoreFromPm25(pm25: number): number {
  return Math.max(0, Math.min(100, Math.round((pm25 / 60) * 100)));
}
