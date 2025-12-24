<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useHevyCache } from "../stores/hevy_cache";

const store = useHevyCache();
const userAccount = computed(() => store.userAccount);

// UI state
const currentPage = ref(1);
const workoutsPerPage = 9; // 3 columns x 3 rows per page
const expandedExercises = ref<Record<string, boolean>>({}); // exercise.id -> expanded
const filterRange = ref<"all" | "1w" | "1m" | "3m" | "6m" | "12m">("all");

// Loading + source data
const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);
const allWorkoutsRaw = computed(() => store.workouts);

// Sort newest → oldest for consistent indexing (#N)
const allWorkoutsSorted = computed(() => {
  return [...allWorkoutsRaw.value].sort((a: any, b: any) => (b.start_time || 0) - (a.start_time || 0));
});

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
    case "12m": days = 360; break; // 12 x 30-day months for consistency
    default: days = 90; // fallback
  }
  const cutoff = nowSec - days * 24 * 3600;
  return allWorkoutsSorted.value.filter((w: any) => (w.start_time || 0) >= cutoff);
});

// Pagination on filtered set
const paginatedWorkouts = computed(() => {
  const start = (currentPage.value - 1) * workoutsPerPage;
  const end = start + workoutsPerPage;
  return filteredWorkouts.value.slice(start, end);
});

const totalPages = computed(() => Math.ceil(filteredWorkouts.value.length / workoutsPerPage) || 1);
const hasMore = computed(() => currentPage.value < totalPages.value);
const hasPrev = computed(() => currentPage.value > 1);

// Compute global index number (#N): oldest = #1, newest = #total
const workoutIndex = (workoutId: string) => {
  const idx = allWorkoutsSorted.value.findIndex((w: any) => w.id === workoutId);
  if (idx < 0) return "?";
  const total = allWorkoutsSorted.value.length;
  // Newest should have the highest number
  return total - idx;
};

const nextPage = () => { if (hasMore.value) currentPage.value++; };
const prevPage = () => { if (hasPrev.value) currentPage.value--; };
const firstPage = () => { currentPage.value = 1; };
const lastPage = () => { currentPage.value = totalPages.value; };

const formatDate = (timestamp: number) => new Date(timestamp * 1000).toLocaleString();

const formatDuration = (start: number, end: number) => {
  const minutes = Math.floor((end - start) / 60);
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  const minutesLeft = minutes - hours * 60;
  if (!minutesLeft) return `${hours}h`;
  return `${hours}h ${minutesLeft}m`
};

// Helpers for additional stats
const totalSets = (workout: any) => {
  return (workout.exercises || []).reduce((sum: number, ex: any) => sum + ((ex.sets || []).length), 0);
};
// Biometrics from Hevy API payload
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

// PR helpers based on sets.prs / sets.personalRecords
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
const exerciseHasPR = (exercise: any) => exercisePRs(exercise).length > 0;
// Note: set-level highlighting reverted per request; keep extractor for future use if needed

const toggleExercise = (exerciseId: string) => {
  // Create a new object to ensure reactivity
  expandedExercises.value = {
    ...expandedExercises.value,
    [exerciseId]: !expandedExercises.value[exerciseId]
  };
};

const onChangeFilter = (val: "all"|"1w"|"1m"|"3m"|"6m"|"12m") => {
  filterRange.value = val;
  currentPage.value = 1;
};

onMounted(async () => {
  await store.fetchWorkouts(); // Fetch all workouts
});
</script>

<!-- ===============================================================================  -->

