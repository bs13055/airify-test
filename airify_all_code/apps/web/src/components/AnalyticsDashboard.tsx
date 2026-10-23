import { useEffect, useState } from 'react';
import { getEventsSummary } from '../api/client';
import type { EventSummary } from '../api/types';

export function AnalyticsDashboard() {
  const [summary, setSummary] = useState<EventSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { getEventsSummary().then(setSummary).catch(() => setError('Failed to load analytics')); }, []);

  if (error) return <div className="card"><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;
  if (!summary) return <div className="card"><p>Loading analytics...</p></div>;

  return (
    <div>
      <div className="card">
        <h3>Overview</h3>
        <p>Total events: <strong>{summary.total_events}</strong></p>
        <p>Sessions: <strong>{summary.sessions_count}</strong></p>
      </div>
      <div className="card">
        <h3>Events by Type</h3>
        {Object.entries(summary.events_by_type).map(([k, v]) => <p key={k}>{k}: {v}</p>)}
      </div>
      <div className="card">
        <h3>Variant Distribution</h3>
        {Object.entries(summary.variant_counts).map(([k, v]) => <p key={k}>{k}: {v}</p>)}
      </div>
      <div className="card">
        <h3>Feedback</h3>
        {Object.entries(summary.feedback_counts).length > 0
          ? Object.entries(summary.feedback_counts).map(([k, v]) => <p key={k}>{k}: {v}</p>)
          : <p style={{ color: '#888' }}>No feedback yet</p>}
      </div>
      <div className="disclaimer"><p>Local demo analytics only. This demo does not ask for your name, email, or phone number. Please do not enter personal, address, or medical information. PII-like payload keys are stripped before storage, but free-text feedback may still contain whatever a user chooses to type.</p></div>
    </div>
  );
}
