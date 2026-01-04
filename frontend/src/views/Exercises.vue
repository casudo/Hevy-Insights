<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useHevyCache } from "../stores/hevy_cache";
import { formatWeight, getWeightUnit, formatPRValue } from "../utils/formatters";
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

// Collapsed state per exercise (default collapsed)
const expanded = ref<Record<string, boolean>>({});
// Search by exercise name
const search = ref("");
// Plateau filter state
const plateauFilter = ref<string | null>(null);

// Graph filters per exercise (stores timeRange and chartType for each graph)
type GraphRange = 30 | 60 | 90 | 365 | 0; // days, 0 = all time
type GraphType = "line" | "bar";
const graphFilters = ref<Record<string, {
  maxWeight: { range: GraphRange, type: GraphType },
  avgVolume: { range: GraphRange, type: GraphType },
  weightVsReps: { range: GraphRange },
  volumeSession: { range: GraphRange, type: GraphType }
}>>({});

// Initialize graph filters for an exercise
function getGraphFilter(exerciseId: string) {
  if (!graphFilters.value[exerciseId]) {
    graphFilters.value[exerciseId] = {
      maxWeight: { range: 0, type: "line" },
      avgVolume: { range: 0, type: "line" },
      weightVsReps: { range: 0 },
      volumeSession: { range: 0, type: "bar" }
    };
  }
  return graphFilters.value[exerciseId];
}

const allWorkouts = computed(() => store.workouts || []);

