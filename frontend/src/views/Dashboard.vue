<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useHevyCache } from "../stores/hevy_cache";
import { calculateCSVStats, calculatePRsGrouped, calculateMuscleDistribution } from "../utils/csvCalculator";
import { formatDuration, formatWeight, getWeightUnit, formatPRValue } from "../utils/formatters";
import { Line, Doughnut, Radar, Bar } from "vue-chartjs";
import { useI18n } from "vue-i18n";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

const { t } = useI18n();
const store = useHevyCache();
const router = useRouter();
const chartData = ref<any>(null);

const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);
const userAccount = computed(() => store.userAccount);
const workouts = computed(() => store.workouts);

// Collapsible sections state (saved to localStorage)
const expandedSections = ref<Record<string, boolean>>({
  plateaus: true, // Plateaus expanded by default
  prs: true, // PRs expanded by default
  trainingAnalytics: JSON.parse(localStorage.getItem("dashboard-section-trainingAnalytics") || "true"),
  exerciseInsights: JSON.parse(localStorage.getItem("dashboard-section-exerciseInsights") || "true"),
  calendarViews: JSON.parse(localStorage.getItem("dashboard-section-calendarViews") || "true"),
  muscleDistribution: JSON.parse(localStorage.getItem("dashboard-section-muscleDistribution") || "true"),
});

// Toggle section and save to localStorage
function toggleSection(section: string) {
  expandedSections.value[section] = !expandedSections.value[section];
  localStorage.setItem(`dashboard-section-${section}`, JSON.stringify(expandedSections.value[section]));
}

// CSV mode stats calculation
const csvStats = computed(() => {
  if (store.isCSVMode && workouts.value.length > 0) {
    return calculateCSVStats(workouts.value as any);
  }
  return null;
});

// Get theme colors from CSS variables
const primaryColor = computed(() => {
  return getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim() || "#10b981";
});
const secondaryColor = computed(() => {
  return getComputedStyle(document.documentElement).getPropertyValue("--color-secondary").trim() || "#06b6d4";
});

// ---------- Individual Chart Range Filters ----------
type Range = "1m" | "3m" | "6m" | "1y" | "all";
type DisplayStyle = "mo" | "wk";

const hoursTrained_Range = ref<Range>("6m");
const hoursTrained_Display = ref<DisplayStyle>("mo");

const volumeProgression_Range = ref<Range>("6m");
const volumeProgression_Display = ref<DisplayStyle>("mo");

const repsAndSets_Range = ref<Range>("6m");
const repsAndSets_Display = ref<DisplayStyle>("mo");

const prsOverTime_Range = ref<Range>("6m");
const prsOverTime_Display = ref<DisplayStyle>("mo");

const muscleDistribution_Range = ref<Range>("all");
const muscleDistribution_Grouping = ref<"groups" | "muscles">("groups");
  
// ---------- Helper functions for date keys ----------

const startOfWeek = (d: Date) => {
  const dd = new Date(d);
  const day = dd.getDay(); // 0=Sun
  const offsetToMonday = day === 0 ? -6 : 1 - day;
  dd.setDate(dd.getDate() + offsetToMonday);
  dd.setHours(0,0,0,0);
  return dd;
};
const weekKey = (d: Date) => {
  const m = startOfWeek(d);
  return m.toISOString().slice(0,10);
};
const monthKey = (d: Date) => {
  return d.toISOString().slice(0,7); // "YYYY-MM"
};

// Map individual muscles to larger groups
function groupMuscles(muscleGroup: string): string {
  const muscle = muscleGroup.toLowerCase();
  
  // Arms
  if (muscle.includes("bicep") || muscle.includes("tricep") || muscle.includes("forearm")) {
    return "Arms";
  }
  
  // Back
  if (muscle.includes("back") || muscle.includes("lat") || muscle.includes("rhomboid") || muscle.includes("trap")) {
    return "Back";
  }
  
  // Chest
  if (muscle.includes("chest") || muscle.includes("pec")) {
    return "Chest";
  }
  
  // Core
  if (muscle.includes("abdominal") || muscle.includes("core") || muscle.includes("oblique")) {
    return "Core";
  }
  
  // Legs
  if (muscle.includes("quad") || muscle.includes("hamstring") || muscle.includes("glute") || 
      muscle.includes("calves") || muscle.includes("leg") || muscle.includes("adductor") || muscle.includes("abductor")) {
    return "Legs";
  }
  
  // Shoulders
  if (muscle.includes("shoulder") || muscle.includes("delt")) {
    return "Shoulders";
  }
  
  // Default: return original
  return muscleGroup;
}

// Localize muscle name
function getLocalizedMuscleName(muscleName: string): string {
  const key = muscleName.toLowerCase().replace(/\s+/g, "");
  // Check if we have a direct translation
  const translationKey = `global.bodymuscles.${key}`;
  const translated = t(translationKey);
  // If translation exists and is different from the key, use it
  return translated !== translationKey ? translated : muscleName;
}

// Localize PR type name
function getLocalizedPRType(prType: string): string {
  const key = `dashboard.prTypes.${prType}`;
  const translation = t(key);
  if (translation === key) return prType.split("_").join(" ");
  return translation;
}

// Get localized range filter label
function getRangeLabel(range: Range): string {
  if (range === "all") return t("dashboard.filters.all");
  if (range === "1y") return t("dashboard.filters.oneYear");
  if (range === "6m") return t("dashboard.filters.sixMonths");
  if (range === "3m") return t("dashboard.filters.threeMonths");
  if (range === "1m") return t("dashboard.filters.oneMonth");
  return range;
}

// Get localized display style label
function getDisplayLabel(display: DisplayStyle): string {
  if (display === "mo") return t("dashboard.filters.monthly");
  if (display === "wk") return t("dashboard.filters.weekly");
  return display;
}


