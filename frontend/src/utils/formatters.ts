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
