import { useState } from 'react';

export function useSessionId(): string {
  const [id] = useState(() => {
    const stored = localStorage.getItem('airify_session_id');
    if (stored) return stored;
    const newId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
    localStorage.setItem('airify_session_id', newId);
    return newId;
  });
  return id;
}
