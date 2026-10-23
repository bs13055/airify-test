/** Health domain types — shape of the shared Airify demo contract as consumed
 * by the Health surface. Backend response fields only; display values (risk band,
 * score) are derived in shared/utils/risk.ts, not part of the contract. */

export interface Prediction {
  forecast_type: string;
  pm25_estimate: number;
  confidence: string;
  uncertainty: number;
  model_version: string;
  data_status: string;
  method?: string;
  forecast_horizon_seconds?: number | null;
  target_time?: string | null;
  weather_provider_used?: string;
  fallback_reason?: string | null;
}

export interface Criteria {
  criteria_version: string;
  user_group: string;
  daily_intake_limit: number;
  unit: string;
  limit_type: string;
  confidence_level: string;
}

export interface Exposure {
  activity: string;
  duration_minutes: number;
  user_group: string;
  pm25_estimate: number;
  estimated_exposure: number;
  add_estimate: number;
  daily_intake_estimate: number;
  daily_intake_limit: number;
  daily_intake_percent: number;
  exposure_level: string;
  guidance: string[];
  criteria: Criteria;
  safety_note: string;
  assumptions?: {
    inhalation_rate_m3_hr: number;
    body_weight_kg: number;
    resting_inhalation_rate_m3_hr?: number;
    indoor_outdoor_ratio?: number;
    add_formula?: string;
    daily_intake_formula?: string;
  };
}

export interface TimelineDay {
  date: string;
  pm25_avg: number;
  daily_exposure_estimate_ug: number;
}

export interface Timeline {
  timeline: TimelineDay[];
  summary: { avg_pm25: number; total_exposure_estimate_ug: number };
}
