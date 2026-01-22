<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from "chart.js";
import { bodyMeasurementService } from "../services/api";
import { formatWeight, getWeightUnit, formatDate } from "../utils/formatters";
import { useHevyCache } from "../stores/hevy_cache";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const { t } = useI18n();
const store = useHevyCache();
const router = useRouter();

// Get theme colors from CSS variables
const primaryColor = computed(() => {
  return getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim() || "#10b981";
});

// State
const measurements = ref<any[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const showAddModal = ref(false);
const userHeight = ref(parseFloat(localStorage.getItem("user_height") || "0"));
const bodyFatData = ref<Record<string, number>>(JSON.parse(localStorage.getItem("body_fat_data") || "{}"));

// Collapsible sections state (saved to localStorage)
const expandedSections = ref<Record<string, boolean>>({
  weightProgress: JSON.parse(localStorage.getItem("bodyMeasurements-section-weightProgress") || "true"),
  measurementHistory: JSON.parse(localStorage.getItem("bodyMeasurements-section-measurementHistory") || "true"),
});

// Toggle section and save to localStorage
function toggleSection(section: string) {
  expandedSections.value[section] = !expandedSections.value[section];
  localStorage.setItem(`bodyMeasurements-section-${section}`, JSON.stringify(expandedSections.value[section]));
}

// Chart filter types and state
type Range = "1m" | "3m" | "6m" | "1y" | "all";
const weightProgress_Range = ref<Range>("all");

// New measurement form
const newMeasurement = ref({
  date: new Date().toISOString().split("T")[0],
  weight: null as number | null,
  bodyFat: null as number | null
});

const today = new Date().toISOString().split("T")[0];

// Computed Properties
const userAccount = computed(() => store.userAccount);

const sortedMeasurements = computed(() => {
  return [...measurements.value].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateB - dateA;
  });
});

const currentWeight = computed(() => {
  if (measurements.value.length === 0) return 0;
  const sorted = sortedMeasurements.value;
  return sorted[0]?.weight_kg || 0;
});

const currentWeightFormatted = computed(() => {
  if (currentWeight.value === 0) return "-";
  return `${formatWeight(currentWeight.value)} ${getWeightUnit()}`;
});

const bmiValue = computed(() => {
  if (currentWeight.value === 0 || !userHeight.value || userHeight.value === 0) {
    return "-";
  }
  const result = calculateBMI(currentWeight.value);
  return result;
});

const bmiCategory = computed(() => {
  const bmi = parseFloat(bmiValue.value);
  if (isNaN(bmi) || bmi === 0) return { label: "-", class: "" };
  
  // https://de.wikipedia.org/wiki/Body-Mass-Index, Header: Interpretationen -> Bei Erwachsenen
  if (bmi < 16) return { label: t("bodyMeasurements.bmiCategory.underweightSevere"), class: "underweight" };
  if (bmi < 17) return { label: t("bodyMeasurements.bmiCategory.underweightModerate"), class: "underweight" };
  if (bmi < 18.5) return { label: t("bodyMeasurements.bmiCategory.underweightMild"), class: "underweight" };
  if (bmi < 25) return { label: t("bodyMeasurements.bmiCategory.normal"), class: "normal" };
  if (bmi < 30) return { label: t("bodyMeasurements.bmiCategory.overweight"), class: "overweight" };
  if (bmi < 35) return { label: t("bodyMeasurements.bmiCategory.obesityClassI"), class: "obese" };
  if (bmi < 40) return { label: t("bodyMeasurements.bmiCategory.obesityClassII"), class: "obese" };
  return { label: t("bodyMeasurements.bmiCategory.obesityClassIII"), class: "obese" };
});

const weightTrend = computed(() => {
  if (measurements.value.length < 2) return "-";
  
  const sorted = sortedMeasurements.value;
  const current = sorted[0]?.weight_kg || 0;
  const previous = sorted[1]?.weight_kg || 0;
  const diff = current - previous;
  
  if (Math.abs(diff) < 0.1) return t("global.sw.stable");
  
  const sign = diff > 0 ? "↑" : "↓";
  return `${sign} ${formatWeight(Math.abs(diff))} ${getWeightUnit()}`;
});

const weightChangeFormatted = computed(() => {
  if (measurements.value.length < 2) return "-";
  
  const sorted = [...measurements.value].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  
  const earliest = sorted[0]?.weight_kg || 0;
  const latest = sorted[sorted.length - 1]?.weight_kg || 0;
  const diff = latest - earliest;
  
  const sign = diff > 0 ? "+" : "";
  return `${sign}${formatWeight(diff)} ${getWeightUnit()}`;
});