// Get calendar week number (ISO 8601)
const getWeekNumber = (d: Date): number => {
  const date = new Date(d.getTime());
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() + 4 - (date.getDay() || 7));
  const yearStart = new Date(date.getFullYear(), 0, 1);
  const weekNo = Math.ceil((((date.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return weekNo;
};

// Format period label based on display style
const formatPeriodLabel = (period: string, displayStyle: DisplayStyle): string => {
  if (displayStyle === "wk") {
    const date = new Date(period);
    const weekNum = getWeekNumber(date);
    return `${t("dashboard.charts.calendarWeek")} ${weekNum}`;
  }
  return period; // Monthly: keep as "YYYY-MM"
};

// Helper to filter by range
const filterByRange = (range: Range) => {
  const now = new Date();
  let daysBack = 180; // default ~6 months
  if (range === "1m") daysBack = 30;
  else if (range === "3m") daysBack = 90;
  else if (range === "6m") daysBack = 180;
  else if (range === "1y") daysBack = 365;
  else if (range === "all") daysBack = 365 * 10; // 10 years
  const start = new Date(now);
  start.setDate(start.getDate() - daysBack);
  const cutoff = Math.floor(start.getTime() / 1000);
  return workouts.value.filter((w: any) => (w.start_time || 0) >= cutoff);
};

// Aggregate by period
const aggregateByPeriod = (_range: Range, displayStyle: DisplayStyle, filteredWorkouts: any[]) => {
  const map: Record<string, {
    durationMin: number;
    volumeKg: number;
    reps: number;
    sets: number;
    workouts: number;
  }> = {};
  
  // Use display style preference
  const useWeeks = displayStyle === "wk";
  
  for (const w of filteredWorkouts) {
    const d = new Date((w.start_time || 0) * 1000);
    const key = useWeeks ? weekKey(d) : monthKey(d);
    const entry = (map[key] ||= { durationMin: 0, volumeKg: 0, reps: 0, sets: 0, workouts: 0 });
    entry.workouts += 1;
    entry.volumeKg += w.estimated_volume_kg || 0;
    const dur = Math.max(0, Math.floor(((w.end_time || w.start_time || 0) - (w.start_time || 0)) / 60));
    entry.durationMin += dur;
    for (const ex of (w.exercises || [])) {
      for (const s of (ex.sets || [])) {
        entry.sets += 1;
        entry.reps += s.reps || 0;
      }
    }
  }
  const keys = Object.keys(map).sort();
  return keys.map(k => ({ period: k, ...map[k] }));
};

// Hours trained per week/month
const hoursTrained_Data = computed(() => {
  const filtered = filterByRange(hoursTrained_Range.value);
  const agg = aggregateByPeriod(hoursTrained_Range.value, hoursTrained_Display.value, filtered);
  return {
    labels: agg.map(w => formatPeriodLabel(w.period, hoursTrained_Display.value)),
    data: agg.map(w => Number(((w.durationMin ?? 0) / 60).toFixed(2)))
  };
});

// Volume per week/month
const volumeProgression_Data = computed(() => {
  const filtered = filterByRange(volumeProgression_Range.value);
  const agg = aggregateByPeriod(volumeProgression_Range.value, volumeProgression_Display.value, filtered);
  return {
    labels: agg.map(w => formatPeriodLabel(w.period, volumeProgression_Display.value)),
    data: agg.map(w => {
      const kg = w.volumeKg ?? 0;
      return Math.round(store.weightUnit === "lbs" ? kg * 2.20462 : kg);
    })
  };
});

// Reps/Sets per week/month
const repsAndSets_Data = computed(() => {
  const filtered = filterByRange(repsAndSets_Range.value);
  const agg = aggregateByPeriod(repsAndSets_Range.value, repsAndSets_Display.value, filtered);
  return {
    labels: agg.map(w => formatPeriodLabel(w.period, repsAndSets_Display.value)),
    reps: agg.map(w => w.reps ?? 0),
    sets: agg.map(w => w.sets ?? 0)
  };
});

// PRs Over Time - Count total PRs earned in workouts
const prsOverTime_Data = computed(() => {
  const filtered = filterByRange(prsOverTime_Range.value);
  const useWeeks = prsOverTime_Display.value === "wk";
  
  let prMap: Record<string, number> = {};
  
  // CSV mode - calculate PRs with filtering
  if (store.isCSVMode) {
    // Use centralized PR calculation from csvCalculator
    prMap = calculatePRsGrouped(filtered as any, useWeeks ? "week" : "month");
  } else {
    // API mode - count actual PRs from API data
    for (const w of filtered) {
      const d = new Date((w.start_time || 0) * 1000);
      const key = useWeeks ? weekKey(d) : monthKey(d);
      
      // Count PRs from set.prs or set.personalRecords arrays
      let prCount = 0;
      for (const ex of (w.exercises || [])) {
        for (const s of (ex.sets || [])) {
          // set.prs
          const prsArr = Array.isArray(s?.prs) ? s.prs : (s?.prs ? [s.prs] : []);
          // set.personalRecords (Probably deprecated?)
          const personalArr = Array.isArray(s?.personalRecords) ? s.personalRecords : (s?.personalRecords ? [s.personalRecords] : []);
          const allPRs = [...prsArr, ...personalArr].filter(Boolean);
          prCount += allPRs.length;
        }
      }
      
      prMap[key] = (prMap[key] || 0) + prCount;
    }
  }
  
  const keys = Object.keys(prMap).sort();
  return {
    labels: keys.map(k => formatPeriodLabel(k, prsOverTime_Display.value)),
    data: keys.map(k => prMap[k] || 0)
  };
});

// Weekly Rhythm - Distribution across days of week
const weeklyRhythm_Data = computed(() => {
  const days = [
    t("global.days.mondayLong"),
    t("global.days.tuesdayLong"),
    t("global.days.wednesdayLong"),
    t("global.days.thursdayLong"),
    t("global.days.fridayLong"),
    t("global.days.saturdayLong"),
    t("global.days.sundayLong")
  ];
  const counts = [0, 0, 0, 0, 0, 0, 0];
  
  for (const w of workouts.value) {
    const d = new Date((w.start_time || 0) * 1000);
    const day = d.getDay(); // 0=Sun, 1=Mon, ...
    const idx = day === 0 ? 6 : day - 1; // Convert to Mon=0, Sun=6
    if (idx >= 0 && idx < counts.length && counts[idx] !== undefined) counts[idx] += 1;
  }
  
  return {
    labels: days,
    data: counts
  };
});

// ========== CALENDAR HEATMAP (12-Month Contribution Graph) ==========

// Group workouts by date (YYYY-MM-DD)
const workoutsByDay = computed(() => {
  const map: Record<string, number> = {};
  for (const w of workouts.value) {
    const date = new Date((w.start_time || 0) * 1000);
    const dayKey = date.toISOString().slice(0, 10);
    map[dayKey] = (map[dayKey] || 0) + 1;
  }
  return map;
});

// Generate calendar data for the last 12 months (grouped by month)
const calendarData = computed(() => {
  const monthNames = [
    t("global.months.januaryShort"), 
    t("global.months.februaryShort"),
    t("global.months.marchShort"),
    t("global.months.aprilShort"),
    t("global.months.mayShort"),
    t("global.months.juneShort"),
    t("global.months.julyShort"),
    t("global.months.augustShort"),
    t("global.months.septemberShort"),
    t("global.months.octoberShort"),
    t("global.months.novemberShort"),
    t("global.months.decemberShort")
  ];
  
  // Calculate date range: last 12 months (current month + 11 previous)
  const today = new Date();
  const months: Array<{ label: string; year: number; weeks: Array<Array<{ date: Date; dateStr: string; count: number } | null>> }> = [];
  
  // Iterate 12 times backwards to get the last 12 months
  for (let i = 11; i >= 0; i--) {
    const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
    const year = d.getFullYear();
    const monthIndex = d.getMonth();
    const monthLabel = monthNames[monthIndex];
    
    // Get all days in this month
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const monthWeeks: Array<Array<{ date: Date; dateStr: string; count: number } | null>> = [];
    let currentWeek: Array<{ date: Date; dateStr: string; count: number } | null> = [];
    
    // Pad start of first week
    // getDay(): 0=Sun, 1=Mon... 6=Sat. We want Mon=0...Sun=6
    let firstDayOfWeek = new Date(year, monthIndex, 1).getDay();
    // Convert to Mon-start (0=Mon, 6=Sun)
    firstDayOfWeek = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
    
    for (let j = 0; j < firstDayOfWeek; j++) {
      currentWeek.push(null);
    }
    
    // Fill days
    for (let day = 1; day <= daysInMonth; day++) {
      // Use string construction to avoid timezone issues
      const dateStr = `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const date = new Date(year, monthIndex, day);
      const count = workoutsByDay.value[dateStr] || 0;
      
      currentWeek.push({ date, dateStr, count });
      
      if (currentWeek.length === 7) {
        monthWeeks.push(currentWeek);
        currentWeek = [];
      }
    }
    
    // Pad end of last week if needed
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push(null);
      }
      monthWeeks.push(currentWeek);
    }
    
    months.push({
      label: monthLabel || "",
      year,
      weeks: monthWeeks
    });
  }
  
  return months;
});

// Color intensity based on workout count
const getCellColor = (count: number) => {
  if (count === 0) return "var(--bg-secondary)";
  const primary = getComputedStyle(document.documentElement)
    .getPropertyValue("--color-primary")
    .trim() || "#10b981";
  
  // Intensity levels - increased opacity for better visibility
  if (count === 1) return primary + "66"; // ~40%
  // 40% = 66
  // 60% = 99
  // 80% = CC
  // 100% = FF
  
  if (count === 1) return primary + "99"; // 60%
  if (count === 2) return primary + "CC"; // 80%
  if (count >= 3) return primary;         // 100%
  return primary;
};

// Navigate to workouts list for a specific day
const scrollToDay = (day: string) => {
  router.push({ path: "/workouts-list", query: { day } });
};

// Muscle Distribution
const muscleDistribution_Data = computed(() => {
  const filtered = filterByRange(muscleDistribution_Range.value);
  
  // CSV mode - calculate muscle distribution with filtering
  if (store.isCSVMode) {
    // Use centralized muscle calculation from csvCalculator
    const muscleGroups = calculateMuscleDistribution(filtered as any);
    const filteredKeys = Object.keys(muscleGroups).filter(k => (muscleGroups[k] || 0) > 0);
    return {
      labels: filteredKeys,
      data: filteredKeys.map(k => muscleGroups[k] || 0)
    };
  }
  
  // API mode - uses muscle_group from API data
  const muscleGroups: { [key: string]: number } = {};
  
  for (const w of filtered) {
    for (const ex of (w.exercises || [])) {
      const rawMuscle = ex.muscle_group || "Unknown";
      // Apply grouping based on filter setting
      const muscleGroup = muscleDistribution_Grouping.value === "groups" ? groupMuscles(rawMuscle) : rawMuscle;
      const setsCount = ex.sets?.length || 0;
      muscleGroups[muscleGroup] = (muscleGroups[muscleGroup] || 0) + setsCount;
    }
  }
  
  return {
    labels: Object.keys(muscleGroups).map(m => getLocalizedMuscleName(m)),
    data: Object.values(muscleGroups)
  };
});

// Muscle Regions (Stacked Bar Chart)
const muscleRegions_Range = ref<Range>("1y");
const muscleRegions_Display = ref<DisplayStyle>("mo");
const muscleRegions_Grouping = ref<"groups" | "muscles">("groups");

const muscleRegions_Data = computed(() => {
  const filtered = filterByRange(muscleRegions_Range.value);
  const useWeeks = muscleRegions_Display.value === "wk";
  
  // Group by week or month and muscle group
  const periodMuscleData: Record<string, Record<string, number>> = {};
  const allMuscles = new Set<string>();
  
  for (const w of filtered) {
    const date = new Date((w.start_time || 0) * 1000);
    const period = useWeeks ? weekKey(date) : monthKey(date);
    
    if (!periodMuscleData[period]) {
      periodMuscleData[period] = {};
    }
    
    for (const ex of (w.exercises || [])) {
      const rawMuscle = ex.muscle_group || "Unknown";
      // Apply grouping based on filter setting
      const muscleGroup = muscleRegions_Grouping.value === "groups" ? groupMuscles(rawMuscle) : rawMuscle;
      allMuscles.add(muscleGroup);
      const setsCount = ex.sets?.length || 0;
      periodMuscleData[period][muscleGroup] = (periodMuscleData[period][muscleGroup] || 0) + setsCount;
    }
  }
  
  // Sort periods
  const periods = Object.keys(periodMuscleData).sort();
  const muscleGroups = Array.from(allMuscles).sort();
  
  // Create datasets for each muscle group
  const datasets = muscleGroups.map((muscle, index) => {
    const colors = generateGradientColors(muscleGroups.length);
    return {
      label: getLocalizedMuscleName(muscle),
      data: periods.map(period => (periodMuscleData[period] || {})[muscle] || 0),
      backgroundColor: colors[index],
      borderColor: colors[index],
      borderWidth: 1
    };
  });
  
  return {
    labels: periods.map(p => formatPeriodLabel(p, muscleRegions_Display.value)),
    datasets
  };
});

// ---------- Summary Stats ----------

// Workout streak (weeks with >=1 workout)
const workoutStreakWeeks = computed(() => {
  const now = new Date();
  const weeks: Record<string, boolean> = {};
  for (const w of workouts.value) {
    const d = new Date((w.start_time || 0) * 1000);
    weeks[weekKey(d)] = true;
  }
  let streak = 0;
  let current = startOfWeek(now);
  while (weeks[weekKey(current)]) {
    streak++;
    current.setDate(current.getDate() - 7);
  }
  return streak;
});

// Most trained exercise
const mostTrainedExercise = computed(() => {
  const freq: Record<string, number> = {};
  for (const w of workouts.value) {
    for (const ex of (w.exercises || [])) {
      const name = ex.title || "Unknown";
      freq[name] = (freq[name] || 0) + 1;
    }
  }
  let best = "-", max = 0;
  for (const [name, count] of Object.entries(freq)) {
    if (count > max) { max = count; best = name; }
  }
  return { name: best, count: max };
});

// Longest workout
const longestWorkout = computed(() => {
  let best: any = null; let bestDur = -1;
  for (const w of workouts.value) {
    const dur = Math.max(0, Math.floor(((w.end_time || w.start_time || 0) - (w.start_time || 0)) / 60));
    if (dur > bestDur) { bestDur = dur; best = w; }
  }
  return { workout: best, minutes: bestDur };
});

// Total workouts, total volume, avg volume
const totalWorkouts = computed(() => workouts.value.length);
const totalVolume = computed(() => {
  if (store.isCSVMode && csvStats.value) {
    return csvStats.value.totalVolume;
  }
  return workouts.value.reduce((sum, w) => sum + (w.estimated_volume_kg || 0), 0);
});
const avgVolume = computed(() => {
  if (store.isCSVMode && csvStats.value) {
    return csvStats.value.avgVolumePerWorkout;
  }
  return totalWorkouts.value > 0 ? Math.round(totalVolume.value / totalWorkouts.value) : 0;
});

const totalMinutesAll = computed(() => {
  let mins = 0;
  for (const w of workouts.value) {
    const start = w.start_time || 0;
    const end = w.end_time || start;
    mins += Math.max(0, Math.floor((end - start) / 60));
  }
  return mins;
});
const totalHoursAll = computed(() => Number((totalMinutesAll.value / 60).toFixed(2)));

// Get exercises with plateaus - show most recent 5
const plateauExercises = computed(() => {
  const locale = localStorage.getItem("language") || "en";
  
  // Build exercise map similar to Exercises.vue
  const exerciseMap: Record<string, any> = {};
  
  for (const w of workouts.value) {
    const date = new Date((w.start_time || 0) * 1000);
    const dayKey = date.toISOString().slice(0,10);
    
    for (const ex of (w.exercises || [])) {
      const title = ex.title || "Unknown Exercise";
      const id = String(title).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      
      const entry = (exerciseMap[id] ||= {
        id,
        title,
        de_title: ex.de_title,
        es_title: ex.es_title,
        lastDay: null,
        byDay: {} as Record<string, { maxWeight: number; repsAtMax: number }>,
      });
      
      // Track by day
      if (!entry.byDay[dayKey]) {
        entry.byDay[dayKey] = { maxWeight: 0, repsAtMax: 0 };
      }
      
      for (const s of (ex.sets || [])) {
        const weight = Number((s as any).weight_kg ?? (s as any).weight ?? 0);
        const reps = Number((s as any).reps ?? 0);
        
        if (weight > entry.byDay[dayKey].maxWeight) {
          entry.byDay[dayKey].maxWeight = weight;
          entry.byDay[dayKey].repsAtMax = reps;
        } else if (weight === entry.byDay[dayKey].maxWeight) {
          entry.byDay[dayKey].repsAtMax = Math.max(entry.byDay[dayKey].repsAtMax, reps);
        }
      }
    }
  }
  
  // Analyze each exercise for plateau
  const plateaus: Array<{ id: string; title: string; localizedTitle: string; lastDay: string; avgWeight: number; avgReps: number }> = [];
  
  for (const ex of Object.values(exerciseMap)) {
    const days = Object.keys(ex.byDay).sort();
    if (days.length < 5) continue;
    
    // Check if active (trained in last 60 days)
    const lastDay = days[days.length - 1];
    if (!lastDay) continue;
    
    const lastDate = new Date(lastDay);
    const daysSince = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
    if (daysSince > 60) continue;
    
    // Get last 5 sessions
    const last5Days = days.slice(-5);
    const sessions = last5Days.map(d => ({
      day: d,
      maxWeight: ex.byDay[d]?.maxWeight || 0,
      repsAtMax: ex.byDay[d]?.repsAtMax || 0,
    }));
    
    const weights = sessions.map(s => s.maxWeight);
    const reps = sessions.map(s => s.repsAtMax);
    const weightRange = Math.max(...weights) - Math.min(...weights);
    const repsRange = Math.max(...reps) - Math.min(...reps);
    const avgWeight = weights.reduce((a, b) => a + b, 0) / weights.length;
    const avgReps = Math.round(reps.reduce((a, b) => a + b, 0) / reps.length);
    
    // Get localized title
    let localizedTitle = ex.title;
    if (locale === "de" && ex.de_title) {
      localizedTitle = ex.de_title;
    } else if (locale === "es" && ex.es_title) {
      localizedTitle = ex.es_title;
    }
    
    // Plateau detection: weight within 0.5kg and reps within 1
    if (weightRange <= 0.5 && repsRange <= 1) {
      plateaus.push({
        id: ex.id,
        title: ex.title,
        localizedTitle,
        lastDay,
        avgWeight,
        avgReps
      });
    }
  }
  
  // Sort by most recent first, return top 5
  return plateaus
    .sort((a, b) => new Date(b.lastDay).getTime() - new Date(a.lastDay).getTime())
    .slice(0, 5);
});

// Get recent PRs - show last 5 PRs achieved
const recentPRs = computed(() => {
  const locale = localStorage.getItem("language") || "en";
  const prsMap = new Map<string, { exercise: string; localizedExercise: string; type: string; localizedType: string; value: number; date: string }>();
  
  for (const w of workouts.value) {
    const date = new Date((w.start_time || 0) * 1000);
    const dateStr = date.toISOString().slice(0, 10); // TODO: Use localized date settings from Settings.vue
    
    for (const ex of (w.exercises || [])) {
      const exerciseName = ex.title || "Unknown Exercise";
      
      // Get localized exercise title
      let localizedExercise = exerciseName;
      if (locale === "de" && ex.de_title) {
        localizedExercise = ex.de_title;
      } else if (locale === "es" && ex.es_title) {
        localizedExercise = ex.es_title;
      }
      
      for (const s of (ex.sets || [])) {
        const prsArr = Array.isArray(s?.prs) ? s.prs : (s?.prs ? [s.prs] : []);
        const personalArr = Array.isArray(s?.personalRecords) ? s.personalRecords : (s?.personalRecords ? [s.personalRecords] : []);
        
        for (const pr of [...prsArr, ...personalArr].filter(Boolean)) {
          const type = String(pr.type || "");
          const localizedType = getLocalizedPRType(type);
          const value = pr.value || 0;
          
          // Create unique key: exercise + type + value to avoid duplicates
          const key = `${exerciseName}-${type}-${value}`;
          
          // Only keep the most recent PR for each unique combination
          const existing = prsMap.get(key);
          if (!existing || new Date(dateStr) > new Date(existing.date)) {
            prsMap.set(key, {
              exercise: exerciseName,
              localizedExercise,
              type,
              localizedType,
              value,
              date: dateStr
            });
          }
        }
      }
    }
  }
  
  // Convert map to array, sort by date (most recent first) and return top 5
  return Array.from(prsMap.values())
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5);
});

// Navigate to Exercises page and scroll to specific exercise
const navigateToExercise = (localizedTitle: string) => {
  // Generate ID from localized title (same logic as Exercises.vue)
  const id = String(localizedTitle)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  
  router.push({
    name: "Exercises",
    hash: `#${id}`
  });
};

const fetchData = async () => {
  try {
    await store.fetchUserAccount();
    await store.fetchWorkouts();
    processChartData();
  } catch (error) {
    console.error("Error fetching data:", error);
  }
};

const processChartData = () => {
  const dates: string[] = [];
  const volumes: number[] = [];

  workouts.value.forEach((workout) => {
    const date = new Date(workout.start_time * 1000).toLocaleDateString("en-US", { month: "short", day: "numeric" });
    dates.push(date);
    const kg = workout.estimated_volume_kg || 0;
    volumes.push(store.weightUnit === "lbs" ? kg * 2.20462 : kg);
  });

  chartData.value = {
    labels: dates.reverse(),
    datasets: [
      {
        label: "Volume (" + getWeightUnit() + ")",
        backgroundColor: "rgba(16, 185, 129, 0.2)",
        borderColor: "#10b981",
        borderWidth: 2,
        data: volumes.reverse(),
        tension: 0.4,
        fill: true,
      },
    ],
  };
};

// ---------- Chart Options ----------

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
      labels: {
        color: "#94a3b8",
        font: { size: 11 }
      }
    },
  },
  scales: {
    y: {
      grid: {
        color: "#334155",
        drawBorder: false
      },
      ticks: {
        color: "#94a3b8",
        font: { size: 11 }
      },
      border: { display: false }
    },
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: "#94a3b8",
        font: { size: 11 }
      },
      border: { display: false }
    },
  },
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "right" as const,
      labels: {
        color: "#94a3b8",
        padding: 12,
        font: {
          size: 11,
        },
      },
    },
  },
};

