/** Formatting utilities. */

export function riskLabel(level: string): string {
  return level.replace(/_/g, ' ');
}
