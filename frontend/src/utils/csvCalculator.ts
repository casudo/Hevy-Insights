/**
 * CSV Calculator Utility
 * 
 * Logic Overview:
 * 1. Aggregation: Sums up volume, reps, and sets across all workouts.
 * 2. Categorization: Maps exercise titles to muscle groups (Strict matching).
 * 3. Progression (PRs): Tracks 3 metrics: Estimated 1RM, Max Weight, and Max Reps.
 * 4. Ranking: Sorts exercises by total workload (volume).
**/

export interface Workout {
  id: string;
  title: string;
  start_time: number;
  end_time: number | null;
  description: string | null;
  exercises: Exercise[];
  [key: string]: any;
}

export interface Exercise {
  id: string;
  title: string;
  sets: Set[];
  [key: string]: any;
}

export interface Set {
  id: string;
  index: number;
  set_type: string | null;
  weight_kg: number | null;
  reps: number | null;
  distance_km: number | null;
  duration_seconds: number | null;
  rpe: number | null;
  [key: string]: any;
}

export interface CSVStats {
  totalVolume: number;
  avgVolumePerWorkout: number;
  totalWorkouts: number;
  totalSets: number;
  totalReps: number;
  muscleDistribution: Record<string, number>;
  prsOverTime: Array<{ date: string; count: number }>;
  topExercises: Array<{ name: string; volume: number; sets: number }>;
}

// --- CALCULATION FUNCTIONS ---

/**
 * Calculates total volume (weight * reps) across all workouts.
**/
export function calculateTotalVolume(workouts: Workout[]): number {
  return Math.round(
    workouts.reduce((acc, workout) => 
      acc + workout.exercises.reduce((exAcc, ex) => 
        exAcc + ex.sets.reduce((setAcc, set) => 
          setAcc + ((set.weight_kg || 0) * (set.reps || 0)), 0
        ), 0
      ), 0
    )
  );
}

/**
 * Calculates average volume per workout session.
**/
export function calculateAvgVolume(workouts: Workout[]): number {
  if (workouts.length === 0) return 0;
  return Math.round(calculateTotalVolume(workouts) / workouts.length);
}

/**
 * Maps exercises to muscle groups based strictly on exercise titles.
 * If no match is found, the exercise is skipped.
**/
export function calculateMuscleDistribution(workouts: Workout[]): Record<string, number> {
  const muscleGroups: Record<string, number> = {
    chest: 0, back: 0, shoulders: 0, biceps: 0, triceps: 0, legs: 0, core: 0,
  };

  const exerciseToMuscle: Record<string, string[]> = {
    // TODO: Support for other languages (overkill?)
    // Chest
    "bench press": ["chest"], "incline bench": ["chest"], "decline bench": ["chest"], 
    "chest press": ["chest"], "chest fly": ["chest"], "pec deck": ["chest"],
    "push up": ["chest", "triceps"], "dips": ["chest", "triceps"],
    // Back
    "deadlift": ["back", "legs"], "pull up": ["back", "biceps"], "chin up": ["back", "biceps"], 
    "lat pulldown": ["back"], "seated row": ["back"], "cable row": ["back"], 
    "bent over row": ["back"], "barbell row": ["back"], "t-bar row": ["back"],
    // Shoulders
    "shoulder press": ["shoulders"], "overhead press": ["shoulders"], "military press": ["shoulders"], 
    "lateral raise": ["shoulders"], "front raise": ["shoulders"], "rear delt": ["shoulders"], 
    "shrug": ["shoulders"],
    // Arms
    "bicep curl": ["biceps"], "biceps curl": ["biceps"], "hammer curl": ["biceps"], 
    "preacher curl": ["biceps"], "reverse curl": ["biceps"],
    "tricep extension": ["triceps"], "triceps extension": ["triceps"], "tricep pushdown": ["triceps"], 
    "triceps pushdown": ["triceps"], "skull crusher": ["triceps"], "overhead extension": ["triceps"],
    // Legs
    "squat": ["legs"], "leg press": ["legs"], "leg extension": ["legs"], "leg curl": ["legs"], 
    "lunge": ["legs"], "calf raise": ["legs"], "romanian deadlift": ["legs", "back"],
    // Core
    "plank": ["core"], "crunch": ["core"], "sit up": ["core"], "ab wheel": ["core"], 
    "russian twist": ["core"], "hanging leg raise": ["core"],
  };

  for (const workout of workouts) {
    for (const exercise of workout.exercises) {
      const name = exercise.title.toLowerCase();
      const setCount = exercise.sets.length;

      for (const [pattern, muscles] of Object.entries(exerciseToMuscle)) {
        if (name.includes(pattern)) {
          muscles.forEach(m => {
            if (muscleGroups[m] !== undefined) muscleGroups[m] += setCount;
          });
          break;
        }
      }
    }
  }
  return muscleGroups;
}

