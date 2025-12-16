<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useHevyCache } from "../stores/hevy_cache";
import { Line, Doughnut, Radar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
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
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

const store = useHevyCache();
const chartData = ref<any>(null);

const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);
const userAccount = computed(() => store.userAccount);
const workouts = computed(() => store.workouts);

// ---------- Individual Chart Range Filters ----------
type Range = "1m" | "3m" | "6m" | "1y" | "all";
type DisplayStyle = "mo" | "wk";

const hoursTrained_Range = ref<Range>("6m");
const hoursTrained_Display = ref<DisplayStyle>("mo");

const volumeProgression_Range = ref<Range>("6m");
const volumeProgression_Display = ref<DisplayStyle>("mo");

const repsAndSets_Range = ref<Range>("6m");
const repsAndSets_Display = ref<DisplayStyle>("mo");

const range = ref<Range>("6m");

const muscleDistribution_Range = ref<Range>("all");
  
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
    labels: agg.map(w => w.period),
    data: agg.map(w => Number(((w.durationMin ?? 0) / 60).toFixed(2)))
  };
});

// Volume per week/month
const volumeProgression_Data = computed(() => {
  const filtered = filterByRange(volumeProgression_Range.value);
  const agg = aggregateByPeriod(volumeProgression_Range.value, volumeProgression_Display.value, filtered);
  return {
    labels: agg.map(w => w.period),
    data: agg.map(w => Math.round(w.volumeKg ?? 0))
  };
});

