import type { PlatformRecommendation } from '../api/types';

export function ActionCard({ rec }: { rec: PlatformRecommendation }) {
  return (
    <div style={{ padding: 16, borderRadius: 10, background: '#e8f5e9', marginBottom: 12 }}>
      <h3 style={{ marginBottom: 8 }}>Recommended Action</h3>
      <p style={{ fontWeight: 500, marginBottom: 8 }}>{rec.action}</p>
      <p style={{ fontSize: '0.85rem', color: '#555' }}>{rec.explanation}</p>
    </div>
  );
}
