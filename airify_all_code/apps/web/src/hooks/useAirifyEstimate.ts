import { useState } from 'react';
import { getDemoState, trackEvent } from '../api/client';
import type { DemoState } from '../api/types';
import { roundCoord } from '../utils/privacy';

export function useAirifyEstimate(sessionId: string, variant: string | null) {
  const [state, setState] = useState<DemoState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEstimate = async (lat: number, lon: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDemoState(lat, lon, sessionId);
      setState(data);
      trackEvent({ session_id: sessionId, variant, event_type: 'location_submit', lat_rounded: roundCoord(lat), lon_rounded: roundCoord(lon), payload: {} });
      trackEvent({ session_id: sessionId, variant, event_type: 'estimate_viewed', payload: { risk_level: data.estimate.risk_level, pm25: data.estimate.pm25_ugm3 } });
      trackEvent({ session_id: sessionId, variant, event_type: 'recommendation_viewed', payload: { action: data.recommendation.action } });
      trackEvent({ session_id: sessionId, variant, event_type: 'variant_seen', payload: { variant: data.variant } });
    } catch (e) {
      setError('Failed to fetch estimate. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return { state, loading, error, fetchEstimate };
}
