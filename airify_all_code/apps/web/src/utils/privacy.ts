/** Privacy utilities — location rounding. */

export function roundCoord(val: number | null | undefined): number | null {
  if (val === null || val === undefined) return null;
  return Math.round(val * 1000) / 1000;
}
