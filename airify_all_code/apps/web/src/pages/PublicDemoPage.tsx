import { useSessionId } from '../hooks/useSessionId';
import { useExperimentAssignment } from '../hooks/useExperimentAssignment';
import { useAirifyEstimate } from '../hooks/useAirifyEstimate';
import { LocationInput } from '../components/LocationInput';
import { VariantLayout } from '../components/VariantLayout';
import { FeedbackPanel } from '../components/FeedbackPanel';
import { PrivacyNotice } from '../components/PrivacyNotice';
import { trackEvent } from '../api/client';
import { useEffect } from 'react';

export function PublicDemoPage() {
  const sessionId = useSessionId();
  const assignment = useExperimentAssignment(sessionId);
  const variant = assignment?.variant ?? null;
  const { state, loading, error, fetchEstimate } = useAirifyEstimate(sessionId, variant);

  useEffect(() => {
    if (variant) trackEvent({ session_id: sessionId, variant, event_type: 'page_view', payload: {} });
  }, [variant, sessionId]);

  return (
    <>
      <LocationInput onSubmit={fetchEstimate} loading={loading} />
      {error && <div className="card" style={{ color: 'var(--color-danger)' }}>{error}</div>}
      {state && <VariantLayout state={state} />}
      {state && <FeedbackPanel sessionId={sessionId} variant={variant} />}
      <PrivacyNotice variant={variant} />
    </>
  );
}
