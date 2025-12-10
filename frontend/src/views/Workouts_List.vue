<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useHevyCache } from "../stores/hevy_cache";

const store = useHevyCache();

// UI state
const filterRange = ref<"all" | "1w" | "1m" | "3m" | "6m" | "12m">("all");
const expanded = ref<Record<string, boolean>>({});

// Loading + source data
const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);
const allWorkoutsRaw = computed(() => store.workouts);

// Sort newest → oldest
const allWorkoutsSorted = computed(() => {
  return [...allWorkoutsRaw.value].sort((a: any, b: any) => (b.start_time || 0) - (a.start_time || 0));
});

// Global workout index (#N): oldest = #1, newest = #total
const workoutIndex = (workoutId: string) => {
  const idx = allWorkoutsSorted.value.findIndex((w: any) => w.id === workoutId);
  if (idx < 0) return "?";
  const total = allWorkoutsSorted.value.length;
  return total - idx;
};

// Filter by date range
const filteredWorkouts = computed(() => {
  if (filterRange.value === "all") return allWorkoutsSorted.value;
  const nowSec = Math.floor(Date.now() / 1000);
  let days: number;
  switch (filterRange.value) {
    case "1w": days = 7; break;
    case "1m": days = 30; break;
    case "3m": days = 90; break;
    case "6m": days = 180; break;
    case "12m": days = 360; break;
    default: days = 90;
  }
  const cutoff = nowSec - days * 24 * 3600;
  return allWorkoutsSorted.value.filter((w: any) => (w.start_time || 0) >= cutoff);
});

// Extra filters
const filters = ref<{ workoutNumber: number | null; workoutName: string }>(
  { workoutNumber: null, workoutName: '' }
);

// Combine date filter with creative filters
const filteredAndSearchedWorkouts = computed(() => {
  const base = filteredWorkouts.value;
  return base.filter((w: any) => {
    // Workout number exact match
    if (filters.value.workoutNumber && workoutIndex(w.id) !== filters.value.workoutNumber) return false;
    // Name contains (case-insensitive)
    if (filters.value.workoutName) {
      const name = (w.name || '').toLowerCase();
      if (!name.includes(filters.value.workoutName.toLowerCase())) return false;
    }
    return true;
  });
});

// Helpers
const formatDateFull = (timestamp: number) => {
  const d = new Date(timestamp * 1000);
  const days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  const dayName = days[d.getDay()];
  const usDate = d.toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "numeric" }); // MM/DD/YYYY
  const time = d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  return `${dayName}, ${usDate} ${time}`;
};

const biometrics = (workout: any) => {
  const bio = workout?.biometrics;
  if (!bio || typeof bio !== "object") return null;
  const hasData = typeof bio.total_calories === "number" || typeof bio.average_heart_rate === "number";
  return hasData ? bio : null;
};
const bpmDisplay = (workout: any) => {
  const bio = biometrics(workout);
  const bpm = bio?.average_heart_rate;
  return typeof bpm === "number" ? `${Math.round(bpm)} bpm` : null;
};
const caloriesDisplay = (workout: any) => {
  const bio = biometrics(workout);
  const cal = bio?.total_calories;
  return typeof cal === "number" ? `${Math.round(cal)} kcal` : null;
};
const formatDuration = (start: number, end: number) => `${Math.floor((end - start) / 60)} min`;
const totalSets = (workout: any) => (workout.exercises || []).reduce((s: number, ex: any) => s + ((ex.sets || []).length), 0);

// Contribution graph (heatmap) data by day
const workoutsByDay = computed(() => {
  const map: Record<string, any[]> = {};
  for (const w of filteredAndSearchedWorkouts.value) {
    const dayKey = new Date((w.start_time || 0) * 1000).toISOString().slice(0,10); // YYYY-MM-DD
    (map[dayKey] ||= []).push(w);
  }
  return map;
});

// Build weeks for a GitHub-like calendar: 52 columns (weeks) x 7 rows (Mon-Sun)
const weeks = computed(() => {
  const monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const end = new Date();
  const start = new Date(end);
  // Go back ~12 months and snap to Monday of the first visible week
  start.setMonth(end.getMonth() - 11);
  start.setDate(1);
  const day = start.getDay(); // 0=Sun,1=Mon
  const offsetToMonday = (day === 0 ? 6 : day - 1);
  start.setDate(start.getDate() - offsetToMonday);

  // Build daily cells first
  const daily: { date: string; count: number; dateObj: Date }[] = [];
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const key = d.toISOString().slice(0,10);
    daily.push({ date: key, count: (workoutsByDay.value[key] || []).length, dateObj: new Date(d) });
  }

  // Group into weeks (chunks of 7 days starting Monday)
  const cols: Array<{ days: typeof daily; monthLabel?: string } > = [];
  for (let i = 0; i < daily.length; i += 7) {
    const chunk = daily.slice(i, i + 7);
    if (chunk.length < 7) break;
    // Month label on the first column that starts a new month (near beginning)
    const firstItem = chunk[0] as { dateObj: Date; date: string };
    const first = firstItem.dateObj ?? new Date(firstItem.date);
    const isFirstWeekOfMonth = first.getDate() <= 7;
    const monthLabel = isFirstWeekOfMonth ? monthNames[first.getMonth()] : undefined;
    cols.push({ days: chunk, monthLabel });
  }
  return cols;
});