// Reusable filter definitions (single source of truth)
const rangeFilters = [
  { value: "all" as Range, label: () => getRangeLabel("all") },
  { value: "1y" as Range, label: () => getRangeLabel("1y") },
  { value: "6m" as Range, label: () => getRangeLabel("6m") },
  { value: "3m" as Range, label: () => getRangeLabel("3m") },
  { value: "1m" as Range, label: () => getRangeLabel("1m") }
];

const displayFilters = [
  { value: "mo" as DisplayStyle, label: () => getDisplayLabel("mo") },
  { value: "wk" as DisplayStyle, label: () => getDisplayLabel("wk") }
];

const groupingFilters = [
  { value: "groups" as "groups" | "muscles", label: () => t("dashboard.charts.muscleFilters.groups") },
  { value: "muscles" as "groups" | "muscles", label: () => t("dashboard.charts.muscleFilters.muscles") }
];

const radarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  elements: {
    line: {
      borderWidth: 0
    },
    point: {
      radius: 0,
      hitRadius: 0,
      hoverRadius: 0
    }
  },
  plugins: {
    legend: {
      display: false,
    },
  },
  scales: {
    r: {
      grid: {
        color: "#334155",
      },
      angleLines: {
        color: "#334155",
      },
      pointLabels: {
        color: "#94a3b8",
        font: { size: 11 }
      },
      ticks: {
        color: "#94a3b8",
        backdropColor: "transparent",
        font: { size: 10 }
      }
    }
  }
};