/**
 * Calculates PRs over time using 3 metrics: 1RM, Best Reps, and Highest Weight.
 * Logic matches Dashboard.vue for cross-app consistency.
**/
export function calculatePRsOverTime(workouts: Workout[]): Array<{ date: string; count: number }> {
  const exercisePRs = new Map<string, { max1RM: number; maxWeight: number; maxReps: number }>();
  const prsByDate = new Map<string, number>();

  // Sort chronologically (oldest first) to track PR progression
  const sorted = [...workouts].sort((a, b) => a.start_time - b.start_time);

  for (const workout of sorted) {
    const date = new Date(workout.start_time * 1000).toISOString().split("T")[0];
    let prsInWorkout = 0;

    for (const exercise of workout.exercises) {
      const exerciseKey = exercise.title.toLowerCase();
      
      if (!exercisePRs.has(exerciseKey)) {
        exercisePRs.set(exerciseKey, { max1RM: 0, maxWeight: 0, maxReps: 0 });
      }
      
      const currentPRs = exercisePRs.get(exerciseKey)!;

      for (const set of exercise.sets) {
        let prCount = 0;
        const weight = set.weight_kg || 0;
        const reps = set.reps || 0;

        if (weight > 0 && reps > 0) {
          // 1. Estimated 1RM (Epley: weight * (1 + reps/30))
          const estimated1RM = weight * (1 + reps / 30);
          if (estimated1RM > currentPRs.max1RM) {
            currentPRs.max1RM = estimated1RM;
            prCount++;
          }
          // 2. Highest Weight
          if (weight > currentPRs.maxWeight) {
            currentPRs.maxWeight = weight;
            prCount++;
          }
          // 3. Best Reps (at any weight)
          if (reps > currentPRs.maxReps) {
            currentPRs.maxReps = reps;
            prCount++;
          }
        } else if (reps > 0 && weight === 0) {
          // Bodyweight PR tracking
          if (reps > currentPRs.maxReps) {
            currentPRs.maxReps = reps;
            prCount++;
          }
        }
        prsInWorkout += prCount;
      }
    }

    // Check that "date" is a valid string before using it as a Map key
    if (date && prsInWorkout > 0) {
      prsByDate.set(date, (prsByDate.get(date) || 0) + prsInWorkout);
    }
  }

  return Array.from(prsByDate.entries())
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/**
 * Calculate PRs with time grouping (weekly or monthly).
 * Used by Dashboard for filtered/aggregated PR charts.
**/
export function calculatePRsGrouped(
  workouts: Workout[], 
  groupBy: "week" | "month"
): Record<string, number> {
  const exercisePRs = new Map<string, { max1RM: number; maxWeight: number; maxReps: number }>();
  const prsByPeriod: Record<string, number> = {};

  // Helper to get start of week (Monday)
  const startOfWeek = (d: Date) => {
    const dd = new Date(d);
    const day = dd.getDay(); // 0=Sun
    const offsetToMonday = day === 0 ? -6 : 1 - day;
    dd.setDate(dd.getDate() + offsetToMonday);
    dd.setHours(0, 0, 0, 0);
    return dd;
  };

  // Sort chronologically (oldest first)
  const sorted = [...workouts].sort((a, b) => a.start_time - b.start_time);

  for (const workout of sorted) {
    const date = new Date(workout.start_time * 1000);
    const periodKey = groupBy === "week" 
      ? startOfWeek(date).toISOString().slice(0, 10) // Week start date (Monday)
      : date.toISOString().slice(0, 7);  // YYYY-MM for month
    
    let prsInWorkout = 0;

    for (const exercise of workout.exercises) {
      const exerciseKey = exercise.title.toLowerCase();
      
      if (!exercisePRs.has(exerciseKey)) {
        exercisePRs.set(exerciseKey, { max1RM: 0, maxWeight: 0, maxReps: 0 });
      }
      
      const currentPRs = exercisePRs.get(exerciseKey)!;

      for (const set of exercise.sets) {
        const weight = set.weight_kg || 0;
        const reps = set.reps || 0;
        let prCount = 0;

        if (weight > 0 && reps > 0) {
          const estimated1RM = weight * (1 + reps / 30);
          if (estimated1RM > currentPRs.max1RM) {
            currentPRs.max1RM = estimated1RM;
            prCount++;
          }
          if (weight > currentPRs.maxWeight) {
            currentPRs.maxWeight = weight;
            prCount++;
          }
          if (reps > currentPRs.maxReps) {
            currentPRs.maxReps = reps;
            prCount++;
          }
        } else if (reps > 0 && weight === 0) {
          if (reps > currentPRs.maxReps) {
            currentPRs.maxReps = reps;
            prCount++;
          }
        }
        prsInWorkout += prCount;
      }
    }

    if (prsInWorkout > 0) {
      prsByPeriod[periodKey] = (prsByPeriod[periodKey] || 0) + prsInWorkout;
    }
  }

  return prsByPeriod;
}

/**
 * Calculate top exercises by total volume moved.
**/
export function calculateTopExercises(workouts: Workout[], limit = 10): Array<{ name: string; volume: number; sets: number }> {
  const stats = new Map<string, { volume: number; sets: number }>();

  for (const workout of workouts) {
    for (const exercise of workout.exercises) {
      const volume = exercise.sets.reduce((sum, s) => sum + ((s.weight_kg || 0) * (s.reps || 0)), 0);
      const current = stats.get(exercise.title) || { volume: 0, sets: 0 };
      
      stats.set(exercise.title, {
        volume: current.volume + volume,
        sets: current.sets + exercise.sets.length,
      });
    }
  }

  return Array.from(stats.entries())
    .map(([name, data]) => ({ name, ...data }))
    .sort((a, b) => b.volume - a.volume)
    .slice(0, limit);
}

/**
 * Main function: Returns a comprehensive statistics object for the dashboard.
**/
export function calculateCSVStats(workouts: Workout[]): CSVStats {
  const totalSets = workouts.reduce((sum, w) => sum + w.exercises.reduce((s, e) => s + e.sets.length, 0), 0);
  const totalReps = workouts.reduce((sum, w) => sum + w.exercises.reduce((s, e) => s + e.sets.reduce((r, set) => r + (set.reps || 0), 0), 0), 0);

  return {
    totalVolume: calculateTotalVolume(workouts),
    avgVolumePerWorkout: calculateAvgVolume(workouts),
    totalWorkouts: workouts.length,
    totalSets,
    totalReps,
    muscleDistribution: calculateMuscleDistribution(workouts),
    prsOverTime: calculatePRsOverTime(workouts),
    topExercises: calculateTopExercises(workouts),
  };
}
