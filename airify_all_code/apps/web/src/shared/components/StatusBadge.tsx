/** Shared status badge — semantically honest demo/mock/planned/live states.
 * See 23_airify_shared_design_system_spec.md §10. Never render a mock, planned,
 * or `validated: false` state in a success/green style.
 */

export type Status = 'demo' | 'mock' | 'planned' | 'live';

const CLASS: Record<Status, string> = {
  demo: 'status-demo',
  mock: 'status-mock',
  planned: 'status-planned',
  live: 'status-live',
};

interface Props {
  status: Status;
  /** Optional label override; defaults to the status word. */
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: Props) {
  return (
    <span className={`status-badge ${CLASS[status]}${className ? ` ${className}` : ''}`}>
      {label ?? status}
    </span>
  );
}
