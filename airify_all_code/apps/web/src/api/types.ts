/** API response types for Airify backend. */

export interface ExperimentAssignment {
  experiment_name: string;
  session_id: string;
  variant: 'risk_first' | 'action_first';
  note: string;
}

export interface PlatformEstimate {
  point: { lat: number; lon: number };
  pm25_ugm3: number;
  risk_level: 'low' | 'moderate' | 'unhealthy_sensitive' | 'unhealthy';
  confidence: string;
  method: string;
  data_status: string;
  aqi_display: number | null;
  explanation: string;
  note: string;
}

export interface PlatformRecommendation {
  risk_level: string;
  action: string;
  explanation: string;
  disclaimer: string;
  data_status: string;
}

export interface DemoState {
  estimate: PlatformEstimate;
  recommendation: PlatformRecommendation;
  variant: string;
  session_id: string;
  data_status: string;
}

export interface EventSummary {
  total_events: number;
  events_by_type: Record<string, number>;
  sessions_count: number;
  variant_counts: Record<string, number>;
  feedback_counts: Record<string, number>;
  latest_events_sample: EventRecord[];
}

export interface EventRecord {
  event_id: string;
  timestamp: string;
  session_id: string;
  variant: string | null;
  event_type: string;
  lat_rounded: number | null;
  lon_rounded: number | null;
  payload: Record<string, unknown> | null;
}