// Generate distinct colors for muscle distribution (expanded palette)
const generateGradientColors = (count: number): string[] => {
  // Expanded distinct color palette (24 colors) for better variety
  const distinctColors = [
    "#10b981", // Emerald
    "#3b82f6", // Blue
    "#f59e0b", // Amber
    "#ef4444", // Red
    "#8b5cf6", // Purple
    "#06b6d4", // Cyan
    "#ec4899", // Pink
    "#14b8a6", // Teal
    "#f97316", // Orange
    "#6366f1", // Indigo
    "#22c55e", // Green
    "#eab308", // Yellow
    "#84cc16", // Lime
    "#0ea5e9", // Sky Blue
    "#d946ef", // Fuchsia
    "#fb923c", // Light Orange
    "#a855f7", // Light Purple
    "#2dd4bf", // Light Teal
    "#f87171", // Light Red
    "#4ade80", // Light Green
    "#fbbf24", // Light Yellow
    "#38bdf8", // Light Blue
    "#fb7185", // Rose
    "#818cf8", // Light Indigo
  ];
  
  // Return only the colors we need, cycling if necessary
  const result: string[] = [];
  for (let i = 0; i < count; i++) {
    result.push(distinctColors[i % distinctColors.length]!);
  }
  return result;
};

onMounted(() => {
  fetchData();
});
</script>

