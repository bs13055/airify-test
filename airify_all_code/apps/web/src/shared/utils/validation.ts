/** Input validation (shared). */

export function isValidLat(v: number): boolean {
  return !isNaN(v) && v >= -90 && v <= 90;
}

export function isValidLon(v: number): boolean {
  return !isNaN(v) && v >= -180 && v <= 180;
}
