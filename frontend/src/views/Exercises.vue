<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useHevyCache } from "../stores/hevy_cache";
import { Scatter, Bar, Line } from "vue-chartjs";
import { useI18n } from "vue-i18n";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
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
  Title,
  Tooltip,
  Legend
);

const store = useHevyCache();
const userAccount = computed(() => store.userAccount);
const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);
const { t } = useI18n();

// Get theme colors from CSS variables
const primaryColor = computed(() => {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() || '#10b981';
});
const secondaryColor = computed(() => {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-secondary').trim() || '#06b6d4';
});

// Time range filter per exercise
type Range = "all" | "1w" | "1m" | "3m" | "6m" | "12m";
const rangeByExercise = ref<Record<string, Range>>({});
// Collapsed state per exercise (default collapsed)
const expanded = ref<Record<string, boolean>>({});
// Search by exercise name
const search = ref("");

const allWorkouts = computed(() => store.workouts || []);

onMounted(async () => {
  await store.fetchWorkouts();
});

// Build exercise aggregates across all workouts
const exercises = computed(() => {
  const map: Record<string, any> = {};
  for (const w of allWorkouts.value) {
    const date = new Date((w.start_time || 0) * 1000);
    const dayKey = date.toISOString().slice(0,10);
    
    for (const ex of (w.exercises || [])) {
      // Key by exercise title to aggregate across all workouts
      const title = ex.title || "Unknown Exercise";
      const id = String(title)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      const entry = (map[id] ||= {
        id,
        title,
        video_url: ex.url || null,
        sets: [] as any[],
        prs: [] as any[],
      });
      for (const s of (ex.sets || [])) {
        const weight = Number((s as any).weight_kg ?? (s as any).weight ?? 0);
        const reps = Number((s as any).reps ?? 0);
        entry.sets.push({
          day: dayKey,
          weight,
          reps,
          rpe: s.rpe,
          index: s.index,
        });
        const prsArr = Array.isArray(s?.prs) ? s.prs : (s?.prs ? [s.prs] : []);
        const personalArr = Array.isArray(s?.personalRecords) ? s.personalRecords : (s?.personalRecords ? [s.personalRecords] : []);
        for (const p of [...prsArr, ...personalArr].filter(Boolean)) {
          entry.prs.push({ type: String(p.type || ''), value: p.value, day: dayKey });
        }
      }
    }
  }
  // derive computed metrics per exercise
  const list = Object.values(map);
  for (const ex of list) {
    const byDay: Record<string, { maxWeight: number; repsAtMax: number; volume: number; setCount: number; avgVolumePerSet: number }> = {};
    for (const s of ex.sets) {
      const cur = (byDay[s.day] ||= { maxWeight: 0, repsAtMax: 0, volume: 0, setCount: 0, avgVolumePerSet: 0 });
      const setVolume = (Number(s.weight) || 0) * (Number(s.reps) || 0);
      cur.volume += setVolume;
      cur.setCount += 1;
      if ((Number(s.weight) || 0) > cur.maxWeight) {
        cur.maxWeight = Number(s.weight) || 0;
        cur.repsAtMax = Number(s.reps) || 0;
      } else if ((Number(s.weight) || 0) === cur.maxWeight) {
        // If same max weight, keep the highest reps
        cur.repsAtMax = Math.max(cur.repsAtMax, Number(s.reps) || 0);
      }
    }
    // Calculate avg volume per set for each day
    for (const day of Object.keys(byDay)) {
      const dayData = byDay[day];
      if (dayData) {
        dayData.avgVolumePerSet = dayData.setCount > 0 ? dayData.volume / dayData.setCount : 0;
      }
    }
    ex.byDay = byDay;
    // Total sessions (sessions = days trained)
    ex.totalSessions = Object.keys(byDay).length;
    // Compute maxima for scaling graphs safely
    let wMax = 0, rMax = 0, vMax = 0;
    for (const d of Object.keys(byDay)) {
      const v = byDay[d];
      if (v) {
        wMax = Math.max(wMax, v.maxWeight);
        rMax = Math.max(rMax, v.repsAtMax);
        vMax = Math.max(vMax, v.volume);
      }
    }
    // top 3 best sets by weight across ALL workouts
    ex.topSets = [...ex.sets].sort((a,b) => (Number(b.weight)||0) - (Number(a.weight)||0)).slice(0,3);
    // distinct PRs - keep only the best value for each PR type
    const prMap: Record<string, { type: string; value: number; day: string }> = {};
    for (const pr of ex.prs) {
      const type = pr.type || '';
      const val = Number(pr.value) || 0;
      if (!prMap[type] || val > (Number(prMap[type].value) || 0)) {
        prMap[type] = pr;
      }
    }
    ex.prDistinct = Object.values(prMap);
  }
  // Initialize collapsed state for new items
  for (const ex of list) {
    if (!(ex.id in expanded.value)) expanded.value[ex.id] = false;
  }
  return list;
});