<template>
  <div class="workouts">
    <!-- Header Section -->
    <div class="workouts-card-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ $t('workouts.workoutsCardTitle') }}</h1>
          <p class="subtitle">{{ $t('workouts.workoutsCardSubtitle') }}</p>
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

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t('global.loadingSpinnerText') }}</p>
    </div>

    <div v-else>
      <!-- Top pagination -->
      <div class="pagination top">
        <div class="pagination-controls">
          <button @click="firstPage" :disabled="!hasPrev" class="pagination-btn">《 {{ $t('global.pagination.first') }}</button>
          <button @click="prevPage" :disabled="!hasPrev" class="pagination-btn">← {{ $t('global.pagination.previous') }}</button>
          <span class="page-info">{{ $t('global.pagination.page') }} {{ currentPage }} {{ $t('global.pagination.pageOf') }} {{ totalPages }}</span>
          <button @click="nextPage" :disabled="!hasMore" class="pagination-btn">{{ $t('global.pagination.next') }} →</button>
          <button @click="lastPage" :disabled="!hasMore" class="pagination-btn">{{ $t('global.pagination.last') }} 》</button>
        </div>
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
        </div>
      </div>

      <div class="grid">
        <!--  Workout Cards  -->
        <div v-for="workout in paginatedWorkouts" :key="workout.id" class="card">
          <!-- Workout Card Header  -->
          <div class="card-header">
            <div class="title-row">
              <span class="index-pill">#{{ workoutIndex(workout.id) }}</span>
              <h2>{{ workout.title || workout.name || "Unnamed Workout" }}</h2>
            </div>
            <div class="header-meta">
              <span class="date">{{ formatDate(workout.start_time) }}</span>
              <span v-if="bpmDisplay(workout)" class="pill pill-red" title="Average Heart Rate">❤️ {{ bpmDisplay(workout) }}</span>
              <span v-if="caloriesDisplay(workout)" class="pill pill-orange" title="Total Calories">🔥 {{ caloriesDisplay(workout) }}</span>
            </div>
          </div>

          <!--  Middle Row with Stats  -->
          <div class="stats-row">
            <div class="stat"><strong>{{ workout.estimated_volume_kg?.toLocaleString() || 0 }} kg</strong><span>{{ $t('global.volume') }}</span></div>
            <div class="stat"><strong>{{ formatDuration(workout.start_time, workout.end_time) }}</strong><span>{{ $t('global.duration') }}</span></div>
            <div class="stat"><strong>{{ workout.exercises?.length || 0 }}</strong><span>{{ $t('global.exercises') }}</span></div>
            <div class="stat"><strong>{{ totalSets(workout) }}</strong><span>Total Sets</span></div>
          </div>

          <div v-if="workout.description" class="workout-description">
            <em>{{ workout.description }}</em>
          </div>

          <!--  Exercises List  -->
          <div class="exercises">
            <h3>{{ $t('global.exercises') }}</h3>
            <div v-for="exercise in workout.exercises" :key="exercise.id" class="exercise" :class="{ 'pr-highlight': exerciseHasPR(exercise) }">
              <button class="exercise-toggle" @click="toggleExercise(exercise.id)">
                <span class="exercise-title">{{ exercise.title || "Unknown Exercise" }}</span>
                <span class="toggle-icon">{{ expandedExercises[exercise.id] ? "▾" : "▸" }}</span>
              </button>

              <div v-show="expandedExercises[exercise.id]" class="exercise-content">
                <div v-if="exerciseHasPR(exercise)" class="pr-summary">
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
                    <tr v-for="set in exercise.sets" :key="set.id">
                      <td>{{ set.index + 1 }}</td>
                      <td>{{ set.weight_kg || "-" }}</td>
                      <td>{{ set.reps || "-" }}</td>
                      <td>{{ set.rpe || "-" }}</td>
                    </tr>
                  </tbody>
                </table>

                <div v-if="exercise.notes" class="exercise-notes">
                  <em>{{ $t('global.notes') }}: {{ exercise.notes }}</em>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom pagination -->
      <div class="pagination bottom">
        <div class="pagination-controls">
          <button @click="firstPage" :disabled="!hasPrev" class="pagination-btn">《 {{ $t('global.pagination.first') }}</button>
          <button @click="prevPage" :disabled="!hasPrev" class="pagination-btn">← {{ $t('global.pagination.previous') }}</button>
          <span class="page-info">{{ $t('global.pagination.page') }} {{ currentPage }} {{ $t('global.pagination.pageOf') }} {{ totalPages }}</span>
          <button @click="nextPage" :disabled="!hasMore" class="pagination-btn">{{ $t('global.pagination.next') }} →</button>
          <button @click="lastPage" :disabled="!hasMore" class="pagination-btn">{{ $t('global.pagination.last') }} 》</button>
        </div>
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
        </div>
      </div>
    </div>
  
  </div>
</template>

<!-- ===============================================================================  -->

<style scoped>

