import { AnalyticsDashboard } from '../components/AnalyticsDashboard';

export function AnalyticsPage() {
  return (
    <>
      <h2 style={{ marginBottom: 16 }}>Local Analytics</h2>
      <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: 16 }}>Local demo analytics only. This demo does not ask for your name, email, or phone number, and PII-like payload keys are stripped before storage. Please do not enter personal information.</p>
      <AnalyticsDashboard />
    </>
  );
}
