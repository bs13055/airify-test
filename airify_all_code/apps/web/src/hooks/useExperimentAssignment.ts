import { useEffect, useState } from 'react';
import { getAssignment } from '../api/client';
import type { ExperimentAssignment } from '../api/types';

export function useExperimentAssignment(sessionId: string) {
  const [assignment, setAssignment] = useState<ExperimentAssignment | null>(null);

  useEffect(() => {
    getAssignment(sessionId).then(setAssignment).catch(() => {
      setAssignment({ experiment_name: 'airify_public_mvp_v1', session_id: sessionId, variant: 'risk_first', note: 'fallback' });
    });
  }, [sessionId]);

  return assignment;
}