const earliestDate = computed(() => {
  if (measurements.value.length === 0) {
    console.log("earliestDate: no measurements");
    return "-";
  }
  
  console.log("earliestDate: processing", measurements.value.length, "measurements");
  console.log("First measurement object:", JSON.stringify(measurements.value[0]));
  
  const sorted = [...measurements.value]
    .filter(m => {
      const dateStr = m.date;
      console.log("Checking date field:", { date: m.date, dateStr });
      if (!dateStr) {
        console.log("No date string found");
        return false;
      }
      const dateObj = new Date(dateStr);
      const isValid = !isNaN(dateObj.getTime());
      console.log("Date validation:", dateStr, "-> valid:", isValid);
      return isValid;
    })
    .sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });
  
  if (sorted.length === 0) {
    console.log("No valid dates found in measurements");
    return "-";
  }
  const dateStr = sorted[0].date;
  console.log("Earliest date string:", dateStr, "type:", typeof dateStr);
  const formatted = formatDate(dateStr);
  console.log("Formatted date:", formatted);
  return formatted;
});

const dateRangeText = computed(() => {
  if (measurements.value.length === 0) return "-";
  if (measurements.value.length === 1) return t("global.sw.entry");
  
  const sorted = [...measurements.value].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateA - dateB;
  });
  
  const days = Math.floor(
    (new Date(sorted[sorted.length - 1].date).getTime() - new Date(sorted[0].date).getTime()) 
    / (1000 * 60 * 60 * 24)
  );
  
  if (days < 30) return `${days} ${t("global.sw.days")}`;
  if (days < 365) return `${Math.floor(days / 30)} ${t("global.sw.months")}`;
  return `${Math.floor(days / 365)} ${t("global.sw.years")}`;
});

const canSave = computed(() => {
  return newMeasurement.value.date && newMeasurement.value.weight && newMeasurement.value.weight > 0;
});

// BFP (Body Fat Percentage) Computed
const currentBFP = computed(() => {
  if (measurements.value.length === 0) return "-";
  const latestMeasurement = sortedMeasurements.value[0];
  const latestDate = latestMeasurement?.date;
  const bfp = bodyFatData.value[latestDate];
  return bfp ? `${bfp.toFixed(1)}%` : "-";
});

const bfpTrend = computed(() => {
  if (measurements.value.length < 2) return "-";
  const sorted = sortedMeasurements.value;
  const currentDate = sorted[0]?.date;
  const previousDate = sorted[1]?.date;
  const current = bodyFatData.value[currentDate];
  const previous = bodyFatData.value[previousDate];
  
  if (!current || !previous) return "-";
  
  const diff = current - previous;
  if (Math.abs(diff) < 0.1) return t("global.sw.stable");
  
  const sign = diff > 0 ? "↑" : "↓";
  return `${sign} ${Math.abs(diff).toFixed(1)}%`;
});

// FFMI (Fat Free Mass Index) Computed
const currentFFMI = computed(() => {
  if (measurements.value.length === 0 || !userHeight.value) return "-";
  
  const latestMeasurement = sortedMeasurements.value[0];
  const latestDate = latestMeasurement?.date;
  const bfp = bodyFatData.value[latestDate];
  const weightKg = currentWeight.value;
  
  if (!bfp || !weightKg) return "-";
  
  // FFMI = (weight × (1 - body fat %)) / height²
  const heightM = userHeight.value / 100;
  const leanMass = weightKg * (1 - bfp / 100);
  const ffmi = leanMass / (heightM * heightM);
  
  return ffmi.toFixed(1);
});

const ffmiCategory = computed(() => {
  const ffmi = parseFloat(currentFFMI.value);
  if (isNaN(ffmi)) return "-";
  
  // FFMI categories (for men, slightly lower for women)
  if (ffmi < 17) return t("bodyMeasurements.ffmiCategory.belowAverage");
  if (ffmi < 19) return t("bodyMeasurements.ffmiCategory.average");
  if (ffmi < 22) return t("bodyMeasurements.ffmiCategory.aboveAverage");
  if (ffmi < 25) return t("bodyMeasurements.ffmiCategory.excellent");
  return t("bodyMeasurements.ffmiCategory.superior");
});

