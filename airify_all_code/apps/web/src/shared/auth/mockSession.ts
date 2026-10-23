/** Phase-1 mock session — client-side UI state only.
 *
 * There is NO real authentication here: no backend, no token/JWT, no password
 * storage. `setMockSession` persists a small, safe UI object to localStorage so
 * the demo can show a "logged-in" experience across reloads. Passwords are never
 * accepted into this object. Everything is clearly labelled demo/mock in the UI.
 */

import { useEffect, useState } from 'react';

export type Role = 'health_user' | 'developer_user';

export interface MockSession {
  displayName: string;
  email: string;
  role: Role;
  demoSession: true;
  createdAt: number;
}

const KEY = 'airify_mock_session';

/** Tiny in-tab pub/sub so components re-render on login/logout without a router. */
const listeners = new Set<() => void>();
function emit() { listeners.forEach(l => l()); }

export function getMockSession(): MockSession | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<MockSession>;
    if ((parsed.role === 'health_user' || parsed.role === 'developer_user') && parsed.email) {
      return {
        displayName: parsed.displayName || parsed.email.split('@')[0],
        email: parsed.email,
        role: parsed.role,
        demoSession: true,
        createdAt: parsed.createdAt || Date.now(),
      };
    }
  } catch { /* corrupt/unavailable — treat as logged out */ }
  return null;
}

/** Persist a safe mock session. `password` is intentionally not a parameter. */
export function setMockSession(input: { displayName?: string; email: string; role: Role }): MockSession {
  const session: MockSession = {
    displayName: input.displayName?.trim() || input.email.split('@')[0],
    email: input.email.trim(),
    role: input.role,
    demoSession: true,
    createdAt: Date.now(),
  };
  try { localStorage.setItem(KEY, JSON.stringify(session)); } catch { /* ignore */ }
  emit();
  return session;
}

export function clearMockSession(): void {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
  emit();
}

export function getRole(): Role | null { return getMockSession()?.role ?? null; }
export function isLoggedIn(): boolean { return getMockSession() !== null; }

/** Subscribe a component to session changes (login/logout, cross-tab storage). */
export function useMockSession(): MockSession | null {
  const [session, setSession] = useState<MockSession | null>(getMockSession);
  useEffect(() => {
    const cb = () => setSession(getMockSession());
    listeners.add(cb);
    window.addEventListener('storage', cb);
    return () => { listeners.delete(cb); window.removeEventListener('storage', cb); };
  }, []);
  return session;
}
