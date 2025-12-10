<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useHevyCache } from "../stores/hevy_cache";

const store = useHevyCache();

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

const formatDate = (timestamp: number) => new Date(timestamp * 1000).toLocaleString();
const formatDuration = (start: number, end: number) => `${Math.floor((end - start) / 60)} min`;

const toggleExercise = (exerciseId: string) => {
  expandedExercises.value[exerciseId] = !expandedExercises.value[exerciseId];
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
    <div class="header-row">
      <h1>Workout History</h1> <!-- Page title -->

      <div class="filters"> <!-- Filter controls -->
        <label class="filter-label">Time Range</label>
        <select class="filter-select" :value="filterRange" @change="onChangeFilter(($event.target as HTMLSelectElement).value as any)">
          <option value="all">All</option>
          <option value="1w">Last week</option>
          <option value="1m">Last month</option>
          <option value="3m">Last 3 months</option>
          <option value="6m">Last 6 months</option>
          <option value="12m">Last 12 months</option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your workout data...</p>
    </div>

    <div v-else>
      <!-- Top pagination -->
      <div class="pagination top">
        <button @click="prevPage" :disabled="!hasPrev" class="pagination-btn">← Previous</button>
        <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="!hasMore" class="pagination-btn">Next →</button>
      </div>

      <div class="grid">
        <!--  Workout Cards  -->
        <div v-for="workout in paginatedWorkouts" :key="workout.id" class="card">
          <!-- Workout Card Header  -->
          <div class="card-header">
            <div class="title-row">
              <span class="index-pill">#{{ workoutIndex(workout.id) }}</span>
              <h2>{{ workout.name || "Unnamed Workout" }}</h2>
            </div>
            <span class="date">{{ formatDate(workout.start_time) }}</span>
          </div>

          <!--  Middle Row with Stats  -->
          <div class="stats-row">
            <div class="stat"><strong>{{ workout.estimated_volume_kg?.toLocaleString() || 0 }} kg</strong><span>Volume</span></div>
            <div class="stat"><strong>{{ formatDuration(workout.start_time, workout.end_time) }}</strong><span>Duration</span></div>
            <div class="stat"><strong>{{ workout.exercises?.length || 0 }}</strong><span>Exercises</span></div>
          </div>

          <!--  Exercises List  -->
          <div class="exercises">
            <h3>Exercises</h3>
            <div v-for="exercise in workout.exercises" :key="exercise.id" class="exercise">
              <button class="exercise-toggle" @click="toggleExercise(exercise.id)">
                <span class="exercise-title">{{ exercise.title || "Unknown Exercise" }}</span>
                <span class="toggle-icon">{{ expandedExercises[exercise.id] ? "▾" : "▸" }}</span>
              </button>

              <div v-show="expandedExercises[exercise.id]" class="exercise-content">
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

                <div v-if="exercise.notes" class="exercise-notes">
                  <em>Notes: {{ exercise.notes }}</em>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom pagination -->
      <div class="pagination bottom">
        <button @click="prevPage" :disabled="!hasPrev" class="pagination-btn">← Previous</button>
        <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="!hasMore" class="pagination-btn">Next →</button>
      </div>
    </div>
  
  </div>
</template>

<!-- ===============================================================================  -->

<style scoped>
  .workouts { padding: 2.5rem 3rem; width: 100%; min-height: 100vh; }
  .header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
  h1 { margin: 0; color: var(--text-primary); font-size: 2rem; font-weight: 600; letter-spacing: -0.5px; }
  .filters { display: flex; align-items: center; gap: 0.75rem; }
  .filter-label { color: var(--text-secondary); font-size: 0.9rem; }
  .filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.75rem; }

  .loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; }
  .loading-spinner { width: 48px; height: 48px; border: 4px solid rgba(16,185,129,0.25); border-top-color: var(--emerald-primary); border-radius: 50%; animation: spin 0.9s linear infinite; }
  @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
  .card { background: var(--bg-card); padding: 1rem; border-radius: 12px; box-shadow: 0 4px 15px var(--shadow); border: 1px solid var(--border-color); transition: all 0.3s ease; }
  .card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px var(--shadow); border-color: var(--emerald-primary); }

  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); }
  .title-row { display: flex; align-items: center; gap: 0.5rem; }
  .index-pill { display: inline-block; background: rgba(16,185,129,0.15); color: var(--emerald-primary); border: 1px solid rgba(16,185,129,0.3); border-radius: 999px; padding: 0.15rem 0.5rem; font-size: 0.8rem; font-weight: 600; }
  .card-header h2 { margin: 0; color: var(--text-primary); font-size: 1.125rem; font-weight: 600; }
  .date { color: var(--text-secondary); font-size: 0.85rem; }

  .stats-row { display: flex; gap: 1.25rem; margin-bottom: 1rem; }
  .stat { display: flex; flex-direction: column; gap: 0.15rem; }
  .stat strong { color: var(--text-primary); font-size: 1rem; }
  .stat span { color: var(--text-secondary); font-size: 0.8rem; }

  .exercises h3 { margin: 0 0 0.5rem; color: var(--text-primary); font-size: 1rem; }
  .exercise { border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; overflow: hidden; }
  .exercise-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); color: var(--text-primary); border: none; padding: 0.6rem 0.75rem; cursor: pointer; }
  .exercise-title { font-weight: 600; }
  .toggle-icon { color: var(--text-secondary); }
  .exercise-content { background: var(--bg-card); }

  .sets-table { width: 100%; border-collapse: collapse; }
  .sets-table th, .sets-table td { padding: 0.5rem; border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-primary); }
  .sets-table th { color: var(--text-secondary); font-weight: 500; }
  .exercise-notes { padding: 0.5rem 0.75rem; color: var(--text-secondary); }

  .pagination { grid-column: 1 / -1; display: flex; justify-content: center; align-items: center; gap: 1rem; margin-top: 1rem; }
  .pagination.top { margin-bottom: 1rem; }
  .pagination.bottom { margin-top: 1rem; }
  .pagination-btn { background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 0.875rem; cursor: pointer; }
  .pagination-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .page-info { color: var(--text-secondary); }

  @media (max-width: 1024px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
</style>
