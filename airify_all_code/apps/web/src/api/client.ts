/**
 * API client for Airify backend.
 * Calls LOCAL backend only. No external services.
 */

import type { DemoState, EventSummary, ExperimentAssignment } from './types';
import { buildApiUrl } from '../shared/api/apiBase';


async function get<T>(path: string): Promise<T> {
  const resp = await fetch(buildApiUrl(path));
  if (!resp.ok) throw new Error(`API ${resp.status}: ${path}`);
  return resp.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(buildApiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`API ${resp.status}: ${path}`);
  return resp.json();
}

export function getAssignment(sessionId: string): Promise<ExperimentAssignment> {
  return get(`/v1/experiments/assignment?session_id=${encodeURIComponent(sessionId)}`);
}

export function getDemoState(lat: number, lon: number, sessionId: string): Promise<DemoState> {
  return get(`/v1/platform/demo-state?lat=${lat}&lon=${lon}&session_id=${encodeURIComponent(sessionId)}`);
}

export function getEventsSummary(): Promise<EventSummary> {
  return get('/v1/events/summary');
}

export function trackEvent(event: {
  session_id: string;
  variant: string | null;
  event_type: string;
  lat_rounded?: number | null;
  lon_rounded?: number | null;
  payload?: Record<string, unknown>;
}): Promise<unknown> {
  return post('/v1/events', event).catch(() => null);
}
