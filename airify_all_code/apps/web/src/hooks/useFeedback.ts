import { useState } from 'react';
import { trackEvent } from '../api/client';

export function useFeedback(sessionId: string, variant: string | null) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const clickFeedback = (type: string) => {
    setSelectedType(type);
    trackEvent({ session_id: sessionId, variant, event_type: 'feedback_click', payload: { feedback_type: type } });
  };

  const submitFeedback = (text: string) => {
    trackEvent({ session_id: sessionId, variant, event_type: 'feedback_submit', payload: { feedback_type: selectedType || 'text_only', text: text.slice(0, 500) } });
    setSubmitted(true);
  };

  return { selectedType, submitted, clickFeedback, submitFeedback };
}
