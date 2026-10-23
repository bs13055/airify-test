/** Shared safety-boundary note — required on both surfaces.
 * See 23_airify_shared_design_system_spec.md §14. Copy must remain materially
 * equivalent to the required boundary; do not soften or remove it.
 */

import type { ReactNode } from 'react';

interface Props {
  /** `core` = required 3-line boundary; `extended` = demo/production + boundary. */
  variant?: 'core' | 'extended';
  /** Extra sentence appended after the boundary (e.g. data/consent posture). */
  children?: ReactNode;
  className?: string;
}

export function SafetyNote({ variant = 'core', children, className }: Props) {
  return (
    <div className={`safety-note${className ? ` ${className}` : ''}`}>
      <strong>Safety.</strong>{' '}
      {variant === 'extended' && 'Demo data only. Not production. Not validated. '}
      Environmental exposure estimate only. Not medical diagnosis. Not clinical decision support.
      {children ? <> {children}</> : null}
    </div>
  );
}