// Filtered by search term
const filteredExercises = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return exercises.value;
  return exercises.value.filter((ex: any) => (ex.title || "").toLowerCase().includes(q));
});

const ranges: Array<{ label: string; value: Range }> = [
  { label: "All", value: "all" },
  { label: "1w", value: "1w" },
  { label: "1m", value: "1m" },
  { label: "3m", value: "3m" },
  { label: "6m", value: "6m" },
  { label: "12m", value: "12m" },
];

function filterDates(exId: string, dates: string[]): string[] {
  const range = rangeByExercise.value[exId] || "all";
  if (range === "all") return dates;
  const now = new Date();
  let days = 90;
  if (range === "1w") days = 7;
  else if (range === "1m") days = 30;
  else if (range === "3m") days = 90;
  else if (range === "6m") days = 180;
  else if (range === "12m") days = 360;
  const cutoff = new Date(now.getTime() - days * 24 * 3600 * 1000);
  return dates.filter(d => new Date(d) >= cutoff);
}

// Helper to get filtered day list for an exercise
function filteredDaysFor(ex: any): string[] {
  const days = Object.keys(ex.byDay || {});
  return filterDates(ex.id, days).sort();
}

// Chart data builders for each exercise
function getWeightVsRepsChartData(ex: any) {
  const days = filteredDaysFor(ex);
  const scatterData = days.map((d) => {
    const date = new Date(d);
    const dateLabel = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    return {
      x: ex.byDay[d]?.repsAtMax || 0,
      y: ex.byDay[d]?.maxWeight || 0,
      label: dateLabel,
    };
  });
  
  return {
    datasets: [
      {
        label: "Weight vs Reps",
        data: scatterData,
        backgroundColor: primaryColor.value,
        borderColor: primaryColor.value,
        pointRadius: 6,
        pointHoverRadius: 8,
      },
    ],
  };
}

function getMaxWeightOverTimeChartData(ex: any) {
  const days = filteredDaysFor(ex);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const weightData = days.map((d) => (ex.byDay[d]?.maxWeight || 0));
  
  return {
    labels,
    datasets: [
      {
        label: `${t("exercises.graphs.labels.maxWeight")} (kg)`,
        data: weightData,
        backgroundColor: primaryColor.value + "33",
        borderColor: primaryColor.value,
        borderWidth: 2,
        tension: 0.4,
        fill: true,
      },
    ],
  };
}

function getAvgVolumePerSetChartData(ex: any) {
  const days = filteredDaysFor(ex);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const avgVolData = days.map((d) => Math.round(ex.byDay[d]?.avgVolumePerSet || 0));
  
  return {
    labels,
    datasets: [
      {
        label: `${t("exercises.graphs.labels.avgVolume")} (kg)`,
        data: avgVolData,
        backgroundColor: secondaryColor.value + "33",
        borderColor: secondaryColor.value,
        borderWidth: 2,
        tension: 0.4,
        fill: true,
      },
    ],
  };
}

function getVolumeChartData(ex: any) {
  const days = filteredDaysFor(ex);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const volData = days.map((d) => (ex.byDay[d]?.volume || 0));
  
  return {
    labels,
    datasets: [
      {
        label: `${t("global.volume")} (kg)`,
        data: volData,
        backgroundColor: primaryColor.value + "33",
        borderColor: primaryColor.value,
        borderWidth: 2,
      },
    ],
  };
}

const scatterChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const point = context.raw;
          return `${point.label}: ${point.y} kg × ${point.x} reps`;
        },
      },
    },
  },
  scales: {
    y: {
      grid: { color: "#2b3553" },
      ticks: { color: "#9A9A9A" },
      title: {
        display: true,
        text: t("exercises.graphs.axis.weightVsReps.y") + " (kg)",
        color: "#9A9A9A",
      },
    },
    x: {
      grid: { color: "#2b3553" },
      ticks: { color: "#9A9A9A", stepSize: 1 },
      title: {
        display: true,
        text: t("exercises.graphs.axis.weightVsReps.x"),
        color: "#9A9A9A",
      },
    },
  },
};

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: {
      grid: { color: "#2b3553" },
      ticks: { color: "#9A9A9A" },
    },
    x: {
      grid: { display: false },
      ticks: { color: "#9A9A9A", maxRotation: 45, minRotation: 45 },
    },
  },
};

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: {
      grid: { color: "#2b3553" },
      ticks: { color: "#9A9A9A" },
      title: {
        display: true,
        text: `${t("exercises.graphs.axis.volumeSession.y")} (kg)`,
        color: "#9A9A9A",
      },
    },
    x: {
      grid: { display: false },
      ticks: { color: "#9A9A9A", maxRotation: 45, minRotation: 45 },
      title: {
        display: true,
        text: t("exercises.graphs.axis.volumeSession.x"),
        color: "#9A9A9A",
      },
    },
  },
};
</script>

<!-- =============================================================================== -->