<!-- =============================================================================== -->

<template>
  <div class="dashboard">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ $t('dashboard.title') }}</h1>
          <p v-if="userAccount" class="subtitle">{{ $t('dashboard.subtitle')}}, {{ userAccount.username }}!</p>
        </div>

        <div class="header-actions">
          <!-- Settings Button -->
          <button @click="$router.push('/settings')" class="settings-btn" title="Settings">
            ⚙️
          </button>
          
          <!-- User Badge -->
          <div v-if="userAccount" class="user-badge">
            <div class="user-avatar">{{ userAccount.username.charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <strong>{{ userAccount.username }}</strong>
              <span>{{ userAccount.email }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t("global.loadingSpinnerText") }}</p>
    </div>

    <!-- Main Content -->
    <div v-else class="dashboard-content">
      <!-- KPI Cards - Compact 4-Column Layout -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon">🏋️</div>
          <div class="kpi-value">{{ totalWorkouts }}</div>
          <div class="kpi-label">{{ $t("dashboard.stats.totalWorkouts") }}</div>
        </div>
        
        <div class="kpi-card">
          <div class="kpi-icon">💪</div>
          <div class="kpi-value">{{ formatWeight(totalVolume) }} {{ getWeightUnit() }}</div>
          <div class="kpi-label">{{ $t("dashboard.stats.totalVolume") }}</div>
        </div>
        
        <div class="kpi-card">
          <div class="kpi-icon">⏳</div>
          <div class="kpi-value">{{ totalHoursAll }}</div>
          <div class="kpi-label">{{ $t("dashboard.stats.totalHoursTrained") }}</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon">🔥</div>
          <div class="kpi-value">{{ workoutStreakWeeks }}</div>
          <div class="kpi-label">{{ $t("dashboard.stats.workoutStreak") }}</div>
        </div>
      </div>

      <!-- Compact KPI Row for Mobile -->
      <div class="kpi-compact-row" style="display: none;">
        <div class="kpi-compact-item">
          <span class="kpi-icon">🏋️</span>
          <span class="kpi-value">{{ totalWorkouts }} workouts</span>
        </div>
        <span>•</span>
        <div class="kpi-compact-item">
          <span class="kpi-icon">💪</span>
          <span class="kpi-value">{{ totalVolume.toLocaleString() }}kg lifted</span>
        </div>
        <span>•</span>
        <div class="kpi-compact-item">
          <span class="kpi-icon">⏳</span>
          <span class="kpi-value">{{ totalHoursAll }} hours trained</span>
        </div>
        <span>•</span>
        <div class="kpi-compact-item">
          <span class="kpi-icon">🔥</span>
          <span class="kpi-value">{{ workoutStreakWeeks }} weeks streak</span>
        </div>
      </div>

      <!-- Plateau Alerts (if any) -->
      <div v-if="plateauExercises.length > 0" class="dashboard-section plateau-section">
        <div class="section-header" @click="toggleSection('plateaus')">
          <div class="section-title">
            <span class="section-icon">⏸️</span>
            <h2>{{ $t("dashboard.sections.plateausDetected", { count: plateauExercises.length }) }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.plateaus ? '▼' : '▶' }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.plateaus" class="section-content">
            <div class="plateau-grid">
              <div 
                v-for="plateau in plateauExercises" 
                :key="plateau.id"
                class="plateau-card"
                @click="navigateToExercise(plateau.localizedTitle)"
              >
                <div class="plateau-icon">⏸️</div>
                <div class="plateau-content">
                  <div class="plateau-title">{{ plateau.localizedTitle }}</div>
                  <div class="plateau-meta">{{ formatWeight(plateau.avgWeight) }} {{ getWeightUnit() }} × {{ plateau.avgReps }} {{ $t('global.sw.reps') }}</div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Recent PRs Section -->
      <div v-if="recentPRs.length > 0" class="dashboard-section pr-section">
        <div class="section-header" @click="toggleSection('prs')">
          <div class="section-title">
            <span class="section-icon">🏆</span>
            <h2>{{ $t("dashboard.sections.recentPRs", { count: recentPRs.length }) }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.prs ? '▼' : '▶' }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.prs" class="section-content">
            <div class="pr-grid">
              <div 
                v-for="(pr, index) in recentPRs" 
                :key="index"
                class="pr-card"
              >
                <div class="pr-icon">🏆</div>
                <div class="pr-content">
                  <div class="pr-exercise">{{ pr.localizedExercise }}</div>
                  <div class="pr-type">{{ pr.localizedType }}</div>
                  <div class="pr-value">{{ formatPRValue(pr.type, pr.value) }}</div>
                </div>
                <div class="pr-date">{{ new Date(pr.date).toLocaleDateString() }}</div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Training Analytics Section (Expandable) -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('trainingAnalytics')">
          <div class="section-title">
            <span class="section-icon">📊</span>
            <h2>{{ $t("dashboard.sections.trainingAnalysis") }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.trainingAnalytics ? "▼" : "▶" }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.trainingAnalytics" class="section-content">
            <div class="charts-grid">
              <!-- Hours Trained Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>⏳ {{ $t("dashboard.charts.hoursTrained") }}</h3>
                    <span class="chart-subtitle">{{ $t("dashboard.charts.hoursTrainedDescription") }}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="hoursTrained_Range = filter.value" :class="['filter-btn', { active: hoursTrained_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in displayFilters" :key="filter.value" @click="hoursTrained_Display = filter.value" :class="['filter-btn', { active: hoursTrained_Display === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Line 
                    :key="'hours-' + hoursTrained_Range" 
                    :data="{ 
                      labels: hoursTrained_Data.labels, 
                      datasets: [{ 
                        label: $t('global.sw.hours'), 
                        data: hoursTrained_Data.data, 
                        borderColor: primaryColor, 
                        backgroundColor: primaryColor + '33', 
                        fill: true, 
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                      }] 
                    }" 
                    :options="chartOptions" 
                  />
                </div>
              </div>

              <!-- Volume Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>💪 {{ $t('dashboard.charts.volumeProgression') }}</h3>
                    <span class="chart-subtitle">{{ $t('dashboard.charts.volumeProgressionDescription') }}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="volumeProgression_Range = filter.value" :class="['filter-btn', { active: volumeProgression_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in displayFilters" :key="filter.value" @click="volumeProgression_Display = filter.value" :class="['filter-btn', { active: volumeProgression_Display === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Line 
                    :key="'volume-' + volumeProgression_Range" 
                    :data="{ 
                      labels: volumeProgression_Data.labels, 
                      datasets: [{ 
                        label: $t('global.sw.volume') + ` (${getWeightUnit()})`, 
                        data: volumeProgression_Data.data, 
                        borderColor: secondaryColor, 
                        backgroundColor: secondaryColor + '33', 
                        fill: true, 
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                      }] 
                    }" 
                    :options="chartOptions" 
                  />
                </div>
              </div>

              <!-- Reps/Sets Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>📊 {{ $t('dashboard.charts.repsAndSets') }}</h3>
                    <span class="chart-subtitle">{{ $t('dashboard.charts.repsAndSetsDescription') }}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="repsAndSets_Range = filter.value" :class="['filter-btn', { active: repsAndSets_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in displayFilters" :key="filter.value" @click="repsAndSets_Display = filter.value" :class="['filter-btn', { active: repsAndSets_Display === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Line 
                    :key="'rs-' + repsAndSets_Range" 
                    :data="{ 
                      labels: repsAndSets_Data.labels, 
                      datasets: [
                        { 
                          label: 'Reps', 
                          data: repsAndSets_Data.reps, 
                          borderColor: primaryColor, 
                          backgroundColor: primaryColor + '26', 
                          fill: true, 
                          tension: 0.4,
                          borderWidth: 2,
                          pointRadius: 3,
                          pointHoverRadius: 5
                        },
                        { 
                          label: 'Sets', 
                          data: repsAndSets_Data.sets, 
                          borderColor: secondaryColor, 
                          backgroundColor: secondaryColor + '26', 
                          fill: true, 
                          tension: 0.4,
                          borderWidth: 2,
                          pointRadius: 3,
                          pointHoverRadius: 5
                        }
                      ] 
                    }" 
                    :options="{ 
                      ...chartOptions, 
                      plugins: { 
                        ...chartOptions.plugins, 
                        legend: { 
                          display: true, 
                          position: 'top' as const,
                          labels: { 
                            color: '#94a3b8', 
                            font: { size: 11 },
                            usePointStyle: true,
                            boxWidth: 6,
                            boxHeight: 6,
                            padding: 15
                          } 
                        } 
                      } 
                    }" 
                  />
                </div>
              </div>

              <!-- PRs Over Time Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>🏆 {{ $t('dashboard.charts.PRsOverTime') }}</h3>
                    <span class="chart-subtitle">{{ $t('dashboard.charts.PRsOverTimeDescription') }}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="prsOverTime_Range = filter.value" :class="['filter-btn', { active: prsOverTime_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in displayFilters" :key="filter.value" @click="prsOverTime_Display = filter.value" :class="['filter-btn', { active: prsOverTime_Display === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Line 
                    :key="'prs-' + prsOverTime_Range" 
                    :data="{ 
                      labels: prsOverTime_Data.labels, 
                      datasets: [{ 
                        label: 'PRs', 
                        data: prsOverTime_Data.data, 
                        borderColor: primaryColor, 
                        backgroundColor: primaryColor + '33', 
                        fill: true, 
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: primaryColor
                      }] 
                    }" 
                    :options="chartOptions" 
                  />
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Exercise Insights Section -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('exerciseInsights')">
          <div class="section-title">
            <span class="section-icon">🏆</span>
            <h2>{{ $t("dashboard.sections.exerciseInsights") }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.exerciseInsights ? '▼' : '▶' }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.exerciseInsights" class="section-content">
            <div class="insights-grid">
              <!-- Most Trained Exercise Widget -->
              <div class="insight-card">
                <div class="insight-icon">🏆</div>
                <div class="insight-content">
                  <div class="insight-label">{{ $t('dashboard.stats.mostTrainedExercise') }}</div>
                  <div class="insight-value">{{ mostTrainedExercise.name }}</div>
                  <div class="insight-meta">{{ mostTrainedExercise.count }} {{ $t('dashboard.stats.sessions') }}</div>
                </div>
              </div>

              <!-- Longest Workout Widget -->
              <div class="insight-card">
                <div class="insight-icon">⏱️</div>
                <div class="insight-content">
                  <div class="insight-label">{{ $t('dashboard.stats.longestWorkout') }}</div>
                  <div class="insight-value">{{ formatDuration(longestWorkout.minutes) }}</div>
                </div>
              </div>

              <!-- Average Volume Widget -->
              <div class="insight-card">
                <div class="insight-icon">📊</div>
                <div class="insight-content">
                  <div class="insight-label">{{ $t('dashboard.stats.avgVolume') }}</div>
                  <div class="insight-value">{{ formatWeight(avgVolume) }} {{ getWeightUnit() }}</div>
                  <div class="insight-meta">{{ $t('dashboard.stats.perWorkout') }}</div>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Calendar Views Section -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('calendarViews')">
          <div class="section-title">
            <span class="section-icon">📅</span>
            <h2>{{$t("dashboard.sections.calendarViews")}}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.calendarViews ? '▼' : '▶' }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.calendarViews" class="section-content">
            <div class="charts-grid">
              <!-- Calendar Heatmap Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>📅 {{$t("dashboard.charts.workoutCalendar")}}</h3>
                    <span class="chart-subtitle">{{$t("dashboard.charts.workoutCalendarDescription")}}</span>
                  </div>
                </div>
                <div class="chart-body">
                  <div class="calendar-heatmap">
                    <div class="calendar-grid-container">
                      <!-- Months Container -->
                      <div class="calendar-months-container">
                        <div 
                          v-for="(month, mIdx) in calendarData" 
                          :key="'m-' + mIdx" 
                          class="calendar-month-block"
                        >
                          <!-- Month Label -->
                          <div class="calendar-month-label">{{ month.label }}</div>
                          
                          <!-- Month Weeks Grid -->
                          <div class="calendar-month-weeks">
                            <div 
                              v-for="(week, wIdx) in month.weeks" 
                              :key="'w-' + mIdx + '-' + wIdx" 
                              class="calendar-week"
                            >
                              <div 
                                v-for="(day, dIdx) in week" 
                                :key="'d-' + mIdx + '-' + wIdx + '-' + dIdx"
                                class="calendar-day"
                                :class="{ 'empty': !day, 'has-workout': day && day.count > 0 }"
                                :style="day ? { backgroundColor: getCellColor(day.count) } : {}"
                                @click="day && day.count > 0 && scrollToDay(day.dateStr)"
                                :title="day ? `${day.dateStr}: ${day.count} workout${day.count !== 1 ? 's' : ''}` : ''"
                              ></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            
              <!-- Weekly Rhythm Radar Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>🔥 {{$t('dashboard.charts.weeklyRhythm')}}</h3>
                    <span class="chart-subtitle">{{$t('dashboard.charts.weeklyRhythmDescription')}}</span>
                  </div>
                </div>
                <div class="chart-body radar-body">
                  <Radar 
                    :data="{ 
                      labels: weeklyRhythm_Data.labels, 
                      datasets: [{ 
                        label: 'Workouts', 
                        data: weeklyRhythm_Data.data, 
                        borderColor: secondaryColor, 
                        backgroundColor: secondaryColor + '66', 
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: secondaryColor,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                      }] 
                    }" 
                    :options="radarOptions" 
                  />
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Muscle Distribution Section -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('muscleDistribution')">
          <div class="section-title">
            <span class="section-icon">💪</span>
            <h2>{{$t("dashboard.sections.muscleDistribution")}}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.muscleDistribution ? '▼' : '▶' }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.muscleDistribution" class="section-content">
            <div class="charts-grid">
              <!-- Muscle Distribution Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>🎯 {{$t('dashboard.charts.muscleDistribution')}}</h3>
                    <span class="chart-subtitle">{{$t('dashboard.charts.muscleDistributionDescription')}}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="muscleDistribution_Range = filter.value" :class="['filter-btn', { active: muscleDistribution_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in groupingFilters" :key="filter.value" @click="muscleDistribution_Grouping = filter.value" :class="['filter-btn', { active: muscleDistribution_Grouping === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body doughnut-body">
                  <Doughnut 
                    :key="'muscle-' + muscleDistribution_Range + '-' + muscleDistribution_Grouping"
                    :data="{
                      labels: muscleDistribution_Data.labels,
                      datasets: [{
                        data: muscleDistribution_Data.data,
                        backgroundColor: generateGradientColors(muscleDistribution_Data.data.length),
                        borderWidth: 0,
                      }]
                    }" 
                    :options="doughnutOptions" 
                  />
                </div>
              </div>
              
              <!-- Muscle Regions Chart -->
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>📊 {{ $t("dashboard.charts.muscleRegions") }}</h3>
                    <span class="chart-subtitle">{{ $t("dashboard.charts.muscleRegionsDescription") }}</span>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button v-for="filter in rangeFilters" :key="filter.value" @click="muscleRegions_Range = filter.value" :class="['filter-btn', { active: muscleRegions_Range === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in displayFilters" :key="filter.value" @click="muscleRegions_Display = filter.value" :class="['filter-btn', { active: muscleRegions_Display === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                    <div class="filter-group">
                      <button v-for="filter in groupingFilters" :key="filter.value" @click="muscleRegions_Grouping = filter.value" :class="['filter-btn', { active: muscleRegions_Grouping === filter.value }]" :title="filter.label()">{{ filter.label() }}</button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Bar
                    :key="'muscle-regions-' + muscleRegions_Range + '-' + muscleRegions_Display + '-' + muscleRegions_Grouping"
                    :data="muscleRegions_Data"
                    :options="{
                      responsive: true,
                      maintainAspectRatio: false,
                      interaction: {
                        mode: 'index' as const,
                        intersect: false
                      },
                      scales: {
                        x: {
                          stacked: true,
                          grid: { display: false },
                          ticks: { color: '#9A9A9A' }
                        },
                        y: {
                          stacked: true,
                          grid: { color: '#2b3553' },
                          ticks: { color: '#9A9A9A' },
                          title: {
                            display: true,
                            text: 'Sets',
                            color: '#9A9A9A'
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          display: true,
                          position: 'bottom' as const,
                          labels: {
                            color: '#94a3b8',
                            font: { size: 11 },
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 12
                          }
                        },
                        tooltip: {
                          mode: 'index' as const,
                          intersect: false,
                          backgroundColor: 'rgba(15, 23, 42, 0.95)',
                          borderColor: 'rgba(51, 65, 85, 0.6)',
                          borderWidth: 1,
                          titleColor: '#f8fafc',
                          bodyColor: '#cbd5e1',
                          padding: 12,
                          displayColors: true
                        }
                      }
                    }"
                  />
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<!-- =============================================================================== -->