onMounted(async () => {
  await store.fetchWorkouts();
  
  // Check if there's an exercise ID in the URL hash
  if (window.location.hash) {
    const exerciseId = window.location.hash.substring(1); // Remove # prefix
    // Wait for exercises to be computed
    setTimeout(() => {
      // Expand the exercise
      expanded.value[exerciseId] = true;
      // Scroll to the exercise
      const element = document.getElementById(exerciseId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 300);
  }
});

// Helper function to get localized exercise title
function getLocalizedTitle(exercise: any): string {
  const locale = localStorage.getItem("language") || "en";
  
  // Select localized title if available
  if (locale === "de" && exercise.de_title) {
    return exercise.de_title;
  } else if (locale === "es" && exercise.es_title) {
    return exercise.es_title;
  }
  
  return exercise.title || "Unknown Exercise";
}

// Analyze strength progress based on last 5 sessions
function analyzeStrengthProgress(ex: any) {
  const days = Object.keys(ex.byDay || {}).sort();
  
  // Check if inactive (last session more than 60 days ago) FIRST
  // This should be checked before insufficient data check
  const lastDay = days[days.length - 1];
  if (!lastDay) return null;
  
  const lastDate = new Date(lastDay);
  const daysSinceLastWorkout = Math.floor((Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
  
  if (daysSinceLastWorkout > 60) {
    return {
      type: "inactive",
      message: t("exercises.insights.inactive", {
        days: daysSinceLastWorkout
      })
    };
  }
  
  // Check for insufficient data - need at least the configured number of sessions
  const minSessions = store.plateauDetectionSessions;
  if (days.length < minSessions) {
    return {
      type: "insufficient",
      message: t("exercises.insights.insufficient", {
        sessions: days.length,
        needed: minSessions
      })
    };
  }
  
  // Filter out sessions older than 60 days for analysis
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 60);
  const recentDays = days.filter(d => new Date(d) >= cutoffDate);
  
  // Need at least the configured number of recent sessions for analysis
  if (recentDays.length < minSessions) {
    return {
      type: "insufficient",
      message: t("exercises.insights.insufficient", {
        sessions: recentDays.length,
        needed: minSessions
      })
    };
  }
  
  // Get last N recent sessions (based on setting)
  const lastNDays = recentDays.slice(-minSessions);
  
  const sessions = lastNDays.map(d => ({
    day: d,
    maxWeight: ex.byDay[d]?.maxWeight || 0,
    repsAtMax: ex.byDay[d]?.repsAtMax || 0,
  }));
  
  // Check for plateau: weight and reps staying within small ranges
  const weights = sessions.map(s => s.maxWeight);
  const reps = sessions.map(s => s.repsAtMax);
  
  const weightRange = Math.max(...weights) - Math.min(...weights);
  const repsRange = Math.max(...reps) - Math.min(...reps);
  const avgWeight = weights.reduce((a, b) => a + b, 0) / weights.length;
  
  // Plateau detection: weight within 0.5kg and reps within 1
  if (weightRange <= 0.5 && repsRange <= 1) {
    return {
      type: "plateau",
      message: t("exercises.insights.plateau", {
        weight: `${formatWeight(avgWeight)} ${getWeightUnit()}`,
        repsMin: Math.min(...reps),
        repsMax: Math.max(...reps)
      })
    };
  }
  
  // Check for strength gain/loss by comparing first half vs second half
  const midpoint = Math.floor(sessions.length / 2);
  const firstHalf = sessions.slice(0, midpoint);
  const secondHalf = sessions.slice(midpoint);
  
  const firstAvgWeight = firstHalf.reduce((a, b) => a + b.maxWeight, 0) / firstHalf.length;
  const secondAvgWeight = secondHalf.reduce((a, b) => a + b.maxWeight, 0) / secondHalf.length;
  
  const firstAvgReps = firstHalf.reduce((a, b) => a + b.repsAtMax, 0) / firstHalf.length;
  const secondAvgReps = secondHalf.reduce((a, b) => a + b.repsAtMax, 0) / secondHalf.length;
  
  const weightChange = secondAvgWeight - firstAvgWeight;
  const repsChange = secondAvgReps - firstAvgReps;
  
  // Strength gain: weight increased by >2kg OR reps increased by >2 with stable/increasing weight
  if (weightChange > 2 || (repsChange > 2 && weightChange >= -0.5)) {
    return {
      type: "gaining",
      message: t("exercises.insights.gaining", {
        weightChange: `${formatWeight(Math.abs(weightChange))} ${getWeightUnit()}`,
        repsChange: Math.abs(repsChange).toFixed(0)
      })
    };
  }
  
  // Strength loss: weight decreased by >2kg OR reps decreased by >2 with stable/decreasing weight
  if (weightChange < -2 || (repsChange < -2 && weightChange <= 0.5)) {
    return {
      type: "losing",
      message: t("exercises.insights.losing", {
        weightChange: `${formatWeight(Math.abs(weightChange))} ${getWeightUnit()}`,
        repsChange: Math.abs(repsChange).toFixed(0)
      })
    };
  }
  
  // Default: maintaining (no significant change detected)
  return {
    type: "maintaining",
    message: t("exercises.insights.maintaining")
  };
}

// Build exercise aggregates across all workouts
const exercises = computed(() => {
  const map: Record<string, any> = {};
  for (const w of allWorkouts.value) {
    const date = new Date((w.start_time || 0) * 1000);
    const dayKey = date.toISOString().slice(0,10);
    
    for (const ex of (w.exercises || [])) {
      // Use localized title based on user's language preference
      const title = getLocalizedTitle(ex);
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
    // top 3 best sets by weight × reps (total work) across ALL workouts
    ex.topSets = [...ex.sets]
      .sort((a,b) => {
        const workA = (Number(a.weight)||0) * (Number(a.reps)||0);
        const workB = (Number(b.weight)||0) * (Number(b.reps)||0);
        return workB - workA;
      })
      .slice(0,3);
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
    
    // Get last trained date
    const days = Object.keys(byDay).sort();
    ex.lastTrainedDate = days.length > 0 ? days[days.length - 1] : null;
    
    // Analyze last N sessions for plateaus and strength changes (based on setting)
    ex.strengthInsight = analyzeStrengthProgress(ex);
  }
  // Initialize collapsed state for new items
  for (const ex of list) {
    if (!(ex.id in expanded.value)) expanded.value[ex.id] = false;
  }
  return list;
});

// Filtered by search term and plateau filter
const filteredExercises = computed(() => {
  let filtered = exercises.value;
  
  // Apply search filter
  const q = search.value.trim().toLowerCase();
  if (q) {
    filtered = filtered.filter((ex: any) => (ex.title || "").toLowerCase().includes(q));
  }
  
  // Apply plateau filter
  if (plateauFilter.value) {
    filtered = filtered.filter((ex: any) => ex.strengthInsight?.type === plateauFilter.value);
  }
  
  return filtered;
});

// Exercise statistics
const exerciseStats = computed(() => {
  const total = exercises.value.length;
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 60);
  
  let active = 0;
  let gaining = 0;
  let plateau = 0;
  let losing = 0;
  let maintaining = 0;
  let inactive = 0;
  let insufficient = 0;
  
  for (const ex of exercises.value) {
    // Check if active (trained in last 60 days)
    if (ex.lastTrainedDate) {
      const lastDate = new Date(ex.lastTrainedDate);
      if (lastDate >= cutoffDate) {
        active++;
      }
    }
    
    // Count by insight type
    if (ex.strengthInsight) {
      const type = ex.strengthInsight.type;
      if (type === "gaining") gaining++;
      else if (type === "plateau") plateau++;
      else if (type === "losing") losing++;
      else if (type === "maintaining") maintaining++;
      else if (type === "inactive") inactive++;
      else if (type === "insufficient") insufficient++;
    }
  }
  
  return { total, active, gaining, plateau, losing, maintaining, inactive, insufficient };
});

// Format date for display
function formatLastTrained(dateStr: string | null): string {
  if (!dateStr) return t("exercises.neverTrained");
  const date = new Date(dateStr);
  const now = new Date();
  const daysDiff = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (daysDiff === 0) return t("exercises.lastTrained.today");
  if (daysDiff === 1) return t("exercises.lastTrained.yesterday");
  if (daysDiff < 7) return t("exercises.lastTrained.daysAgo", { days: daysDiff });
  if (daysDiff < 30) {
    const weeks = Math.floor(daysDiff / 7);
    return t("exercises.lastTrained.weeksAgo", { weeks });
  }
  if (daysDiff < 365) {
    const months = Math.floor(daysDiff / 30);
    return t("exercises.lastTrained.monthsAgo", { months });
  }
  return date.toLocaleDateString();
}

// Filter days for a specific graph with custom range
function filterGraphDates(ex: any, graphRange: GraphRange): string[] {
  const days = Object.keys(ex.byDay || {});
  if (graphRange === 0) return days.sort();
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - graphRange);
  return days.filter((d) => new Date(d) >= cutoff).sort();
}

// Chart data builders for each exercise
function getWeightVsRepsChartData(ex: any, graphRange: GraphRange = 0) {
  const days = filterGraphDates(ex, graphRange);
  const scatterData = days.map((d) => {
    const date = new Date(d);
    const dateLabel = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    return {
      x: ex.byDay[d]?.repsAtMax || 0,
      y: store.weightUnit === "lbs" ? (ex.byDay[d]?.maxWeight || 0) * 2.20462 : (ex.byDay[d]?.maxWeight || 0),
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

function getMaxWeightOverTimeChartData(ex: any, graphRange: GraphRange = 0) {
  const days = filterGraphDates(ex, graphRange);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const weightData = days.map((d) => {
    const kg = ex.byDay[d]?.maxWeight || 0;
    return store.weightUnit === "lbs" ? kg * 2.20462 : kg;
  });
  
  return {
    labels,
    datasets: [
      {
        label: `${t("exercises.graphs.labels.maxWeight")} (${getWeightUnit()})`,
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

function getAvgVolumePerSetChartData(ex: any, graphRange: GraphRange = 0) {
  const days = filterGraphDates(ex, graphRange);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const avgVolData = days.map((d) => {
    const kg = ex.byDay[d]?.avgVolumePerSet || 0;
    return Math.round(store.weightUnit === "lbs" ? kg * 2.20462 : kg);
  });
  
  return {
    labels,
    datasets: [
      {
        label: `${t("exercises.graphs.labels.avgVolume")} (${getWeightUnit()})`,
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

function getVolumeChartData(ex: any, graphRange: GraphRange = 0) {
  const days = filterGraphDates(ex, graphRange);
  const labels = days.map((d) => {
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  });
  const volData = days.map((d) => {
    const kg = ex.byDay[d]?.volume || 0;
    return store.weightUnit === "lbs" ? kg * 2.20462 : kg;
  });
  
  return {
    labels,
    datasets: [
      {
        label: `${t("global.volume")} (${getWeightUnit()})`,
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
          return `${point.label}: ${formatWeight(point.y)} ${getWeightUnit()} × ${point.x} reps`;
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
        text: t("exercises.graphs.axis.weightVsReps.y") + ` (${getWeightUnit()})`,
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
        text: `${t("exercises.graphs.axis.volumeSession.y")} (${getWeightUnit()})`,
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
    <div v-if="!loading" class="search-section">
      <input class="search-input" type="text" v-model="search" :placeholder="`🔍 ${$t('exercises.searchFilter')}`" />
      
      <!-- Exercise Statistics Summary -->
      <div class="exercise-stats-summary">
        <div 
          class="stat-pill clickable"
          :class="{ selected: plateauFilter === null }"
          @click="plateauFilter = null"
        >
          <span class="stat-label">{{ $t("exercises.summary.total") }}:</span>
          <span class="stat-value">{{ exerciseStats.total }}</span>
        </div>
        <div class="stat-pill stat-active">
          <span class="stat-label">{{ $t("exercises.summary.active") }}:</span>
          <span class="stat-value">{{ exerciseStats.active }}</span>
        </div>
        <div 
          class="stat-pill stat-gaining clickable" 
          v-if="exerciseStats.gaining > 0"
          :class="{ selected: plateauFilter === 'gaining' }"
          @click="plateauFilter = plateauFilter === 'gaining' ? null : 'gaining'"
        >
          <span class="stat-icon">📈</span>
          <span class="stat-value">{{ exerciseStats.gaining }}</span>
        </div>
        <div 
          class="stat-pill stat-plateau clickable" 
          v-if="exerciseStats.plateau > 0"
          :class="{ selected: plateauFilter === 'plateau' }"
          @click="plateauFilter = plateauFilter === 'plateau' ? null : 'plateau'"
        >
          <span class="stat-icon">⏸️</span>
          <span class="stat-value">{{ exerciseStats.plateau }}</span>
        </div>
        <div 
          class="stat-pill stat-losing clickable" 
          v-if="exerciseStats.losing > 0"
          :class="{ selected: plateauFilter === 'losing' }"
          @click="plateauFilter = plateauFilter === 'losing' ? null : 'losing'"
        >
          <span class="stat-icon">📉</span>
          <span class="stat-value">{{ exerciseStats.losing }}</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t("global.loadingSpinnerText") }}</p>
    </div>

    <div v-else class="exercise-list">
      <div v-for="ex in filteredExercises" :key="ex.id" :id="ex.id" class="exercise-card">
        <!-- Card Header / Toggle -->
        <button class="card-toggle" @click="expanded[ex.id] = !expanded[ex.id]">
          <div class="toggle-left">
            <div class="exercise-title-container">
              <span class="exercise-title">{{ ex.title }}</span>
              <span class="last-trained-date">{{ formatLastTrained(ex.lastTrainedDate) }}</span>
            </div>
            <!-- Strength Insight Badge -->
            <div v-if="ex.strengthInsight" class="insight-badge-container">
              <span 
                class="insight-badge" 
                :class="ex.strengthInsight.type"
              >
                <span v-if="ex.strengthInsight.type === 'plateau'" class="insight-icon">⏸️</span>
                <span v-else-if="ex.strengthInsight.type === 'gaining'" class="insight-icon">📈</span>
                <span v-else-if="ex.strengthInsight.type === 'losing'" class="insight-icon">📉</span>
                <span v-else-if="ex.strengthInsight.type === 'insufficient'" class="insight-icon">ℹ️</span>
                <span v-else-if="ex.strengthInsight.type === 'inactive'" class="insight-icon">🚫</span>
                <span v-else-if="ex.strengthInsight.type === 'maintaining'" class="insight-icon">➡️</span>
                <span class="insight-text">{{ 
                  ex.strengthInsight.type === "plateau" ? $t("exercises.insights.plateauBadge") :
                  ex.strengthInsight.type === "gaining" ? $t("exercises.insights.gainingBadge") :
                  ex.strengthInsight.type === "losing" ? $t("exercises.insights.losingBadge") :
                  ex.strengthInsight.type === "inactive" ? $t("exercises.insights.inactiveBadge") :
                  ex.strengthInsight.type === "maintaining" ? $t("exercises.insights.maintainingBadge") :
                  $t("exercises.insights.insufficientBadge")
                }}</span>
              </span>
            </div>
          </div>
          <span class="toggle-icon">{{ expanded[ex.id] ? "▾" : "▸" }}</span>
        </button>

        <!-- Card Content (Expanded) -->
        <div v-show="expanded[ex.id]" class="card-content">
          <!-- Plateau Insight Message -->
          <div v-if="ex.strengthInsight" class="insight-message" :class="ex.strengthInsight.type">
            {{ ex.strengthInsight.message }}
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
                    <th>{{ getWeightUnit() }}</th>
                    <th>Reps</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in ex.topSets" :key="`${ex.id}-${s.day}-${s.index}`">
                    <td>{{ s.day }}</td>
                    <td>{{ s.weight ? formatWeight(s.weight) : '-' }}</td>
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
                  <span v-for="(pr,i) in ex.prDistinct" :key="i" class="pr-chip">{{ (pr.type||'').split('_').join(' ') }}: <strong>{{ formatPRValue(pr.type, pr.value) }}</strong></span>
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
            <!-- Max Weight Over Time -->
            <div class="graph">
              <div class="graph-header">
                <h3>{{ $t("exercises.graphs.maxWeight") }}</h3>
                <div class="graph-controls">
                  <div class="range-selector">
                    <button
                      v-for="range in [30, 60, 90, 365, 0]"
                      :key="range"
                      :class="['range-btn', { active: getGraphFilter(ex.id).maxWeight.range === range }]"
                      @click="getGraphFilter(ex.id).maxWeight.range = range as GraphRange"
                    >
                      {{ range === 0 ? 'All' : range === 365 ? '1Y' : `${range}D` }}
                    </button>
                  </div>
                  <div class="type-selector">
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).maxWeight.type === 'line' }]"
                      @click="getGraphFilter(ex.id).maxWeight.type = 'line'"
                      title="Line chart"
                    >📈</button>
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).maxWeight.type === 'bar' }]"
                      @click="getGraphFilter(ex.id).maxWeight.type = 'bar'"
                      title="Bar chart"
                    >📊</button>
                  </div>
                </div>
              </div>
              <div class="graph-grid chart-container">
                <Line
                  v-if="getGraphFilter(ex.id).maxWeight.type === 'line'"
                  :data="getMaxWeightOverTimeChartData(ex, getGraphFilter(ex.id).maxWeight.range)"
                  :options="lineChartOptions"
                />
                <Bar
                  v-else
                  :data="getMaxWeightOverTimeChartData(ex, getGraphFilter(ex.id).maxWeight.range)"
                  :options="barChartOptions"
                />
              </div>
            </div>

            <!-- Average Volume Per Set -->
            <div class="graph">
              <div class="graph-header">
                <h3>{{ $t("exercises.graphs.avgVolume") }}</h3>
                <div class="graph-controls">
                  <div class="range-selector">
                    <button
                      v-for="range in [30, 60, 90, 365, 0]"
                      :key="range"
                      :class="['range-btn', { active: getGraphFilter(ex.id).avgVolume.range === range }]"
                      @click="getGraphFilter(ex.id).avgVolume.range = range as GraphRange"
                    >
                      {{ range === 0 ? 'All' : range === 365 ? '1Y' : `${range}D` }}
                    </button>
                  </div>
                  <div class="type-selector">
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).avgVolume.type === 'line' }]"
                      @click="getGraphFilter(ex.id).avgVolume.type = 'line'"
                      title="Line chart"
                    >📈</button>
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).avgVolume.type === 'bar' }]"
                      @click="getGraphFilter(ex.id).avgVolume.type = 'bar'"
                      title="Bar chart"
                    >📊</button>
                  </div>
                </div>
              </div>
              <div class="graph-grid chart-container">
                <Line
                  v-if="getGraphFilter(ex.id).avgVolume.type === 'line'"
                  :data="getAvgVolumePerSetChartData(ex, getGraphFilter(ex.id).avgVolume.range)"
                  :options="lineChartOptions"
                />
                <Bar
                  v-else
                  :data="getAvgVolumePerSetChartData(ex, getGraphFilter(ex.id).avgVolume.range)"
                  :options="barChartOptions"
                />
              </div>
            </div>

            <!-- Weight vs Reps Scatter -->
            <div class="graph">
              <div class="graph-header">
                <h3>{{ $t("exercises.graphs.weightVsReps") }}</h3>
                <div class="graph-controls">
                  <div class="range-selector">
                    <button
                      v-for="range in [30, 60, 90, 365, 0]"
                      :key="range"
                      :class="['range-btn', { active: getGraphFilter(ex.id).weightVsReps.range === range }]"
                      @click="getGraphFilter(ex.id).weightVsReps.range = range as GraphRange"
                    >
                      {{ range === 0 ? 'All' : range === 365 ? '1Y' : `${range}D` }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="graph-grid chart-container">
                <Scatter :data="getWeightVsRepsChartData(ex, getGraphFilter(ex.id).weightVsReps.range)" :options="scatterChartOptions" />
              </div>
            </div>

            <!-- Volume Per Session -->
            <div class="graph">
              <div class="graph-header">
                <h3>{{ $t("exercises.graphs.volumeSession") }}</h3>
                <div class="graph-controls">
                  <div class="range-selector">
                    <button
                      v-for="range in [30, 60, 90, 365, 0]"
                      :key="range"
                      :class="['range-btn', { active: getGraphFilter(ex.id).volumeSession.range === range }]"
                      @click="getGraphFilter(ex.id).volumeSession.range = range as GraphRange"
                    >
                      {{ range === 0 ? 'All' : range === 365 ? '1Y' : `${range}D` }}
                    </button>
                  </div>
                  <div class="type-selector">
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).volumeSession.type === 'bar' }]"
                      @click="getGraphFilter(ex.id).volumeSession.type = 'bar'"
                      title="Bar chart"
                    >📊</button>
                    <button
                      :class="['type-btn', { active: getGraphFilter(ex.id).volumeSession.type === 'line' }]"
                      @click="getGraphFilter(ex.id).volumeSession.type = 'line'"
                      title="Line chart"
                    >📈</button>
                  </div>
                </div>
              </div>
              <div class="graph-grid chart-container">
                <Bar
                  v-if="getGraphFilter(ex.id).volumeSession.type === 'bar'"
                  :data="getVolumeChartData(ex, getGraphFilter(ex.id).volumeSession.range)"
                  :options="barChartOptions"
                />
                <Line
                  v-else
                  :data="getVolumeChartData(ex, getGraphFilter(ex.id).volumeSession.range)"
                  :options="lineChartOptions"
                />
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
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-row {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
  width: 100%;
}

/* Desktop: horizontal layout with search and stats on same row */
@media (min-width: 769px) {
  .search-section {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
  }
  
  .search-row {
    flex: 1;
    max-width: 600px;
  }
  
  .search-input {
    flex: 1;
    min-width: 250px;
  }
  
  .exercise-stats-summary {
    justify-content: flex-end;
    flex: 1;
  }
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

.exercise-stats-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  align-items: center;
}

.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.stat-pill:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stat-pill .stat-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-pill .stat-value {
  color: var(--text-primary);
  font-weight: 700;
  font-size: 1.05rem;
}

.stat-pill .stat-icon {
  font-size: 1.1rem;
}

.stat-pill.clickable {
  cursor: pointer;
  user-select: none;
}

.stat-pill.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.stat-pill.clickable:active {
  transform: translateY(0);
}

.stat-pill.selected {
  border-width: 2.5px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  transform: scale(1.05);
}

.stat-pill.selected:hover {
  transform: scale(1.05) translateY(-2px);
}

.stat-pill.stat-active {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10b981;
}

.stat-pill.stat-active .stat-value {
  color: #10b981;
}

.stat-pill.stat-gaining {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10b981;
}

.stat-pill.stat-gaining .stat-value {
  color: #10b981;
}

.stat-pill.stat-plateau {
  background: rgba(234, 179, 8, 0.1);
  border-color: #eab308;
}

.stat-pill.stat-plateau .stat-value {
  color: #fbbf24;
}

.stat-pill.stat-losing {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}

.stat-pill.stat-losing .stat-value {
  color: #ef4444;
}

.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; gap: 1rem; }
.loading-spinner { width: 48px; height: 48px; border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 25%, transparent); border-top-color: var(--color-primary, #10b981); border-radius: 50%; animation: spin 0.9s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-container p { color: var(--text-secondary); font-size: 1.1rem; }

.exercise-list { display: flex; flex-direction: column; gap: 1rem; }
.exercise-card { border: 1px solid var(--border-color); border-radius: 12px; background: var(--bg-card); padding: 1rem; transition: all 0.3s ease; }
.exercise-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); border-color: var(--color-primary, #10b981); }
.card-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); color: var(--text-primary); border: none; padding: 0.6rem 0.75rem; cursor: pointer; border-radius: 8px; }
.toggle-left { display: flex; align-items: center; gap: 1rem; flex: 1; }
.exercise-title-container { display: flex; flex-direction: column; align-items: flex-start; gap: 0.25rem; }
.exercise-title { font-size: 1rem; font-weight: 600; }
.last-trained-date { font-size: 0.75rem; color: var(--text-secondary); font-weight: 400; }
.insight-badge-container { display: flex; align-items: center; }
.insight-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.75rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; transition: all 0.2s ease; }
.insight-badge.plateau { background: rgba(234, 179, 8, 0.15); color: #fbbf24; border: 1.5px solid #eab308; }
.insight-badge.gaining { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1.5px solid #10b981; }
.insight-badge.losing { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1.5px solid #ef4444; }
.insight-badge.insufficient { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1.5px solid #64748b; }
.insight-badge.inactive { background: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1.5px solid #6b7280; }
.insight-badge.maintaining { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1.5px solid #3b82f6; }
.insight-icon { font-size: 1rem; line-height: 1; }
.insight-text { font-size: 0.8rem; font-weight: 600; }
.insight-message { padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.9rem; line-height: 1.5; margin: 0.5rem 0; }
.insight-message.plateau { background: rgba(234, 179, 8, 0.12); color: #fbbf24; border-left: 3px solid #eab308; }
.insight-message.gaining { background: rgba(16, 185, 129, 0.12); color: #10b981; border-left: 3px solid #10b981; }
.insight-message.losing { background: rgba(239, 68, 68, 0.12); color: #ef4444; border-left: 3px solid #ef4444; }
.insight-message.insufficient { background: rgba(148, 163, 184, 0.12); color: #94a3b8; border-left: 3px solid #64748b; }
.insight-message.inactive { background: rgba(107, 114, 128, 0.12); color: #9ca3af; border-left: 3px solid #6b7280; }
.insight-message.maintaining { background: rgba(59, 130, 246, 0.12); color: #60a5fa; border-left: 3px solid #3b82f6; }
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
.graph { 
  display: flex; 
  flex-direction: column;
  overflow: hidden; /* Prevent chart overflow */
}
.graph-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 0.5rem; 
  gap: 0.75rem;
  flex-wrap: wrap;
}
.graph h3 { margin: 0; font-size: 1rem; color: var(--text-primary); }
.graph-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}
.range-selector {
  display: flex;
  gap: 0.25rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  padding: 0.125rem;
  border: 1px solid var(--border-color);
}
.range-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}
.range-btn:hover {
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
  color: var(--text-primary);
}
.range-btn.active {
  background: var(--color-primary, #10b981);
  color: white;
}
.type-selector {
  display: flex;
  gap: 0.25rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  padding: 0.125rem;
  border: 1px solid var(--border-color);
}
.type-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.5;
}
.type-btn:hover {
  opacity: 1;
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
}
.type-btn.active {
  opacity: 1;
  background: color-mix(in srgb, var(--color-primary, #10b981) 20%, transparent);
}
.graph-grid { 
  border: 1.5px solid color-mix(in srgb, var(--color-primary, #10b981) 20%, var(--border-color)); 
  border-radius: 12px; 
  padding: 1rem; 
  background: rgba(15, 23, 42, 0.6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}
.graph-grid:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 30%, var(--border-color));
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
}
.chart-container { 
  height: 220px;
  overflow: hidden; /* Prevent overflow on mobile when switching chart types */
}

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
  
  /* Ensure charts don't overflow on mobile */
  .graph-grid {
    overflow-x: auto;
  }
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
