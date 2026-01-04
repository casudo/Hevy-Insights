import { useHevyCache } from "../stores/hevy_cache";

/**
 * Convert weight from kg to the user's preferred unit
 * @param weightKg - Weight in kilograms
 * @returns Formatted weight in user's preferred unit
**/
export function formatWeight(weightKg: number): string {
  const store = useHevyCache();
  if (store.weightUnit === 'lbs') {
    const lbs = weightKg * 2.20462;
    return lbs.toFixed(1);
  }
  return weightKg.toFixed(1);
}

/**
 * Get the weight unit label
 * @returns "kg" or "lbs" based on user preference
**/
export function getWeightUnit(): string {
  const store = useHevyCache();
  return store.weightUnit;
}

/**
 * Get the distance unit label based on weight unit preference
 * @returns "km" or "mi" based on user preference (lbs → mi, kg → km)
**/
export function getDistanceUnit(): string {
  const store = useHevyCache();
  return store.weightUnit === "lbs" ? "mi" : "km";
}

/**
 * Format duration from minutes to "Xh Ym" format
 * @param minutes - Duration in minutes
 * @returns Formatted duration string (e.g., "1h 15m" or "45m")
**/
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  
  if (hours > 0) {
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }
  return `${mins}m`;
}

/**
 * Format duration from timestamps (in seconds) to "Xh Ym" format
 * @param startTime - Start timestamp in seconds
 * @param endTime - End timestamp in seconds
 * @returns Formatted duration string (e.g., "1h 15m")
**/
export function formatDurationFromTimestamps(startTime: number, endTime: number): string {
  const durationMinutes = Math.floor((endTime - startTime) / 60);
  return formatDuration(durationMinutes);
}

/**
 * Format PR value based on its type. Weight-based PRs are converted to user's preferred unit.
 * @param type - The type of PR (e.g., "Max Weight", "1RM", "Total Volume", "Best Time")
 * @param value - The PR value (can be number or string)
 * @returns Formatted PR value with unit as string
**/
export function formatPRValue(type: string, value: number | string): string {
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return String(value);
  
  // Check if this is a weight-based PR
  const weightTypes = ["weight", "max", "1rm", "volume"];
  if (weightTypes.some(t => type.toLowerCase().includes(t))) {
    return `${formatWeight(numValue)} ${getWeightUnit()}`;
  }
  
  return String(value);
}