// Filter helper functions
const getRangeLabel = (range: Range): string => {
  if (range === "all") return t("dashboard.filters.all");
  if (range === "1y") return t("dashboard.filters.oneYear");
  if (range === "6m") return t("dashboard.filters.sixMonths");
  if (range === "3m") return t("dashboard.filters.threeMonths");
  if (range === "1m") return t("dashboard.filters.oneMonth");
  return range;
};

const rangeFilters = [
  { value: "all" as Range, label: () => getRangeLabel("all") },
  { value: "1y" as Range, label: () => getRangeLabel("1y") },
  { value: "6m" as Range, label: () => getRangeLabel("6m") },
  { value: "3m" as Range, label: () => getRangeLabel("3m") },
  { value: "1m" as Range, label: () => getRangeLabel("1m") }
];

// Chart Data
const chartData = computed(() => {
  // Filter by range
  const now = new Date();
  let daysBack = 365 * 10; // default: all (10 years)
  if (weightProgress_Range.value === "1m") daysBack = 30;
  else if (weightProgress_Range.value === "3m") daysBack = 90;
  else if (weightProgress_Range.value === "6m") daysBack = 180;
  else if (weightProgress_Range.value === "1y") daysBack = 365;
  
  const cutoffDate = new Date(now);
  cutoffDate.setDate(cutoffDate.getDate() - daysBack);
  
  const filtered = measurements.value.filter(m => {
    const measurementDate = new Date(m.date);
    return measurementDate >= cutoffDate;
  });
  
  const sorted = [...filtered].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateA - dateB;
  });

  const labels = sorted.map(m => formatDate(m.date));
  const data = sorted.map(m => parseFloat(formatWeight(m.weight_kg)));

  return {
    labels,
    datasets: [
      {
        label: `${t("global.sw.weight")} (${getWeightUnit()})`,
        data,
        borderColor: primaryColor.value,
        backgroundColor: primaryColor.value + '33',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5
      }
    ]
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      mode: "index" as const,
      intersect: false,
      backgroundColor: "rgba(15, 23, 42, 0.95)",
      titleColor: "#f8fafc",
      bodyColor: "#94a3b8",
      borderColor: "rgba(51, 65, 85, 0.6)",
      borderWidth: 1,
      padding: 12,
      callbacks: {
        label: (context: any) => {
          return `${context.parsed.y} ${getWeightUnit()}`;
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: "rgba(51, 65, 85, 0.3)",
        drawBorder: false
      },
      ticks: {
        color: "#94a3b8",
        font: { size: 11 }
      }
    },
    y: {
      beginAtZero: false,
      grid: {
        color: "rgba(51, 65, 85, 0.3)",
        drawBorder: false
      },
      ticks: {
        color: "#94a3b8",
        font: { size: 11 },
        callback: (value: any) => `${value} ${getWeightUnit()}`
      }
    }
  }
}));

// Methods
const loadMeasurements = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    measurements.value = await bodyMeasurementService.getMeasurements();
    // Debug: log first measurement to see structure
    if (measurements.value.length > 0) {
      console.log("First measurement:", measurements.value[0]);
    }
  } catch (err: any) {
    error.value = err.message;
    measurements.value = [];
  } finally {
    isLoading.value = false;
  }
};

const saveMeasurement = async () => {
  if (!canSave.value) return;
  
  try {
    // Save height to localStorage
    localStorage.setItem("user_height", userHeight.value.toString());
    store.setUserHeight(userHeight.value);
    
    // Save body fat percentage if provided
    if (newMeasurement.value.bodyFat && newMeasurement.value.bodyFat > 0 && newMeasurement.value.date) {
      bodyFatData.value[newMeasurement.value.date] = newMeasurement.value.bodyFat;
      localStorage.setItem("body_fat_data", JSON.stringify(bodyFatData.value));
    }
    
    // Convert weight back to kg if user is in lbs mode
    let weightKg = newMeasurement.value.weight!;
    if (getWeightUnit() === "lbs") {
      weightKg = weightKg / 2.20462;
    }
    
    // Post measurement to backend
    await bodyMeasurementService.addMeasurement({
      weight_kg: weightKg,
      date: newMeasurement.value.date
    });
    
    // Reload measurements from backend to ensure UI is in sync
    await loadMeasurements();
    
    closeModal();
  } catch (err: any) {
    console.error("Error saving measurement:", err);
    alert(err.message);
  }
};