.workouts {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles */
.workouts-card-header {
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

@media (max-width: 768px) {
  .user-badge {
    display: none;
  }
  
  .settings-btn {
    display: none;
  }
}

.filters { display: flex; align-items: center; gap: 0.75rem; }
.filter-label { color: var(--text-secondary); font-size: 0.9rem; }
.filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.75rem; }

.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; }
.loading-spinner { width: 48px; height: 48px; border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 25%, transparent); border-top-color: var(--color-primary, #10b981); border-radius: 50%; animation: spin 0.9s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.card { min-width: 0; display: flex; flex-direction: column; }
.card { background: var(--bg-card); padding: 1rem; border-radius: 12px; box-shadow: 0 4px 15px var(--shadow); border: 1px solid var(--border-color); transition: all 0.3s ease; }
.card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px var(--shadow); border-color: var(--color-primary, #10b981); }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); }
.title-row { display: flex; align-items: center; gap: 0.5rem; }
.index-pill { display: inline-block; background: color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent); color: var(--color-primary, #10b981); border: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent); border-radius: 999px; padding: 0.15rem 0.5rem; font-size: 0.8rem; font-weight: 600; }
.card-header h2 { margin: 0; color: var(--text-primary); font-size: 1.125rem; font-weight: 600; }
.header-meta { display: flex; align-items: center; gap: 0.5rem; }
.date { color: var(--text-secondary); font-size: 0.85rem; }
.pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; border: 1px solid transparent; }
.pill-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.35); }
.pill-orange { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.35); }
.pill-pr { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.35); }

.stats-row { display: flex; gap: 1.25rem; margin-bottom: 1rem; }
.stat { display: flex; flex-direction: column; gap: 0.15rem; }
.stat strong { color: var(--text-primary); font-size: 1rem; }
.stat span { color: var(--text-secondary); font-size: 0.8rem; }

.workout-description { margin: 0.5rem 0 1rem; color: var(--text-secondary); }

.exercises h3 { margin: 0 0 0.5rem; color: var(--text-primary); font-size: 1rem; }
.exercise { border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; overflow: hidden; background: rgba(0, 0, 0, 0.2); }
.exercise-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: rgba(0, 0, 0, 0.3); color: var(--text-primary); border: none; padding: 0.6rem 0.75rem; cursor: pointer; transition: all 0.2s ease; }
.exercise-toggle:hover { background: rgba(0, 0, 0, 0.4); }
.exercise-title { font-weight: 600; font-size: 0.95rem; }
.toggle-icon { color: var(--text-secondary); }
.exercise-content { background: rgba(0, 0, 0, 0.15); padding: 0.75rem; }

.sets-table { width: 100%; border-collapse: collapse; }
.sets-table th, .sets-table td { padding: 0.5rem; border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-primary); }
.sets-table th { color: var(--text-secondary); font-weight: 500; }
.exercise-notes { padding: 0.5rem 0.75rem; color: var(--text-secondary); }

/* PR highlighting */
.pr-highlight { border: 2px solid #f59e0b; }
.pr-summary { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0; padding: 0.25rem 0.5rem; }
.pr-chip { background: rgba(245, 158, 11, 0.22); color: #eedebc; border: 2px solid #f59e0b; border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.85rem; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.15); margin: 2px; }

.pagination { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
.pagination.top { margin-bottom: 1rem; }
.pagination.bottom { margin-top: 1rem; }
.pagination-controls { display: flex; justify-content: center; align-items: center; gap: 1rem; }
.pagination-btn { background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.875rem; cursor: pointer; }
.pagination-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.page-info { color: var(--text-secondary); }

/* Mobile Responsive */
@media (max-width: 1024px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) {
  .workouts { padding: 1rem; }
  .header-row { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
  .grid { grid-template-columns: 1fr; }
  .card { padding: 0.75rem; }
  .card-header { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
  .stats-row { flex-wrap: wrap; gap: 0.75rem; }
  .stat strong { font-size: 0.95rem; }
  .sets-table { display: block; overflow-x: auto; width: 100%; }
  .sets-table table { min-width: 100%; width: 100%; }
  
  .pagination {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .pagination-btn {
    padding: 0.375rem 0.625rem;
    font-size: 0.875rem;
  }
  
  .filter-select {
    font-size: 0.875rem;
  }
}
@media (max-width: 480px) {
  .workouts {
    padding: 1rem;
  }
  
  .title-section h1 {
    font-size: 1.625rem;
  }
  
  .user-badge {
    padding: 0.5rem 0.75rem;
  }
  
  .user-avatar {
    display: none;
  }
  
  .user-details span {
    display: none;
  }
}

</style>
