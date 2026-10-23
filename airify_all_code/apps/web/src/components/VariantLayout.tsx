import type { DemoState } from '../api/types';
import { RiskCard } from './RiskCard';
import { ActionCard } from './ActionCard';
import { MedicalDisclaimer } from './MedicalDisclaimer';

export function VariantLayout({ state }: { state: DemoState }) {
  const { estimate, recommendation, variant } = state;

  if (variant === 'action_first') {
    return (
      <div className="card">
        <ActionCard rec={recommendation} />
        <RiskCard est={estimate} />
        <MedicalDisclaimer />
      </div>
    );
  }
  // risk_first (default)
  return (
    <div className="card">
      <RiskCard est={estimate} />
      <ActionCard rec={recommendation} />
      <MedicalDisclaimer />
    </div>
  );
}