<style scoped>
.dashboard {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles */
.dashboard-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.title-section h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, var(--color-primary, #10b981), var(--color-secondary, #06b6d4));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.5rem 0 0;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 400;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.settings-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  backdrop-filter: blur(8px);
  color: var(--text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-btn:hover {
  border-color: var(--color-primary, #10b981);
  color: var(--color-primary, #10b981);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--bg-card);
  backdrop-filter: blur(8px);
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.user-badge:hover {
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
  transform: translateY(-2px);
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary, #10b981), var(--color-secondary, #06b6d4));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1.125rem;
  text-transform: uppercase;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.user-details strong {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 600;
}

.user-details span {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6rem 2rem;
  gap: 1.5rem;
}

.loading-container p {
  color: var(--text-secondary);
}

.loading-spinner {
  width: 56px;
  height: 56px;
  border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
  border-top-color: var(--color-primary, #10b981);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-container p {
  color: #94a3b8;
  font-size: 1rem;
  margin: 0;
}

/* KPI Cards - Compact 4-Column Layout */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(51, 65, 85, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
}

.kpi-icon {
  font-size: 1.75rem;
  opacity: 0.9;
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f8fafc;
  line-height: 1;
}

.kpi-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.2;
}

/* Plateau Alert Section */
.plateau-section {
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.4);
}

.plateau-section .section-header {
  background: rgba(251, 191, 36, 0.15);
}

.plateau-section .section-content {
  background: rgba(251, 191, 36, 0.05);
}

.plateau-section .section-icon {
  color: #fbbf24;
}

.plateau-section .section-title h2 {
  color: #fbbf24;
}

.plateau-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.plateau-card {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 10px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.plateau-card:hover {
  transform: translateY(-2px);
  border-color: #fbbf24;
  box-shadow: 0 8px 20px rgba(251, 191, 36, 0.2);
  background: rgba(15, 23, 42, 1);
}

.plateau-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.plateau-content {
  flex: 1;
  min-width: 0;
}

.plateau-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f8fafc;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plateau-meta {
  font-size: 0.8rem;
  color: #fbbf24;
  font-weight: 500;
}

/* PR Section Styles */
.pr-section {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.4);
}

.pr-section .section-header {
  background: rgba(16, 185, 129, 0.15);
}

.pr-section .section-content {
  background: rgba(16, 185, 129, 0.05);
}

.pr-section .section-icon {
  color: #10b981;
}

.pr-section .section-title h2 {
  color: #10b981;
}

.pr-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
  max-width: 100%;
}

@media (min-width: 1200px) {
  .pr-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

.pr-card {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 10px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
}

.pr-card:hover {
  transform: translateY(-2px);
  border-color: #10b981;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.2);
  background: rgba(15, 23, 42, 1);
}

.pr-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.pr-content {
  flex: 1;
  min-width: 0;
}

.pr-exercise {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f8fafc;
  margin-bottom: 0.125rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pr-type {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: capitalize;
  margin-bottom: 0.25rem;
}

.pr-value {
  font-size: 0.85rem;
  color: #10b981;
  font-weight: 600;
}

.pr-date {
  font-size: 0.75rem;
  color: #64748b;
  flex-shrink: 0;
}

/* Dashboard Sections (Expandable/Collapsible) */
.dashboard-section {
  margin-bottom: 1rem;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.6);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1.25rem;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.section-header:hover {
  background: rgba(30, 41, 59, 0.9);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.section-icon {
  font-size: 1.25rem;
}

.section-title h2 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-toggle {
  display: flex;
  align-items: center;
}

.toggle-icon {
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
}

.section-content {
  padding: 1.5rem;
  border-top: 1px solid rgba(51, 65, 85, 0.4);
}

/* Insights Grid (for Exercise Insights section) */
.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.insight-card {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.6);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  transition: all 0.3s ease;
}

.insight-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
}

.insight-icon {
  font-size: 2rem;
  flex-shrink: 0;
  opacity: 0.9;
}

.insight-content {
  flex: 1;
  min-width: 0;
}

.insight-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.insight-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.insight-meta {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.plateau-card {
  cursor: pointer;
  transition: all 0.25s ease;
}

.plateau-card:hover {
  transform: translateY(-4px);
  border-color: rgba(251, 191, 36, 0.8);
  box-shadow: 0 12px 24px rgba(251, 191, 36, 0.2);
}

.plateau-card .insight-icon {
  color: rgba(251, 191, 36, 0.9);
}


/* Stats Grid (Legacy - keeping for compatibility) */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  padding: 1.25rem 1rem;
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.6);
  display: flex;
  align-items: center;
  gap: 0.9rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
  background: rgba(15, 23, 42, 1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
  background: rgba(16, 185, 129, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f8fafc;
  margin-bottom: 0.25rem;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Charts Grid - 2 Column Layout */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.chart-container {
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.6);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.chart-container:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 50%, transparent);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--color-primary, #10b981) 12%, transparent);
  transform: translateY(-2px);
}

.chart-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary, #10b981) 5%, transparent), color-mix(in srgb, var(--color-secondary, #06b6d4) 5%, transparent));
}

.chart-title-section {
  flex: 1;
  min-width: 0;
}

.chart-header h2, .chart-header h3 {
  margin: 0 0 0.25rem;
  color: #f8fafc;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.25px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-subtitle {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
}

.chart-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.5);
}

.filter-btn {
  padding: 0.375rem 0.75rem;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-btn:hover {
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.1);
}

.filter-btn.active {
  background: var(--color-primary, #10b981);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.chart-body {
  flex: 1;
  padding: 1.25rem 1rem;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.doughnut-body {
  min-height: 320px;
  padding: 1.5rem 1rem;
}

.radar-body {
  min-height: 320px;
  padding: 1.5rem 1rem;
}

/* Responsive Adjustments */
@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

/* ========== Calendar Heatmap Styles ========== */
.calendar-heatmap {
  width: 100%;
  padding: 0.5rem 0;
  overflow-x: auto;
}

.calendar-grid-container {
  display: flex;
  gap: 12px;
}

.calendar-months-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px; /* Space between months */
  flex: 1;
  justify-content: space-between;
}

.calendar-month-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03); /* Slightly lighter than bg-primary */
  padding: 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08); /* Subtle border */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.calendar-month-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
  height: 16px;
}

.calendar-month-weeks {
  display: flex;
  gap: 4px;
}

.calendar-week {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.calendar-day {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  cursor: default;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.15s ease;
  background-color: rgba(255, 255, 255, 0.02); /* Default empty color */
}

.calendar-day.has-workout {
  cursor: pointer;
}

.calendar-day.empty {
  background-color: transparent;
  border: none;
  cursor: default;
}

.calendar-day.has-workout:hover {
  transform: scale(1.3);
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  z-index: 10;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .calendar-heatmap {
    overflow-x: scroll;
    padding: 0.5rem;
  }
  
  .calendar-grid-container {
    gap: 8px;
  }
  
  .calendar-months-container {
    gap: 12px;
    flex-wrap: nowrap; /* Keep horizontal scroll on mobile */
    justify-content: flex-start;
  }
  
  .calendar-day {
    width: 10px;
    height: 10px;
  }
  
  .calendar-month-label {
    font-size: 0.75rem;
  }
}

/* Reverted forcing canvas sizing — allow chart library to manage canvas sizing for accurate axes */

@media (max-width: 768px) {
  .user-badge {
    display: none;
  }
  
  .settings-btn {
    display: none;
  }

  .dashboard {
    padding: 1.5rem 1rem;
  }
  
  .title-section h1 {
    font-size: 1.875rem;
  }
  
  /* Hide plateau/PR section titles when collapsible is active */
  .plateau-section .plateau-section-title:not(),
  .pr-section .pr-section-title:not() {
    display: none;
  }
  
  /* Compact KPI Row for Mobile */
  .stats-grid,
  .kpi-grid {
    display: none; /* Hide card grid on mobile */
  }
  
  .kpi-compact-row {
    display: flex !important; /* Show compact row on mobile */
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 1rem;
    /* background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); */
    
    border-radius: 12px;
    margin-bottom: 1.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }
  
  .kpi-compact-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    white-space: nowrap;
  }
  
  .kpi-compact-item .kpi-icon {
    font-size: 1rem;
  }
  
  .kpi-compact-item .kpi-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #f8fafc;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  /* Reduce nesting padding on mobile for charts */
  .section-content {
    padding: 1rem 0.5rem;
  }
  
  .chart-container {
    border-radius: 12px;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
  }
  
  .chart-filters {
    width: 100%;
    justify-content: flex-end;
  }
  
  /* Make filter buttons smaller to fit mo/wk on same line */
  .filter-btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.7rem;
  }
  
  .chart-body {
    padding: 0.75rem 0.5rem;
    min-height: 260px;
  }
  
  .doughnut-body,
  .radar-body {
    min-height: 260px;
    padding: 1rem 0.5rem;
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: 1rem 0.5rem;
  }
  
  .title-section h1 {
    font-size: 1.625rem;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-value {
    font-size: 1.375rem;
  }
  
  .stat-icon {
    width: 44px;
    height: 44px;
    font-size: 1.375rem;
  }
  
  .user-avatar {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  /* Further reduce padding on smallest screens */
  .section-content {
    padding: 0.75rem 0.25rem;
  }
  
  .chart-header {
    padding: 0.5rem 0.75rem;
  }
  
  .chart-body {
    padding: 0.5rem 0.25rem;
    min-height: 240px;
  }
  
  .doughnut-body,
  .radar-body {
    padding: 0.75rem 0.25rem;
    min-height: 240px;
  }
  
  /* Make KPI cards more compact */
  .kpi-grid {
    gap: 0.75rem;
  }
  
  .kpi-card {
    padding: 1rem 0.75rem;
  }
}
</style>
