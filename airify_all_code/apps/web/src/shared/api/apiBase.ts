/**
 * Shared API base URL helper for Airify frontend.
 *
 * Behavior:
 * - If VITE_API_BASE_URL env is set (e.g., during local dev), uses that.
 * - Otherwise defaults to same-origin relative paths (empty string).
 *   This makes fetch("/v1/...") work correctly on any deployed domain
 *   (e.g., http://airify.zentia.tech, localhost:8000, etc.)
 *
 * Usage:
 *   import { buildApiUrl, API_ERROR_TH, API_ERROR_EN } from '../shared/api/apiBase';
 *   fetch(buildApiUrl('/v1/prediction/estimate?...'))
 */

const configured = import.meta.env.VITE_API_BASE_URL;

/** Resolved API base. Empty string = same-origin relative. */
export const API_BASE: string = configured
  ? String(configured).replace(/\/+$/, '')
  : '';

/**
 * Build a full API URL from a path.
 * @param path - Must start with "/" (e.g., "/v1/prediction/estimate?lat=...")
 */
export function buildApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** Public-safe Thai error message (no developer instructions). */
export const API_ERROR_TH = 'ระบบข้อมูลยังไม่พร้อมใช้งานชั่วคราว กรุณาลองใหม่อีกครั้ง';

/** Public-safe English error message. */
export const API_ERROR_EN = 'Data service temporarily unavailable. Please try again.';
