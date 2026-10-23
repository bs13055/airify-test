import type { PlatformEstimate } from '../api/types';
import { riskLabel } from '../utils/formatting';

export function RiskCard({ est }: { est: PlatformEstimate }) {
  return (
    <div style={{ padding: 16, borderRadius: 10, background: '#f8f9fa', marginBottom: 12 }}>
      <h3 style={{ marginBottom: 8 }}>PM2.5 Risk Level</h3>
      <span className={`badge badge-${est.risk_level}`}>{riskLabel(est.risk_level)}</span>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, margin: '8px 0' }}>{est.pm25_ugm3} µg/m³</div>
      <div style={{ fontSize: '0.8rem', color: '#888' }}>Confidence: {est.confidence} | Data: {est.data_status}</div>
      <p style={{ fontSize: '0.85rem', color: '#666', marginTop: 8 }}>{est.explanation}</p>
    </div>
  );
}