const closeModal = () => {
  showAddModal.value = false;
  newMeasurement.value = {
    date: new Date().toISOString().split("T")[0],
    weight: null,
    bodyFat: null
  };
};

const formatDateDisplay = (measurement: any) => {
  return measurement.date ? formatDate(measurement.date) : "-";
};

const formatWeightValue = (weightKg: number) => {
  return `${formatWeight(weightKg)} ${getWeightUnit()}`;
};

// https://de.wikipedia.org/wiki/Body-Mass-Index
const calculateBMI = (weightKg: number) => {
  if (!weightKg || !userHeight.value || userHeight.value === 0) return "-";
  const heightM = userHeight.value / 100;
  const bmi = weightKg / (heightM * heightM);
  return bmi.toFixed(1);
};

const getBodyFat = (date: string) => {
  const bfp = bodyFatData.value[date];
  return bfp ? `${bfp.toFixed(1)}%` : "-";
};

const calculateFFMI = (weightKg: number, date: string) => {
  if (!weightKg || !userHeight.value || userHeight.value === 0) return "-";
  
  const bfp = bodyFatData.value[date];
  if (!bfp) return "-";
  
  const heightM = userHeight.value / 100;
  const leanMass = weightKg * (1 - bfp / 100);
  const ffmi = leanMass / (heightM * heightM);
  
  return ffmi.toFixed(1);
};

const getWeightChange = (index: number) => {
  const sorted = sortedMeasurements.value;
  if (index === sorted.length - 1) return "-";
  
  const current = sorted[index].weight_kg;
  const previous = sorted[index + 1].weight_kg;
  const diff = current - previous;
  
  if (Math.abs(diff) < 0.1) return "—";
  
  const sign = diff > 0 ? "+" : "";
  return `${sign}${formatWeight(diff)} ${getWeightUnit()}`;
};

const getChangeClass = (index: number) => {
  const sorted = sortedMeasurements.value;
  if (index === sorted.length - 1) return "";
  
  const current = sorted[index].weight_kg;
  const previous = sorted[index + 1].weight_kg;
  const diff = current - previous;
  
  if (diff > 0.1) return "weight-increase";
  if (diff < -0.1) return "weight-decrease";
  return "";
};

// Lifecycle
onMounted(async () => {
  await store.fetchUserAccount();
  loadMeasurements();
});
</script>

<!-- =============================================================================== -->

