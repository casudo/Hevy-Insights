/**
 * Exercise Type Detector Utility
 * 
 * Determines if an exercise is strength-based (weight/reps) or cardio/time-based (distance/duration) or if it is a bodyweight exercise.
 * This helps display appropriate metrics and graphs for each exercise type.
 * https://github.com/casudo/Hevy-Insights/issues/26
**/

import { useHevyCache } from "../stores/hevy_cache";

export type ExerciseType = "strength" | "cardio" | "mixed" | "unknown";

export interface ExerciseSet {
  weight_kg?: number | null;
  reps?: number | null;
  distance_km?: number | null;
  duration_seconds?: number | null;
  [key: string]: any;
}

export interface Exercise {
  sets: ExerciseSet[];
  [key: string]: any;
}

/**
 * Detects the type of an exercise based on its sets data.
 * 
 * Logic:
 * - If majority of sets have weight/reps → "strength"
 * - If majority of sets have distance/duration → "cardio"
 * - If both types exist → "mixed"
 * - If neither → "unknown"
 * 
 * @param exercise - Exercise object containing sets
 * @returns ExerciseType - "strength", "cardio", "mixed", or "unknown"
**/
export function detectExerciseType(exercise: Exercise): ExerciseType {
  if (!exercise?.sets || exercise.sets.length === 0) {
    return "unknown";
  }

  let strengthSets = 0;
  let cardioSets = 0;

  for (const set of exercise.sets) {
    const hasWeight = (set.weight_kg !== null && set.weight_kg !== undefined && set.weight_kg > 0);
    const hasReps = (set.reps !== null && set.reps !== undefined && set.reps > 0);
    const hasDistance = (set.distance_km !== null && set.distance_km !== undefined && set.distance_km > 0);
    const hasDuration = (set.duration_seconds !== null && set.duration_seconds !== undefined && set.duration_seconds > 0);

    if (hasWeight || hasReps) {
      strengthSets++;
    }
    if (hasDistance || hasDuration) {
      cardioSets++;
    }
  }

  // Determine type based on majority (>50% of sets)
  const totalClassifiedSets = strengthSets + cardioSets;
  if (totalClassifiedSets === 0) {
    return "unknown";
  }

  const strengthRatio = strengthSets / totalClassifiedSets;
  const cardioRatio = cardioSets / totalClassifiedSets;

  if (strengthRatio > 0.7) {
    return "strength";
  } else if (cardioRatio > 0.7) {
    return "cardio";
  } else if (strengthSets > 0 && cardioSets > 0) { // edge case?
    return "mixed";
  }

  return "unknown";
}

/**
 * Check if an exercise has cardio metrics (distance or duration).
**/
export function hasCardioMetrics(exercise: Exercise): boolean {
  return exercise?.sets?.some(set => 
    (set.distance_km !== null && set.distance_km !== undefined && set.distance_km > 0) ||
    (set.duration_seconds !== null && set.duration_seconds !== undefined && set.duration_seconds > 0)
  ) || false;
}

/**
 * Check if an exercise has strength metrics (weight or reps).
**/
export function hasStrengthMetrics(exercise: Exercise): boolean {
  return exercise?.sets?.some(set => 
    (set.weight_kg !== null && set.weight_kg !== undefined && set.weight_kg > 0) ||
    (set.reps !== null && set.reps !== undefined && set.reps > 0)
  ) || false;
}

/**
 * Format duration from seconds to human-readable format.
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "1h 15m", "45m 30s", "90s")
**/
export function formatDurationSeconds(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return '-';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) { // e.g., 1h 15m
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  } else if (minutes > 0) { // e.g., 45m 30s
    return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
  } else { // only seconds, e.g., 90s
    return `${secs}s`;
  }
}

/**
 * Format distance from kilometers to appropriate unit based on user's weight unit preference.
 * If user prefers lbs, distance is shown in miles; if kg, shown in kilometers.
 * @param km - Distance in kilometers
 * @returns Formatted string with unit (e.g., "5.00 km" or "3.11 mi")
**/
export function formatDistance(km: number | null | undefined): string {
  if (!km || km <= 0) return "-";
  
  const store = useHevyCache();
  
  // If user prefers lbs (imperial), show miles; otherwise show km
  if (store.weightUnit === "lbs") {
    const miles = km * 0.621371;
    return `${miles.toFixed(2)} mi`;
  }
  
  return `${km.toFixed(2)} km`;
}

/**
 * Detects if an exercise is bodyweight-only (reps without weight).
 * 
 * This is needed for Hevy PRO API which doesn't include the "exercise_type" field in the API response.
 * Bodyweight exercises have reps but no weight.
 * 
 * Examples: Pull Up, Chin Up, Dip, Push Up (without "Weighted" in title)
 * 
 * @param exercise - Exercise object containing sets
 * @returns true if exercise is bodyweight-only
**/
export function isBodyweightExercise(exercise: Exercise): boolean {
  if (!exercise?.sets || exercise.sets.length === 0) {
    return false;
  }

  let hasReps = false;
  let hasWeight = false;

  for (const set of exercise.sets) {
    const reps = set.reps ?? 0;
    const weight = (set as any).weight ?? 0;
    
    if (reps > 0) {
      hasReps = true;
    }
    if (weight > 0) {
      hasWeight = true;
    }
  }

  // Bodyweight exercise: has reps but no weight
  return hasReps && !hasWeight;
}