const cellColor = (count: number) => {
  return count > 0 ? "#68d391" : "var(--bg-secondary)"; // single color for days with workouts
};

const scrollToDay = async (day: string) => {
  // Auto-expand all workouts on that day
  const workouts = workoutsByDay.value[day] || [];
  for (const w of workouts) expanded.value[w.id] = true;
  await nextTick();
  const anchors = document.querySelectorAll(`[data-day="${day}"]`);
  if (anchors.length) {
    const el = anchors[0] as HTMLElement;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};

const toggleItem = (id: string) => { expanded.value[id] = !expanded.value[id]; };
const onChangeFilter = (val: "all"|"1w"|"1m"|"3m"|"6m"|"12m") => { filterRange.value = val; };

onMounted(async () => { await store.fetchWorkouts(); });
</script>

<!-- ===============================================================================  -->

<template>
  <div class="workouts-list">
    <div class="header-row">
      <h1>Workout History (List)</h1>
    </div>

    <!-- Contribution Graph -->
    <div class="contrib-graph">
      <div class="graph-and-filters">
        <div class="graph-area">
          <div class="month-row">
            <span v-for="(col, ci) in weeks" :key="'m-' + ci" class="month-label">{{ col.monthLabel || '' }}</span>
          </div>
          <div class="grid">
            <div class="weekday-col">
              <span v-for="label in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']" :key="label" class="weekday">{{ label }}</span>
            </div>
            <div class="weeks-wrap">
              <div v-for="(col, ci) in weeks" :key="'c-' + ci" class="week-col">
                <div v-for="day in col.days" :key="day.date" class="cell" :style="{ backgroundColor: cellColor(day.count) }" @click="scrollToDay(day.date)" :title="`${day.date} — ${day.count} workout(s)`"></div>
              </div>
            </div>
          </div>
        </div>
        <div class="filters">
          <label class="filter-label">Time Range</label>
          <select class="filter-select" :value="filterRange" @change="onChangeFilter(($event.target as HTMLSelectElement).value as any)">
            <option value="all">All</option>
            <option value="1w">Last week</option>
            <option value="1m">Last month</option>
            <option value="3m">Last 3 months</option>
            <option value="6m">Last 6 months</option>
            <option value="12m">Last 12 months</option>
          </select>
          <label class="filter-label">By Number</label>
          <input class="filter-input" type="number" min="1" placeholder="#" v-model.number="filters.workoutNumber" />
          <label class="filter-label">Name</label>
          <input class="filter-input" type="text" placeholder="Contains…" v-model="filters.workoutName" />
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your workout data...</p>
    </div>

    <div v-else class="list">
      <div v-for="workout in filteredAndSearchedWorkouts" :key="workout.id" class="item" :data-day="new Date(workout.start_time * 1000).toISOString().slice(0,10)">
        <!-- Collapsed line -->
        <button class="item-toggle" @click="toggleItem(workout.id)">
          <div class="line">
            <span class="pill pill-green">#{{ workoutIndex(workout.id) }}</span>
            <span class="line-date">{{ formatDateFull(workout.start_time) }}</span>
            <span class="line-sep">•</span>
            <span class="line-name">{{ workout.name || "Unnamed" }}</span>
            <span v-if="bpmDisplay(workout)" class="pill pill-red">❤️ {{ bpmDisplay(workout) }}</span>
            <span v-if="caloriesDisplay(workout)" class="pill pill-orange">🔥 {{ caloriesDisplay(workout) }}</span>
          </div>
          <span class="toggle-icon">{{ expanded[workout.id] ? "▾" : "▸" }}</span>
        </button>

        <!-- Expanded details -->
        <div v-show="expanded[workout.id]" class="details">
          <!-- Media + Stats row -->
          <div class="row">
            <div class="media" v-if="(workout.media || []).length">
              <div class="media-grid">
                <template v-for="m in workout.media" :key="m.id || m.url">
                  <img v-if="m.type && m.type.includes('image')" :src="m.url" alt="Workout image" />
                  <video v-else-if="m.type && m.type.includes('video')" :src="m.url" controls></video>
                  <img v-else :src="m.url" alt="Workout media" />
                </template>
              </div>
            </div>
            <div class="stats">
              <div class="stat"><strong>{{ workout.estimated_volume_kg?.toLocaleString() || 0 }} kg</strong><span>Volume</span></div>
              <div class="stat"><strong>{{ formatDuration(workout.start_time, workout.end_time) }}</strong><span>Duration</span></div>
              <div class="stat"><strong>{{ workout.exercises?.length || 0 }}</strong><span>Exercises</span></div>
              <div class="stat"><strong>{{ totalSets(workout) }}</strong><span>Total Sets</span></div>
              <div class="stat" v-if="workout.description"><strong>{{ workout.description }}</strong><span>Description</span></div>
            </div>
          </div>

          <!-- Exercises list with thumbnails -->
          <div class="exercises">
            <h3>Exercises</h3>
            <div class="exercise-grid">
              <div v-for="(exercise, exIdx) in workout.exercises" :key="exercise.id" class="exercise">
                <div class="exercise-header">
                  <span class="pill pill-blue">#{{ exIdx + 1 }}</span>
                  <img v-if="exercise.thumbnail_url" :src="exercise.thumbnail_url" class="thumb" alt="Exercise thumbnail" />
                  <div class="exercise-title">{{ exercise.title || "Unknown Exercise" }}</div>
                </div>
              <table class="sets-table">
                <thead>
                  <tr>
                    <th>Set</th>
                    <th>Weight (kg)</th>
                    <th>Reps</th>
                    <th>RPE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="set in exercise.sets" :key="set.id">
                    <td>{{ set.index + 1 }}</td>
                    <td>{{ set.weight_kg || "-" }}</td>
                    <td>{{ set.reps || "-" }}</td>
                    <td>{{ set.rpe || "-" }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="exercise.notes" class="exercise-notes"><em>Notes: {{ exercise.notes }}</em></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- ===============================================================================  -->

<style scoped>
.workouts-list { padding: 2.5rem 3rem; width: 100%; min-height: 100vh; }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
h1 { margin: 0; color: var(--text-primary); font-size: 2rem; font-weight: 600; letter-spacing: -0.5px; }
.filters { display: flex; align-items: center; gap: 0.75rem; }
.filter-label { color: var(--text-secondary); font-size: 0.9rem; }
.filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.75rem; }

/* Contribution graph */
.contrib-graph { margin-bottom: 1.5rem; }
.contrib-graph .graph-and-filters { display: flex; align-items: flex-start; gap: 1rem; }
.contrib-graph .graph-area { display: inline-block; }
.contrib-graph .month-row { display: flex; gap: 3px; margin-bottom: 4px; }
.contrib-graph .month-label { display: inline-block; width: 12px; font-size: 0.7rem; color: var(--text-secondary); text-align: center; }
.contrib-graph .grid { display: flex; gap: 6px; align-items: flex-start; width: auto; }
.contrib-graph .weekday-col { display: flex; flex-direction: column; gap: 3px; }
.contrib-graph .weekday { width: 28px; font-size: 0.7rem; color: var(--text-secondary); text-align: right; line-height: 12px; }
.contrib-graph .weeks-wrap { display: flex; gap: 3px; }
.contrib-graph .week-col { display: flex; flex-direction: column; gap: 3px; }
.contrib-graph .cell { width: 12px; height: 12px; border-radius: 2px; cursor: pointer; border: 1px solid var(--border-color); }


.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; }
.loading-spinner { width: 48px; height: 48px; border: 4px solid rgba(16,185,129,0.25); border-top-color: var(--emerald-primary); border-radius: 50%; animation: spin 0.9s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

.list { display: flex; flex-direction: column; gap: 0.75rem; }
.item { border: 1px solid var(--border-color); border-radius: 10px; background: var(--bg-card); overflow: hidden; }
.item-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); color: var(--text-primary); border: none; padding: 0.75rem 1rem; cursor: pointer; }
.item .line { display: flex; align-items: center; flex-wrap: wrap; gap: 0.4rem; }
.line-date { color: var(--text-secondary); font-weight: 600; }
.line-name { color: var(--text-primary); font-weight: 700; }
.line-sep { color: var(--text-secondary); }
.pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; border: 1px solid transparent; }
.pill-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.35); }
.pill-orange { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.35); }
.pill-green { background: rgba(16,185,129,0.15); color: var(--emerald-primary); border-color: rgba(16,185,129,0.35); }
.pill-blue { background: rgba(59,130,246,0.15); color: #3b82f6; border-color: rgba(59,130,246,0.35); }
.toggle-icon { color: var(--text-secondary); margin-left: 0.5rem; }

.details { padding: 1rem; }
.row { display: grid; grid-template-columns: 240px 1fr; gap: 1rem; align-items: start; }
.media-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; }
.media-grid img, .media-grid video { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border-color); }

.stats { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 0.75rem; }
.stat { display: flex; flex-direction: column; gap: 0.15rem; }
.stat strong { color: var(--text-primary); font-size: 1rem; }
.stat span { color: var(--text-secondary); font-size: 0.8rem; }

.exercises h3 { margin: 1rem 0 0.5rem; color: var(--text-primary); font-size: 1rem; }
.exercise { border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; overflow: hidden; }
.exercise-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.exercise-header { display: flex; align-items: center; gap: 0.5rem; background: var(--bg-secondary); padding: 0.6rem 0.75rem; }
.exercise-header .thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border-color); }
.exercise-title { font-weight: 600; }
.sets-table { width: 100%; border-collapse: collapse; }
.sets-table th, .sets-table td { padding: 0.5rem; border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-primary); }
.sets-table th { color: var(--text-secondary); font-weight: 500; }
.exercise-notes { padding: 0.5rem 0.75rem; color: var(--text-secondary); }

@media (max-width: 900px) {
  .row { grid-template-columns: 1fr; }
  .stats { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
}
</style>