<template>
  <div class="body-measurements">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ t("bodyMeasurements.title") }}</h1>
          <p class="subtitle">{{ t("bodyMeasurements.subtitle") }}</p>
        </div>
        <div class="header-actions">
          <button class="add-btn" @click="showAddModal = true">
            <span>+</span>
            {{ t("bodyMeasurements.addMeasurement") }}
          </button>
          <button class="settings-btn" @click="router.push('/settings')" title="Settings">
            ⚙️
          </button>
          <div v-if="userAccount" class="user-badge" @click="router.push('/profile')" title="View Profile">
            <div class="user-avatar">
              {{ userAccount.username?.[0]?.toUpperCase() || "U" }}
            </div>
            <div class="user-details">
              <strong>{{ userAccount.username }}</strong>
              <span>{{ userAccount.email }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ t("global.loadingSpinnerText") }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button class="btn-secondary" @click="loadMeasurements">{{ t("global.sw.retry") }}</button>
    </div>

    <!-- Main Content -->
    <div v-else class="dashboard-content">
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <!-- Current Weight -->
        <div class="kpi-card">
          <div class="kpi-icon">⚖️</div>
          <div class="kpi-value">{{ currentWeightFormatted }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.currentWeight") }}</div>
          <div class="kpi-meta">{{ weightTrend }}</div>
        </div>

        <!-- BMI -->
        <div class="kpi-card">
          <div class="kpi-icon">📊</div>
          <div class="kpi-value">{{ bmiValue }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.bmi") }}</div>
          <div class="kpi-meta" :class="bmiCategory.class">{{ bmiCategory.label }}</div>
        </div>

        <!-- Body Fat Percentage -->
        <div class="kpi-card">
          <div class="kpi-icon">📉</div>
          <div class="kpi-value">{{ currentBFP }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.bfp") }}</div>
          <div class="kpi-meta">{{ bfpTrend }}</div>
        </div>

        <!-- FFMI -->
        <div class="kpi-card">
          <div class="kpi-icon">💪</div>
          <div class="kpi-value">{{ currentFFMI }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.ffmi") }}</div>
          <div class="kpi-meta">{{ ffmiCategory }}</div>
        </div>

        <!-- Total Entries -->
        <div class="kpi-card">
          <div class="kpi-icon">📝</div>
          <div class="kpi-value">{{ measurements.length }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.totalEntries") }}</div>
          <div class="kpi-meta">{{ dateRangeText }}</div>
        </div>

        <!-- Weight Change -->
        <div class="kpi-card">
          <div class="kpi-icon">📈</div>
          <div class="kpi-value">{{ weightChangeFormatted }}</div>
          <div class="kpi-label">{{ t("bodyMeasurements.weightChange") }}</div>
          <div class="kpi-meta">{{ t("global.sw.since") }} {{ earliestDate }}</div>
        </div>
      </div>

      <!-- Weight Progress Chart -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('weightProgress')">
          <div class="section-title">
            <span class="section-icon">📈</span>
            <h2>{{ t("bodyMeasurements.weightProgress") }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.weightProgress ? "▼" : "▶" }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.weightProgress" class="section-content">
            <div class="charts-grid">
              <div class="chart-container">
                <div class="chart-header">
                  <div class="chart-title-section">
                    <h3>📊 {{ t("bodyMeasurements.weightProgress") }}</h3>
                  </div>
                  <div class="chart-filters">
                    <div class="filter-group">
                      <button 
                        v-for="filter in rangeFilters" 
                        :key="filter.value" 
                        @click="weightProgress_Range = filter.value" 
                        :class="['filter-btn', { active: weightProgress_Range === filter.value }]" 
                        :title="filter.label()"
                      >
                        {{ filter.label() }}
                      </button>
                    </div>
                  </div>
                </div>
                <div class="chart-body">
                  <Line 
                    :key="'weight-' + weightProgress_Range"
                    :data="chartData" 
                    :options="chartOptions" 
                  />
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Measurements List -->
      <div class="dashboard-section">
        <div class="section-header" @click="toggleSection('measurementHistory')">
          <div class="section-title">
            <span class="section-icon">📊</span>
            <h2>{{ t("bodyMeasurements.measurementHistory") }}</h2>
          </div>
          <div class="section-toggle">
            <span class="toggle-icon">{{ expandedSections.measurementHistory ? "▼" : "▶" }}</span>
          </div>
        </div>
        <transition name="expand">
          <div v-if="expandedSections.measurementHistory" class="section-content">
          <div v-if="measurements.length === 0" class="empty-state">
            <p>{{ t("bodyMeasurements.noMeasurements") }}</p>
            <button class="btn-primary" @click="showAddModal = true">
              {{ t("bodyMeasurements.addFirst") }}
            </button>
          </div>

          <div v-else class="measurements-table-container">
            <table class="measurements-table">
              <thead>
                <tr>
                  <th>{{ t("global.sw.date") }}</th>
                  <th>{{ t("global.sw.weight") }}</th>
                  <th>{{ t("bodyMeasurements.bmi") }}</th>
                  <th>{{ t("bodyMeasurements.bfp") }}</th>
                  <th>{{ t("bodyMeasurements.ffmi") }}</th>
                  <th>{{ t("bodyMeasurements.change") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(measurement, index) in sortedMeasurements" :key="measurement.id">
                  <td>{{ formatDateDisplay(measurement) }}</td>
                  <td class="weight-cell">{{ formatWeightValue(measurement.weight_kg) }}</td>
                  <td>{{ calculateBMI(measurement.weight_kg) }}</td>
                  <td>{{ getBodyFat(measurement.date) }}</td>
                  <td>{{ calculateFFMI(measurement.weight_kg, measurement.date) }}</td>
                  <td :class="getChangeClass(index)">{{ getWeightChange(index) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        </transition>
      </div>
    </div>

    <!-- Add Measurement Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ t("bodyMeasurements.addMeasurement") }}</h2>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        
        <div class="modal-body">
          <!-- Add date -->
          <div class="form-group">
            <label>{{ t("global.sw.date") }}</label>
            <input 
              v-model="newMeasurement.date" 
              type="date" 
              :max="today"
              class="form-input"
            />
          </div>

          <!-- Add weight -->
          <div class="form-group">
            <label>{{ t("global.sw.weight") }} ({{ getWeightUnit() }})</label>
            <input 
              v-model.number="newMeasurement.weight" 
              type="number" 
              step="0.1"
              min="0"
              :placeholder="t('bodyMeasurements.enterWeight')"
              class="form-input"
            />
          </div>

          <!-- Add body fat percentage -->
          <div class="form-group">
            <label>{{ t("bodyMeasurements.bfp") }}</label>
            <input 
              v-model.number="newMeasurement.bodyFat" 
              type="number" 
              step="0.1"
              min="0"
              max="100"
              :placeholder="t('bodyMeasurements.enterBodyFat')"
              class="form-input"
            />
            <small>{{ t("bodyMeasurements.bodyFatNote") }}</small>
          </div>

          <!-- User height -->
          <div class="form-group">
            <label>{{ t("global.sw.height") }} (cm)</label>
            <input 
              v-model.number="userHeight" 
              type="number" 
              step="0.1"
              min="0"
              :placeholder="t('bodyMeasurements.enterHeight')"
              class="form-input"
            />
            <small>{{ t("bodyMeasurements.heightNote") }}</small>
          </div>
        </div>

        <!-- Footer with buttons -->
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal">
            {{ t("global.sw.cancel") }}
          </button>
          <button class="btn-primary" @click="saveMeasurement" :disabled="!canSave">
            {{ t("global.sw.save") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- =============================================================================== -->

<style scoped>
/* Match Dashboard styling */
.body-measurements {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles - Match Dashboard.vue */
.dashboard-header {
  margin-bottom: 1.5rem;
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

.add-btn {
  padding: 0.75rem 1.5rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9375rem;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
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
  cursor: pointer;
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
  
  .dashboard-header {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
  }
  
  .header-content {
    gap: 0rem;
  }
}

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.625rem;
  }
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid color-mix(in srgb, var(--color-primary, #10b981) 25%, transparent);
  border-top-color: var(--color-primary, #10b981);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-container p {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  /* margin-bottom: 1.5rem; */
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

.kpi-meta {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  opacity: 0.8;
}

.kpi-meta.underweight { color: #f59e0b; }
.kpi-meta.normal { color: #10b981; }
.kpi-meta.overweight { color: #f59e0b; }
.kpi-meta.obese { color: #ef4444; }

/* Dashboard Sections - Match Dashboard.vue */
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

/* Expand/Collapse Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* Charts Grid - Match Dashboard.vue */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

/* Chart Container - Match Dashboard.vue */
.chart-container {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.6);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-container:hover {
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
}

.chart-header {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
}

.chart-title-section {
  flex: 1;
  min-width: 0;
}

.chart-title-section h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 0.375rem;
  background: rgba(30, 41, 59, 0.6);
  padding: 0.25rem;
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.6);
}

.filter-btn {
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-btn:hover {
  background: rgba(148, 163, 184, 0.1);
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--color-primary, #10b981);
  color: white;
  border-color: var(--color-primary, #10b981);
}

.chart-body {
  padding: 1.5rem;
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Measurements Table Section */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text-secondary);
}

.empty-state button {
  margin-top: 1rem;
}

/* Table Styling */
.measurements-table-container {
  overflow-x: auto;
  border-radius: 8px;
}

.measurements-table {
  width: 100%;
  border-collapse: collapse;
}

.measurements-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
}

.measurements-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.measurements-table tbody tr {
  transition: background 0.2s;
}

.measurements-table tbody tr:hover {
  background: rgba(148, 163, 184, 0.05);
}

.weight-cell {
  font-weight: 600;
  color: var(--color-primary);
}

.weight-increase {
  color: #10b981;
  font-weight: 600;
}

.weight-decrease {
  color: #ef4444;
  font-weight: 600;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  transition: background 0.2s;
}

.modal-close:hover {
  background: rgba(148, 163, 184, 0.1);
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.form-group small {
  display: block;
  margin-top: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.8125rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-primary);
  font-size: 1rem;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9375rem;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.1);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: rgba(148, 163, 184, 0.15);
  border-color: var(--color-primary, #10b981);
}

.modal-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

/* Responsive */
@media (max-width: 768px) {
  .body-measurements {
    padding: 1rem 0.5rem;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .chart-body {
    height: 280px;
    padding: 1rem;
  }

  .measurements-table {
    font-size: 0.8125rem;
  }

  .measurements-table th,
  .measurements-table td {
    padding: 0.5rem;
  }
}

@media (max-width: 640px) {
  .body-measurements {
    padding: 0.5rem;
  }
}

@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
