import { useHevyCache } from "../stores/hevy_cache";
import { useI18n } from "vue-i18n";

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

/**
 * Format date according to user's preferred format
 * @param dateInput - Date string, Date object, or timestamp
 * @returns Formatted date string based on user preference
**/
export function formatDate(dateInput: string | Date | number): string {
  const store = useHevyCache();
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
  
  if (isNaN(date.getTime())) return String(dateInput);
  
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const year = date.getFullYear();
  
  switch (store.dateFormat) {
    case "eu": // DD.MM.YYYY
      return `${day}.${month}.${year}`;
    case "us": // MM/DD/YYYY
      return `${month}/${day}/${year}`;
    case "uk": // DD/MM/YYYY
      return `${day}/${month}/${year}`;
    case "iso": // YYYY-MM-DD
    default:
      return `${year}-${month}-${day}`;
  }
}

/**
 * Format datetime with time according to user's preferred format
 * ISO/EU formats use 24-hour time (HH:MM) (cutoff seconds for simplicity)
 * US/UK formats use 12-hour time with AM/PM (h:MM AM/PM) (cutoff seconds for simplicity)
 * @param dateInput - Date string, Date object, or timestamp
 * @returns Formatted datetime string (e.g., "21.12.2025, 14:30" or "12/21/2025, 2:30 PM")
**/
export function formatDateTime(dateInput: string | Date | number): string {
  const store = useHevyCache();
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
  
  if (isNaN(date.getTime())) return String(dateInput);
  
  const hours24 = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, "0");
  
  // Use 12-hour format for US/UK, 24-hour for ISO/EU
  const use12Hour = store.dateFormat === "us" || store.dateFormat === "uk";
  
  let timeString: string;
  if (use12Hour) {
    const hours12 = hours24 % 12 || 12; // Convert to 12-hour (0 becomes 12)
    const ampm = hours24 >= 12 ? "PM" : "AM";
    timeString = `${hours12}:${minutes} ${ampm}`;
  } else {
    const hours = hours24.toString().padStart(2, "0");
    timeString = `${hours}:${minutes}`;
  }
  
  return `${formatDate(date)}, ${timeString}`;
}

/**
 * Format date for graph axis (month-year format)
 * Uses user's preferred graph axis format from store if no style is specified
 * @param dateInput - Date string, Date object, or timestamp
 * @param style - Optional override: 'short' for "Dec 2025", 'long' for "December 2025", 'numeric' for "2025-12"
 * @returns Formatted month-year string
**/
export function formatMonthYear(dateInput: string | Date | number, style?: "short" | "long" | "numeric"): string {
  const store = useHevyCache();
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
  
  if (isNaN(date.getTime())) return String(dateInput);
  
  const year = date.getFullYear();
  const month = date.getMonth();
  const monthNum = (month + 1).toString().padStart(2, "0");
  
  // Use provided style or fall back to user's preference
  const formatStyle = style || store.graphAxisFormat;
  
  if (formatStyle === "numeric") {
    return `${year}-${monthNum}`;
  }
  
  // Use i18n for localized month names
  const { t } = useI18n();
  
  const monthKeys = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
  ];
  
  const suffix = formatStyle === "short" ? "Short" : "Long";
  const monthKey = `global.months.${monthKeys[month]}${suffix}`;
  const monthName = t(monthKey);
  
  return `${monthName} ${year}`;
}
