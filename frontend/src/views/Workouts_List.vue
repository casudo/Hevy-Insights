<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useHevyCache } from "../stores/hevy_cache";
import { useI18n } from "vue-i18n";

const store = useHevyCache();
const userAccount = computed(() => store.userAccount);
const { t } = useI18n();

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
  const days = [t("global.sunday"), t("global.monday"), t("global.tuesday"), t("global.wednesday"), t("global.thursday"), t("global.friday"), t("global.saturday")];
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

// PR helpers using sets.prs / sets.personalRecords
type PRItem = { type: string; value: number | string };
const extractSetPRs = (set: any): PRItem[] => {
  const prsArr = Array.isArray(set?.prs) ? set.prs : (set?.prs ? [set.prs] : []);
  const personalArr = Array.isArray(set?.personalRecords) ? set.personalRecords : (set?.personalRecords ? [set.personalRecords] : []);
  const all = [...prsArr, ...personalArr].filter(Boolean).map((p: any) => ({ type: String(p.type || ''), value: p.value }));
  return all.filter(p => p.type);
};
const exercisePRs = (exercise: any): PRItem[] => {
  const sets = Array.isArray(exercise?.sets) ? exercise.sets : [];
  const items: PRItem[] = [];
  for (const s of sets) items.push(...extractSetPRs(s));
  const seen = new Set<string>();
  return items.filter(it => { const k = `${it.type}|${it.value}`; if (seen.has(k)) return false; seen.add(k); return true; });
};
const setHasPR = (set: any) => extractSetPRs(set).length > 0;
const workoutPRCount = (workout: any) => {
  let count = 0;
  for (const ex of (workout.exercises || [])) {
    for (const s of (ex.sets || [])) count += extractSetPRs(s).length;
  }
  return count;
};

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
  const primary = getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() || '#10b981';
  return count > 0 ? primary : "var(--bg-secondary)"; // single color for days with workouts
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
    <!-- Header Section -->
    <div class="workouts-list-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ $t('workouts.workoutsListTitle') }}</h1>
          <p class="subtitle">{{ $t('workouts.workoutsListSubtitle') }}</p>
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

    <!-- Top Row -->
    <div class="contrib-graph">
      <div class="graph-and-filters">
        <!-- Contribution Graph (hidden on mobile via CSS) -->
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
        <!-- Filters -->
        <div class="filters">
          <label class="filter-label">{{ $t('global.timeRangeFilter.timeRange') }}</label>
          <select class="filter-select" :value="filterRange" @change="onChangeFilter(($event.target as HTMLSelectElement).value as any)">
            <option value="all">{{ $t('global.timeRangeFilter.allTime') }}</option>
            <option value="1w">{{ $t('global.timeRangeFilter.lastWeek') }}</option>
            <option value="1m">{{ $t('global.timeRangeFilter.lastMonth') }}</option>
            <option value="3m">{{ $t('global.timeRangeFilter.last3Months') }}</option>
            <option value="6m">{{ $t('global.timeRangeFilter.last6Months') }}</option>
            <option value="12m">{{ $t('global.timeRangeFilter.last12Months') }}</option>
          </select>
          <label class="filter-label">{{ $t('global.searchFilter.byNumber') }}</label>
          <input class="filter-input" type="number" min="1" placeholder="#" v-model.number="filters.workoutNumber" />
          <label class="filter-label">{{ $t('global.searchFilter.byName') }}</label>
          <input class="filter-input" type="text" placeholder="Contains…" v-model="filters.workoutName" />
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t('global.loadingSpinnerText') }}</p>
    </div>

    <div v-else class="list">
      <div v-for="workout in filteredAndSearchedWorkouts" :key="workout.id" class="item" :data-day="new Date(workout.start_time * 1000).toISOString().slice(0,10)">
        <!-- Collapsed line -->
        <button class="item-toggle" @click="toggleItem(workout.id)">
          <div class="line">
            <span class="pill pill-green">#{{ workoutIndex(workout.id) }}</span>
            <span class="line-date">{{ formatDateFull(workout.start_time) }}</span>
            <span class="line-sep">•</span>
            <span class="line-name">{{ workout.title || workout.name || "Unnamed" }}</span>
            <span v-if="bpmDisplay(workout)" class="pill pill-red">❤️ {{ bpmDisplay(workout) }}</span>
            <span v-if="caloriesDisplay(workout)" class="pill pill-orange">🔥 {{ caloriesDisplay(workout) }}</span>
            <span v-if="workoutPRCount(workout) > 0" class="pill pill-gold" title="Personal Records">🏆 {{ workoutPRCount(workout) }}</span>
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
              <div class="stat"><strong>{{ workout.estimated_volume_kg?.toLocaleString() || 0 }} kg</strong><span>{{ $t('global.volume') }}</span></div>
              <div class="stat"><strong>{{ formatDuration(workout.start_time, workout.end_time) }}</strong><span>{{ $t('global.duration') }}</span></div>
              <div class="stat"><strong>{{ workout.exercises?.length || 0 }}</strong><span>{{ $t('global.exercises') }}</span></div>
              <div class="stat"><strong>{{ totalSets(workout) }}</strong><span>Sets</span></div>
              <div class="stat" v-if="workout.description"><strong>{{ workout.description }}</strong><span>{{ $t('global.description') }}</span></div>
            </div>
          </div>

          <!-- Exercises list with thumbnails -->
          <div class="exercises">
            <h3>{{ $t('global.exercises') }}</h3>
            <div class="exercise-grid">
              <div v-for="(exercise, exIdx) in workout.exercises" :key="exercise.id" class="exercise">
                <div class="exercise-header">
                  <span class="pill pill-blue">#{{ exIdx + 1 }}</span>
                  <img v-if="exercise.thumbnail_url" :src="exercise.thumbnail_url" class="thumb" alt="Exercise thumbnail" />
                  <div class="exercise-title">{{ exercise.title || "Unknown Exercise" }}</div>
                </div>
              <div v-if="exercisePRs(exercise).length" class="pr-summary">
                <span v-for="(pr, i) in exercisePRs(exercise)" :key="i" class="pr-chip">{{ (pr.type || '').split('_').join(' ') }}: <strong>{{ pr.value }}</strong></span>
              </div>
              <table class="sets-table">
                <thead>
                  <tr>
                    <th>Set</th>
                    <th>{{ $t('global.weight') }} (kg)</th>
                    <th>Reps</th>
                    <th>RPE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="set in exercise.sets" :key="set.id" :class="{ 'set-pr-highlight': setHasPR(set) }">
                    <td>{{ set.index + 1 }}</td>
                    <td>{{ set.weight_kg || "-" }}</td>
                    <td>{{ set.reps || "-" }}</td>
                    <td>{{ set.rpe || "-" }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="exercise.notes" class="exercise-notes"><em>{{ $t('global.notes') }}: {{ exercise.notes }}</em></div>
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
  .workouts-list {
    padding: 1.5rem 1.25rem;
    width: 100%;
    min-height: 100vh;
    background: var(--bg-primary);
  }

  /* Header Styles */
  .workouts-list-header {
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

  .filters { display: flex; align-items: center; gap: 0.75rem; }
  .filter-label { color: var(--text-secondary); font-size: 0.9rem; }
  .filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.75rem; }
  .filter-input { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.75rem; width: 120px; }
  
  @media (max-width: 768px) {
    .user-badge {
      display: none;
    }
    
    .settings-btn {
      display: none;
    }
  }

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
  .loading-spinner { width: 48px; height: 48px; border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 25%, transparent); border-top-color: var(--color-primary, #10b981); border-radius: 50%; animation: spin 0.9s linear infinite; }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

  .list { display: flex; flex-direction: column; gap: 0.75rem; }
  .item { border: 1px solid var(--border-color); border-radius: 10px; background: var(--bg-card); overflow: hidden; transition: all 0.3s ease; }
  .item:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); border-color: var(--color-primary, #10b981); }
  .item-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); color: var(--text-primary); border: none; padding: 0.75rem 1rem; cursor: pointer; transition: all 0.2s ease; }
  .item-toggle:hover { background: rgba(30, 41, 59, 0.8); }
  .item .line { display: flex; align-items: center; flex-wrap: wrap; gap: 0.4rem; }
  .line-date { color: var(--text-secondary); font-weight: 600; }
  .line-name { color: var(--text-primary); font-weight: 700; }
  .line-sep { color: var(--text-secondary); }
  .pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; border: 1px solid transparent; }
  .pill-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.35); }
  .pill-orange { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.35); }
  .pill-green { background: color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent); color: var(--color-primary, #10b981); border-color: color-mix(in srgb, var(--color-primary, #10b981) 35%, transparent); }
  .pill-blue { background: rgba(59,130,246,0.15); color: #3b82f6; border-color: rgba(59,130,246,0.35); }
  .pill-gold { background: rgba(201, 187, 0, 0.205); color: #eeea05; border-color: rgba(253, 228, 3, 0.35); }
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
  .exercise { border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; overflow: hidden; background: rgba(0, 0, 0, 0.2); }
  .exercise-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
  .exercise-header { display: flex; align-items: center; gap: 0.5rem; background: rgba(0, 0, 0, 0.3); padding: 0.6rem 0.75rem; transition: all 0.2s ease; }
  .exercise-header:hover { background: rgba(0, 0, 0, 0.4); }
  .exercise-header .thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border-color); }
  .exercise-title { font-weight: 600; font-size: 0.95rem; }
  .sets-table { width: 100%; border-collapse: collapse; }
  .sets-table th, .sets-table td { padding: 0.5rem; border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-primary); }
  .sets-table th { color: var(--text-secondary); font-weight: 500; }
  .exercise-notes { padding: 0.5rem 0.75rem; color: var(--text-secondary); }

  /* PR styling for list view */
  .set-pr-highlight { border-left: 5px solid #f59e0b; }
  .pr-summary { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0; padding: 0.25rem 0.5rem; }
  .pr-chip { background: rgba(245, 158, 11, 0.22); color: #eedebc; border: 2px solid #f59e0b; border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.85rem; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.15); margin: 2px; }

  @media (max-width: 900px) {
    .row { grid-template-columns: 1fr; }
    .stats { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
  }

  /* Mobile Responsive */
  @media (max-width: 640px) {
    /* Hide contribution graph entirely on mobile */
    .graph-area { display: none !important; }

    .workouts-list { padding: 1rem; }
    .header-row { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
    .filters { flex-wrap: wrap; }
    .contrib-graph .grid { flex-direction: column; gap: 8px; }
    .contrib-graph .weekday-col { flex-direction: row; gap: 6px; }
    .contrib-graph .weekday { width: auto; text-align: left; }
    .weeks-wrap { overflow-x: auto; padding-bottom: 4px; }
    .details { padding: 0.75rem; }
    .media-grid { grid-template-columns: 1fr; }
    .stats { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
    .exercise-grid { grid-template-columns: 1fr; }
    .exercise-header { flex-wrap: wrap; }
    .sets-table { display: block; overflow-x: auto; width: 100%; }
    .sets-table table { min-width: 100%; width: 100%; }
  }

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.625rem;
  }
}
</style>