<template>
  <div class="exercises-page">
    <!-- Header Section -->
    <div class="exercises-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ $t("exercises.title") }}</h1>
          <p class="subtitle">{{ $t("exercises.subtitle") }}</p>
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

    <!-- Search Section -->
    <div class="search-section">
      <input class="search-input" type="text" v-model="search" :placeholder="`🔍 ${$t('exercises.searchFilter')}`" />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t("global.loadingSpinnerText") }}</p>
    </div>

    <div v-else class="exercise-list">
      <div v-for="ex in filteredExercises" :key="ex.id" class="exercise-card">
        <!-- Card Header / Toggle -->
        <button class="card-toggle" @click="expanded[ex.id] = !expanded[ex.id]">
          <span class="exercise-title">{{ ex.title }}</span>
          <span class="toggle-icon">{{ expanded[ex.id] ? "▾" : "▸" }}</span>
        </button>

        <!-- Card Content (Expanded) -->
        <div v-show="expanded[ex.id]" class="card-content">
          <!-- Card Header -->
          <div class="card-header">
            <div class="title-row">
              <h2 class="exercise-title">{{ ex.title }}</h2>
            </div>

            <div class="header-actions">
              <label class="filter-label">{{ $t("global.timeRangeFilter.timeRange") }}</label>
              <select class="filter-select" :value="rangeByExercise[ex.id] || 'all'" @change="(e:any)=> rangeByExercise[ex.id] = (e.target.value as Range)">
                <option v-for="r in ranges" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
          </div>

          <!-- Media and Stats -->
          <div class="media-and-stats">
            <!-- Exercise Video -->
            <div class="thumb" v-if="ex.video_url">
              <video :src="ex.video_url" autoplay loop muted playsinline></video>
            </div>

            <!-- Top Sets -->
            <div class="top-sets inline" v-if="ex.topSets && ex.topSets.length">
              <h3>Top 3 Best Sets</h3>
              <table class="sets-table compact">
                <thead>
                  <tr>
                    <th>{{ $t("global.day") }}</th>
                    <th>kg</th>
                    <th>Reps</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in ex.topSets" :key="`${ex.id}-${s.day}-${s.index}`">
                    <td>{{ s.day }}</td>
                    <td>{{ s.weight || '-' }}</td>
                    <td>{{ s.reps || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="right-section">
              <!-- PR's -->
              <div class="pr-list" v-if="ex.prDistinct && ex.prDistinct.length">
                <h3>{{ $t("exercises.personalRecords") }}</h3>
                <div class="pr-chips">
                  <span v-for="(pr,i) in ex.prDistinct" :key="i" class="pr-chip">{{ (pr.type||'').split('_').join(' ') }}: <strong>{{ pr.value }}</strong></span>
                </div>
              </div>
              <!-- Stats -->
              <div class="exercise-stats">
                <h3>{{ $t("exercises.stats.statsHeader") }}</h3>
                <div class="stat-items">
                  <div class="stat-item">
                    <span class="stat-label">{{ $t("exercises.stats.totalSessions") }}</span>
                    <span class="stat-value">{{ ex.totalSessions || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Graphs -->
          <div class="graphs">
            <div class="graph">
              <h3>{{ $t("exercises.graphs.maxWeight") }}</h3>
              <div class="graph-grid chart-container">
                <Line :data="getMaxWeightOverTimeChartData(ex)" :options="lineChartOptions" />
              </div>
            </div>

            <div class="graph">
              <h3>{{ $t("exercises.graphs.avgVolume") }}</h3>
              <div class="graph-grid chart-container">
                <Line :data="getAvgVolumePerSetChartData(ex)" :options="lineChartOptions" />
              </div>
            </div>

            <div class="graph">
              <h3>{{ $t("exercises.graphs.weightVsReps") }}</h3>
              <div class="graph-grid chart-container">
                <Scatter :data="getWeightVsRepsChartData(ex)" :options="scatterChartOptions" />
              </div>
            </div>

            <div class="graph">
              <h3>{{ $t("exercises.graphs.volumeSession") }}</h3>
              <div class="graph-grid chart-container">
                <Bar :data="getVolumeChartData(ex)" :options="barChartOptions" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.exercises-page {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles */
.exercises-header {
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

/* Search Section */
.search-section {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.search-input {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  width: 100%;
  max-width: 600px;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.search-input:hover,
.search-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; }
.loading-spinner { width: 48px; height: 48px; border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 25%, transparent); border-top-color: var(--color-primary, #10b981); border-radius: 50%; animation: spin 0.9s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

.exercise-list { display: flex; flex-direction: column; gap: 1rem; }
.exercise-card { border: 1px solid var(--border-color); border-radius: 12px; background: var(--bg-card); padding: 1rem; transition: all 0.3s ease; }
.exercise-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); border-color: var(--color-primary, #10b981); }
.card-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); color: var(--text-primary); border: none; padding: 0.6rem 0.75rem; cursor: pointer; border-radius: 8px; }
.card-content { margin-top: 0.75rem; }
.card-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); }
.exercise-title { margin: 0; color: var(--text-primary); font-size: 1.2rem; font-weight: 600; }
.filter-label { color: var(--text-secondary); font-size: 0.85rem; }
.filter-select { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.4rem 0.6rem; }

.media-and-stats { display: grid; grid-template-columns: 200px auto 1fr; gap: 1rem; align-items: start; margin-top: 0.75rem; }
.thumb img { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border-color); }
.thumb video { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border-color); }
.right-section { display: flex; gap: 1rem; }
.pr-list { max-width: 320px; }
.pr-list h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: var(--text-primary); }
.pr-chips { display: flex; flex-direction: column; gap: 0.4rem; }
.pr-chip { background: rgba(245, 158, 11, 0.22); color: #eedebc; border: 2px solid #f59e0b; border-radius: 999px; padding: 0.25rem 0.75rem; font-size: 0.85rem; font-weight: 600; text-align: center; }
.exercise-stats { max-width: 320px; }
.exercise-stats h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: var(--text-primary); }
.stat-items { display: flex; flex-direction: column; gap: 0.4rem; }
.stat-item { display: flex; justify-content: flex-start; align-items: center; gap: 0.5rem; font-size: 0.9rem; }
.stat-label { color: var(--text-secondary); }
.stat-value { color: var(--text-primary); font-weight: 600; }

.graphs { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
.graph h3 { margin: 0 0 0.5rem; font-size: 1rem; color: var(--text-primary); }
.graph-grid { border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem; background: var(--bg-secondary); }
.chart-container { height: 220px; }

.top-sets h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: var(--text-primary); }
.sets-table { width: 100%; border-collapse: collapse; }
.sets-table th, .sets-table td { padding: 0.5rem; border-bottom: 1px solid var(--border-color); text-align: left; color: var(--text-primary); }
.sets-table th { color: var(--text-secondary); font-weight: 500; }
.sets-table.compact { width: auto; max-width: 320px; }
.sets-table.compact th, .sets-table.compact td { padding: 0.25rem 0.4rem; font-size: 0.8rem; }
.sets-table.compact th:nth-child(1), .sets-table.compact td:nth-child(1) { width: 90px; }
.sets-table.compact th:nth-child(2), .sets-table.compact td:nth-child(2) { width: 50px; text-align: right; }
.sets-table.compact th:nth-child(3), .sets-table.compact td:nth-child(3) { width: 60px; text-align: right; }

@media (max-width: 900px) {
  .media-and-stats { grid-template-columns: 1fr; }
  .graphs { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .exercises-page { padding: 1rem; }
  .header-row { flex-direction: column; align-items: flex-start; }
  .header-actions { width: 100%; }
  .search-input { width: 100%; min-width: unset; }
}

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.625rem;
  }
}
</style>
