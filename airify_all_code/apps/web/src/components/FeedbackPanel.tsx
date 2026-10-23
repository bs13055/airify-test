import { useState } from 'react';
import { useFeedback } from '../hooks/useFeedback';

interface Props { sessionId: string; variant: string | null; }

export function FeedbackPanel({ sessionId, variant }: Props) {
  const { selectedType, submitted, clickFeedback, submitFeedback } = useFeedback(sessionId, variant);
  const [text, setText] = useState('');

  if (submitted) return <div className="card" style={{ textAlign: 'center', color: 'var(--color-success)' }}>Thank you for your feedback!</div>;

  return (
    <div className="card">
      <h3 style={{ marginBottom: 12 }}>Was this helpful?</h3>
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        {(['useful', 'not_useful', 'confusing'] as const).map(type => (
          <button key={type} className={`btn btn-secondary`} onClick={() => clickFeedback(type)}
            style={{ flex: 1, minWidth: 100, border: selectedType === type ? '2px solid var(--color-primary)' : undefined, background: selectedType === type ? '#e3f2fd' : undefined }}>
            {type === 'useful' ? '👍 Useful' : type === 'not_useful' ? '👎 Not Useful' : '🤔 Confusing'}
          </button>
        ))}
      </div>
      <label style={{ fontSize: '0.85rem', color: '#666' }} htmlFor="fb-text">Optional: tell us more</label>
      <p style={{ fontSize: '0.75rem', color: '#999', marginTop: 2, marginBottom: 6 }}>
        ⚠️ Do not include your name, phone number, email, address, or medical information.
      </p>
      <textarea id="fb-text" className="input-field" rows={3} maxLength={500} placeholder="What did you think?" value={text} onChange={e => setText(e.target.value)} style={{ marginTop: 4, marginBottom: 10, resize: 'vertical' }} />
      <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => submitFeedback(text)}>Submit Feedback</button>
    </div>
  );
}
