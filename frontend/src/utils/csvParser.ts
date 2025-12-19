/**
 * CSV Parser for Hevy workout data
 * 
 * Expected CSV format:
 * title; start_time; end_time; description; exercise_title; superset_id; 
 * exercise_notes; set_index; set_type; weight_kg; reps; distance_km; 
 * duration_seconds; rpe
 * 
 * TODO: "weight_lbs" will currently throw an error. Add support for both units.
**/

export interface CSVRow {
  title: string;
  start_time: string;
  end_time: string;
  description: string;
  exercise_title: string;
  superset_id: string;
  exercise_notes: string;
  set_index: string;
  set_type: string;
  weight_kg: string;
  reps: string;
  distance_km: string;
  duration_seconds: string;
  rpe: string;
}

export interface ParsedWorkout {
  id: string;
  title: string;
  start_time: number;
  end_time: number | null;
  description: string | null;
  exercises: ParsedExercise[];
  estimated_volume_kg?: number;
}

export interface ParsedExercise {
  id: string;
  title: string;
  superset_id: string | null;
  notes: string | null;
  sets: ParsedSet[];
  exercise?: {
    url: string | null;
  };
}

export interface ParsedSet {
  id: string;
  index: number;
  set_type: string | null;
  weight_kg: number | null;
  reps: number | null;
  distance_km: number | null;
  duration_seconds: number | null;
  rpe: number | null;
}

/**
 * Main parser function to transform raw CSV text into a structured Workout array.
**/
export function parseCSV(csvContent: string): ParsedWorkout[] {
  // Parse lines
  const lines = csvContent.trim().split("\n");
  if (lines.length === 0) throw new Error("CSV file is empty");

  // Parse header
  const headerLine = lines[0];
  if (!headerLine) throw new Error("CSV header is missing");
  const headers = parseCSVLine(headerLine);

  const workoutsMap = new Map<string, ParsedWorkout>();

  // Process data rows starting from index 1 (skipping header)
  for (let i = 1; i < lines.length; i++) {
    const lineData = lines[i]?.trim();
    if (!lineData) continue;

    const values = parseCSVLine(lineData);
    if (values.length !== headers.length) continue;

    // Map headers to values for the current row
    const row: any = {};
    headers.forEach((header, index) => {
      row[header] = values[index];
    });

    const workoutKey = `${row.title}_${row.start_time}`;

    // 1. Get or Create Workout
    if (!workoutsMap.has(workoutKey)) {
      workoutsMap.set(workoutKey, {
        id: `csv_${workoutKey}_${Date.now()}`,
        title: row.title || "Unnamed Workout",
        start_time: parseDate(row.start_time),
        end_time: row.end_time ? parseDate(row.end_time) : null,
        description: cleanString(row.description),
        exercises: [],
        estimated_volume_kg: 0
      });
    }
    const workout = workoutsMap.get(workoutKey)!;

    // 2. Get or Create Exercise within that Workout
    let exercise = workout.exercises.find(ex => ex.title === row.exercise_title);
    if (!exercise) {
      exercise = {
        id: `${workout.id}_ex_${workout.exercises.length}_${row.exercise_title}`,
        title: row.exercise_title || "Unknown Exercise",
        superset_id: cleanString(row.superset_id),
        notes: cleanString(row.exercise_notes),
        sets: [],
        exercise: { url: null }
      };
      workout.exercises.push(exercise);
    }

    // 3. Create the Set
    const weight = row.weight_kg ? parseFloat(row.weight_kg) : null;
    const reps = row.reps ? parseInt(row.reps) : null;
    
    const set: ParsedSet = {
      id: `csv_set_${row.set_index}_${Date.now()}_${i}`,
      index: parseInt(row.set_index) || 0,
      set_type: row.set_type || null,
      weight_kg: weight,
      reps: reps,
      distance_km: row.distance_km ? parseFloat(row.distance_km) : null,
      duration_seconds: row.duration_seconds ? parseInt(row.duration_seconds) : null,
      rpe: row.rpe ? parseFloat(row.rpe) : null
    };

    exercise.sets.push(set);
    
    // Update total volume
    if (weight && reps) {
      workout.estimated_volume_kg = (workout.estimated_volume_kg || 0) + (weight * reps);
    }
  }

  // Final sort: Newest workouts first
  return Array.from(workoutsMap.values()).sort((a, b) => b.start_time - a.start_time);
}

/**
 * Splits a CSV line into an array of strings, respecting double quotes.
**/
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];
    
    if (char === '"' && nextChar === '"') {
      current += '"';
      i++; 
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

/**
 * Converts date strings to Unix timestamps, handling German month names.
**/
function parseDate(dateString: string): number {
  try {
    // Handle German month names: "16 Dez 2025, 15:06"
    const germanMonths: Record<string, string> = {
      "Jan": "Jan", "Feb": "Feb", "Mär": "Mar", "Mar": "Mar", "Apr": "Apr",
      "Mai": "May", "Jun": "Jun", "Jul": "Jul", "Aug": "Aug",
      "Sep": "Sep", "Okt": "Oct", "Nov": "Nov", "Dez": "Dec"
    };
    
    // TODO: Add handler for Spanish, French, etc. month names if needed

    let normalizedDate = dateString;
    
    // Replace German month abbreviations with English
    for (const [german, english] of Object.entries(germanMonths)) {
      if (dateString.includes(german)) {
        normalizedDate = dateString.replace(german, english);
        break;
      }
    }
    
    const date = new Date(normalizedDate);
    return isNaN(date.getTime()) 
      ? Math.floor(Date.now() / 1000) 
      : Math.floor(date.getTime() / 1000);
  } catch {
    return Math.floor(Date.now() / 1000);
  }
}

/**
 * Cleans string values by removing empty quotes or whitespace.
**/
function cleanString(val: string | undefined): string | null {
  if (!val) return null;
  const trimmed = val.trim();
  // Check if string is just an empty quote or purely empty
  return (trimmed === "" || trimmed === '"') ? null : trimmed;
}

// --- FILE UTILITIES ---

export async function validateCSVFile(file: File): Promise<boolean> {
  if (!file.name.toLowerCase().endsWith(".csv")) throw new Error("File must be a CSV file");
  if (file.size > 10 * 1024 * 1024) throw new Error("File size must be less than 10MB");
  
  // Check if CSV contains weight_kg (not weight_lbs)
  const content = await readCSVFile(file);
  const firstLine = content.split("\n")[0]?.toLowerCase() || "";
  
  if (firstLine.includes("weight_lbs")) {
    throw new Error("CSV must use 'weight_kg' not 'weight_lbs'. Please export with metric units.");
  }
  
  if (!firstLine.includes("weight_kg")) {
    throw new Error("CSV must contain 'weight_kg' column.");
  } // Unlikely that this would ever fail, but just in case
  
  return true;
}

export function readCSVFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsText(file);
  });
}