// Reps/Sets per week/month
const repsAndSets_Data = computed(() => {
  const filtered = filterByRange(repsAndSets_Range.value);
  const agg = aggregateByPeriod(repsAndSets_Range.value, repsAndSets_Display.value, filtered);
  return {
    labels: agg.map(w => w.period),
    reps: agg.map(w => w.reps ?? 0),
    sets: agg.map(w => w.sets ?? 0)
  };
});
// Weekly Rhythm - Distribution across days of week
const weeklyRhythm_Data = computed(() => {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
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

// Muscle Distribution
const muscleDistribution_Data = computed(() => {
  const filtered = filterByRange(muscleDistribution_Range.value);
  const muscleGroups: { [key: string]: number } = {};
  
  for (const w of filtered) {
    for (const ex of (w.exercises || [])) {
      const muscleGroup = ex.muscle_group || "Unknown";
      const setsCount = ex.sets?.length || 0;
      muscleGroups[muscleGroup] = (muscleGroups[muscleGroup] || 0) + setsCount;
    }
  }
  
  return {
    labels: Object.keys(muscleGroups),
    data: Object.values(muscleGroups)
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
const totalVolume = computed(() =>
  workouts.value.reduce((sum, w) => sum + (w.estimated_volume_kg || 0), 0)
);
const avgVolume = computed(() =>
  totalWorkouts.value > 0 ? Math.round(totalVolume.value / totalWorkouts.value) : 0
);

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
    volumes.push(workout.estimated_volume_kg || 0);
  });

  chartData.value = {
    labels: dates.reverse(),
    datasets: [
      {
        label: "Volume (kg)",
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
          <h1>Dashboard</h1>
          <p v-if="userAccount" class="subtitle">Welcome back, {{ userAccount.username }}!</p>
        </div>

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

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your workout data...</p>
    </div>

    <!-- Main Content -->
    <div v-else class="dashboard-content">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon workout-icon">🏋️</div>
          <div class="stat-content">
            <div class="stat-value">{{ totalWorkouts }}</div>
            <div class="stat-label">Total Workouts</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon volume-icon">💪</div>
          <div class="stat-content">
            <div class="stat-value">{{ totalVolume.toLocaleString() }}</div>
            <div class="stat-label">Total Volume (kg)</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon avg-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ avgVolume.toLocaleString() }}</div>
            <div class="stat-label">Avg Volume (kg)</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⏳</div>
          <div class="stat-content">
            <div class="stat-value">{{ totalHoursAll }}</div>
            <div class="stat-label">Total Hours Trained</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🔥</div>
          <div class="stat-content">
            <div class="stat-value">{{ workoutStreakWeeks }}</div>
            <div class="stat-label">Workout Streak (Weeks)</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🏆</div>
          <div class="stat-content">
            <div class="stat-value">{{ mostTrainedExercise.name }}</div>
            <div class="stat-label">Most Trained Exercise</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-content">
            <div class="stat-value">{{ longestWorkout.minutes }} min</div>
            <div class="stat-label">Longest Workout</div>
          </div>
        </div>
      </div>

      <!-- Charts Section - 2 Column Grid -->
      <div class="charts-grid">
        <!-- Hours Trained Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title-section">
              <h2>⏳ Hours Trained</h2>
              <span class="chart-subtitle">Your training duration over time</span>
            </div>
            <div class="chart-filters">
              <div class="filter-group">
                <button @click="hoursTrained_Range = 'all'" :class="['filter-btn', { active: hoursTrained_Range === 'all' }]" title="All Time">All</button>
                <button @click="hoursTrained_Range = '1y'" :class="['filter-btn', { active: hoursTrained_Range === '1y' }]" title="1 Year">1Y</button>
                <button @click="hoursTrained_Range = '6m'" :class="['filter-btn', { active: hoursTrained_Range === '6m' }]" title="6 Months">6M</button>
                <button @click="hoursTrained_Range = '3m'" :class="['filter-btn', { active: hoursTrained_Range === '3m' }]" title="3 Months">3M</button>
                <button @click="hoursTrained_Range = '1m'" :class="['filter-btn', { active: hoursTrained_Range === '1m' }]" title="1 Month">1M</button>
              </div>
              <div class="filter-group">
                <button @click="hoursTrained_Display = 'mo'" :class="['filter-btn', { active: hoursTrained_Display === 'mo' }]" title="Monthly">Mo</button>
                <button @click="hoursTrained_Display = 'wk'" :class="['filter-btn', { active: hoursTrained_Display === 'wk' }]" title="Weekly">Wk</button>
              </div>
            </div>
          </div>
          <div class="chart-body">
            <Line 
              :key="'hours-' + hoursTrained_Range" 
              :data="{ 
                labels: hoursTrained_Data.labels, 
                datasets: [{ 
                  label: 'Hours', 
                  data: hoursTrained_Data.data, 
                  borderColor: '#10b981', 
                  backgroundColor: 'rgba(16,185,129,0.2)', 
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
              <h2>💪 Volume Progression</h2>
              <span class="chart-subtitle">Total weight lifted per period</span>
            </div>
            <div class="chart-filters">
              <div class="filter-group">
                <button @click="volumeProgression_Range = 'all'" :class="['filter-btn', { active: volumeProgression_Range === 'all' }]" title="All Time">All</button>
                <button @click="volumeProgression_Range = '1y'" :class="['filter-btn', { active: volumeProgression_Range === '1y' }]" title="1 Year">1Y</button>
                <button @click="volumeProgression_Range = '6m'" :class="['filter-btn', { active: volumeProgression_Range === '6m' }]" title="6 Months">6M</button>
                <button @click="volumeProgression_Range = '3m'" :class="['filter-btn', { active: volumeProgression_Range === '3m' }]" title="3 Months">3M</button>
                <button @click="volumeProgression_Range = '1m'" :class="['filter-btn', { active: volumeProgression_Range === '1m' }]" title="1 Month">1M</button>
              </div>
              <div class="filter-group">
                <button @click="volumeProgression_Display = 'mo'" :class="['filter-btn', { active: volumeProgression_Display === 'mo' }]" title="Monthly">Mo</button>
                <button @click="volumeProgression_Display = 'wk'" :class="['filter-btn', { active: volumeProgression_Display === 'wk' }]" title="Weekly">Wk</button>
              </div>
            </div>
          </div>
          <div class="chart-body">
            <Line 
              :key="'volume-' + volumeProgression_Range" 
              :data="{ 
                labels: volumeProgression_Data.labels, 
                datasets: [{ 
                  label: 'Volume (kg)', 
                  data: volumeProgression_Data.data, 
                  borderColor: '#06b6d4', 
                  backgroundColor: 'rgba(6,182,212,0.2)', 
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
              <h2>📊 Reps & Sets</h2>
              <span class="chart-subtitle">Training volume breakdown</span>
            </div>
            <div class="chart-filters">
              <div class="filter-group">
                <button @click="repsAndSets_Range = 'all'" :class="['filter-btn', { active: repsAndSets_Range === 'all' }]" title="All Time">All</button>
                <button @click="repsAndSets_Range = '1y'" :class="['filter-btn', { active: repsAndSets_Range === '1y' }]" title="1 Year">1Y</button>
                <button @click="repsAndSets_Range = '6m'" :class="['filter-btn', { active: repsAndSets_Range === '6m' }]" title="6 Months">6M</button>
                <button @click="repsAndSets_Range = '3m'" :class="['filter-btn', { active: repsAndSets_Range === '3m' }]" title="3 Months">3M</button>
                <button @click="repsAndSets_Range = '1m'" :class="['filter-btn', { active: repsAndSets_Range === '1m' }]" title="1 Month">1M</button>
              </div>
              <div class="filter-group">
                <button @click="repsAndSets_Display = 'mo'" :class="['filter-btn', { active: repsAndSets_Display === 'mo' }]" title="Monthly">Mo</button>
                <button @click="repsAndSets_Display = 'wk'" :class="['filter-btn', { active: repsAndSets_Display === 'wk' }]" title="Weekly">Wk</button>
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
                    borderColor: '#8b5cf6', 
                    backgroundColor: 'rgba(139,92,246,0.15)', 
                    fill: true, 
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5
                  },
                  { 
                    label: 'Sets', 
                    data: repsAndSets_Data.sets, 
                    borderColor: '#f59e0b', 
                    backgroundColor: 'rgba(245,158,11,0.15)', 
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

        <div class="chart-container">
          <div class="chart-header">
            <h2>Reps / Sets Per Week</h2>
            <span class="chart-subtitle">Filtered by range</span>
          </div>
          <div class="chart-body">
            <Line :key="'rs-' + range" :data="{ labels: hoursPerWeekLabels, datasets: [
              { label: 'Reps', data: repsPerWeekData, borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.15)', fill: true, tension: 0.3 },
              { label: 'Sets', data: setsPerWeekData, borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.15)', fill: true, tension: 0.3 }
            ] }" :options="chartOptions" />
          </div>
        </div>

        <!-- Weekly Rhythm Radar Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title-section">
              <h2>🔥 Weekly Rhythm</h2>
              <span class="chart-subtitle">Training frequency by day</span>
            </div>
          </div>
          <div class="chart-body radar-body">
            <Radar 
              :data="{ 
                labels: weeklyRhythm_Data.labels, 
                datasets: [{ 
                  label: 'Workouts', 
                  data: weeklyRhythm_Data.data, 
                  borderColor: '#ec4899', 
                  backgroundColor: 'rgba(236,72,153,0.4)', 
                  borderWidth: 3,
                  pointRadius: 4,
                  pointHoverRadius: 6,
                  pointBackgroundColor: '#ec4899',
                  pointBorderColor: '#fff',
                  pointBorderWidth: 2
                }] 
              }" 
              :options="radarOptions" 
            />
          </div>
        </div>

        <!-- Muscle Distribution Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title-section">
              <h2>🎯 Muscle Distribution</h2>
              <span class="chart-subtitle">Sets by muscle group</span>
            </div>
            <div class="chart-filters">
              <div class="filter-group">
                <button @click="muscleDistribution_Range = 'all'" :class="['filter-btn', { active: muscleDistribution_Range === 'all' }]" title="All Time">All</button>
                <button @click="muscleDistribution_Range = '1y'" :class="['filter-btn', { active: muscleDistribution_Range === '1y' }]" title="1 Year">1Y</button>
                <button @click="muscleDistribution_Range = '6m'" :class="['filter-btn', { active: muscleDistribution_Range === '6m' }]" title="6 Months">6M</button>
                <button @click="muscleDistribution_Range = '3m'" :class="['filter-btn', { active: muscleDistribution_Range === '3m' }]" title="3 Months">3M</button>
                <button @click="muscleDistribution_Range = '1m'" :class="['filter-btn', { active: muscleDistribution_Range === '1m' }]" title="1 Month">1M</button>
              </div>
            </div>
          </div>
          <div class="chart-body doughnut-body">
            <Doughnut 
              :key="'muscle-' + muscleDistribution_Range"
              :data="{
                labels: muscleDistribution_Data.labels,
                datasets: [{
                  data: muscleDistribution_Data.data,
                  backgroundColor: [
                    '#10b981',
                    '#06b6d4',
                    '#8b5cf6',
                    '#f59e0b',
                    '#ef4444',
                    '#ec4899',
                    '#14b8a6',
                    '#f97316',
                  ],
                  borderWidth: 0,
                }]
              }" 
              :options="doughnutOptions" 
            />
          </div>
        </div>
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
  background: #0f172a;
}

/* Header Styles */
.dashboard-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(16, 185, 129, 0.15);
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
  color: #f8fafc;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0.5rem 0 0;
  color: #94a3b8;
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
  border: 1px solid rgba(51, 65, 85, 0.5);
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  color: #94a3b8;
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
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  border: 1px solid rgba(16, 185, 129, 0.2);
  transition: all 0.3s ease;
}

.user-badge:hover {
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
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
  color: #f8fafc;
  font-weight: 600;
}

.user-details span {
  font-size: 0.8rem;
  color: #94a3b8;
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

.loading-spinner {
  width: 56px;
  height: 56px;
  border: 4px solid rgba(16, 185, 129, 0.1);
  border-top-color: #10b981;
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

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  padding: 1.25rem 1rem;
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  display: flex;
  align-items: center;
  gap: 0.9rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #10b981, #06b6d4);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 12px 28px rgba(16, 185, 129, 0.15);
  background: rgba(15, 23, 42, 0.9);
}

.stat-card:hover::before {
  opacity: 1;
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
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.chart-container:hover {
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.12);
  transform: translateY(-2px);
}

.chart-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(6, 182, 212, 0.05));
}

.chart-title-section {
  flex: 1;
  min-width: 0;
}

.chart-header h2 {
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

@media (max-width: 768px) {
  .dashboard {
    padding: 1.5rem 1rem;
  }
  
  .title-section h1 {
    font-size: 1.875rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .chart-filters {
    width: 100%;
    justify-content: flex-end;
  }
  
  .chart-body {
    padding: 1rem 0.75rem;
    min-height: 280px;
  }
  
  .doughnut-body,
  .radar-body {
    min-height: 280px;
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: 1rem;
  }
  
  .title-section h1 {
    font-size: 1.625rem;
  }
  
  .subtitle {
    font-size: 0.875rem;
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
  
  .chart-body {
    padding: 1rem 0.5rem;
  }
}
</style>
