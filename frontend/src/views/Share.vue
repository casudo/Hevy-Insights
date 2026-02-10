<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useHevyCache } from "../stores/hevy_cache";
import { calculateCSVStats } from "../utils/csvCalculator";
import { getWeightUnit } from "../utils/formatters";
import html2canvas from "html2canvas";

const { t } = useI18n();
const store = useHevyCache();
const router = useRouter();

const userAccount = computed(() => store.userAccount);
const workouts = computed(() => store.workouts);
const loading = computed(() => store.isLoadingWorkouts || store.isLoadingUser);

// CSV mode stats calculation - Match Dashboard.vue
const csvStats = computed(() => {
  if (store.isCSVMode && workouts.value.length > 0) {
    return calculateCSVStats(workouts.value as any);
  }
  return null;
});

// State for image generation
const generating = ref(false);
const shareMessage = ref("");
const previewRef = ref<HTMLElement | null>(null);

// Calculate achievements - Match Dashboard.vue exactly
const totalWorkouts = computed(() => workouts.value.length);

// Total Volume - Match Dashboard.vue: Use API's estimated_volume_kg
const totalVolume = computed(() => {
  if (store.isCSVMode && csvStats.value) {
    return csvStats.value.totalVolume || 0;
  }
  return workouts.value.reduce((sum, w) => sum + (w.estimated_volume_kg || 0), 0);
});

// Total Volume converted to user's preferred unit for display
const totalVolumeDisplay = computed(() => {
  const volumeKg = totalVolume.value;
  if (store.weightUnit === "lbs") {
    return Math.round(volumeKg * 2.20462);
  }
  return Math.round(volumeKg);
});

// Count PRs
const prCount = computed(() => {
  let count = 0;
  for (const w of workouts.value) {
    for (const ex of (w.exercises || [])) {
      for (const s of (ex.sets || [])) {
        const prsArr = Array.isArray(s?.prs) ? s.prs : (s?.prs ? [s.prs] : []);
        const personalArr = Array.isArray(s?.personalRecords) ? s.personalRecords : (s?.personalRecords ? [s.personalRecords] : []);
        count += [...prsArr, ...personalArr].filter(Boolean).length;
      }
    }
  }
  return count;
});

// Total Hours - Match Dashboard.vue calculation
const totalMinutesAll = computed(() => {
  let mins = 0;
  for (const w of workouts.value) {
    const dur = Math.max(0, Math.floor(((w.end_time || w.start_time || 0) - (w.start_time || 0)) / 60));
    mins += dur;
  }
  return mins;
});

const totalHoursAll = computed(() => Number((totalMinutesAll.value / 60).toFixed(2)));

// Most trained exercise
const mostTrainedExercise = computed(() => {
  if (workouts.value.length === 0) return { name: "-", count: 0 };
  const exerciseCount: Record<string, number> = {};
  for (const w of workouts.value) {
    for (const ex of (w.exercises || [])) {
      const title = ex.title || "Unknown";
      exerciseCount[title] = (exerciseCount[title] || 0) + 1;
    }
  }
  let best = "";
  let max = 0;
  for (const [name, count] of Object.entries(exerciseCount)) {
    if (count > max) {
      max = count;
      best = name;
    }
  }
  return { name: best || "-", count: max };
});

// Helper functions - Match Dashboard.vue exactly
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
  // Use local date for week grouping
  return `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, '0')}-${String(m.getDate()).padStart(2, '0')}`;
};

// Workout streak (consecutive weeks with at least 1 workout) - Match Dashboard.vue
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

// Selected card for preview
const selectedCard = ref<string>("workout-streak");

// Year selection for Year Wrapped card
const availableYears = computed(() => {
  const years = new Set<number>();
  for (const w of workouts.value) {
    const year = new Date((w.start_time || 0) * 1000).getFullYear();
    years.add(year);
  }
  return Array.from(years).sort((a, b) => b - a); // Newest first
});

const selectedYear = ref<number>(new Date().getFullYear());

// Filter workouts by selected year for Year Wrapped card
const yearWorkouts = computed(() => {
  return workouts.value.filter(w => {
    const year = new Date((w.start_time || 0) * 1000).getFullYear();
    return year === selectedYear.value;
  });
});

// Year-specific stats
const yearTotalWorkouts = computed(() => yearWorkouts.value.length);

const yearTotalMinutes = computed(() => {
  let mins = 0;
  for (const w of yearWorkouts.value) {
    const dur = Math.max(0, Math.floor(((w.end_time || w.start_time || 0) - (w.start_time || 0)) / 60));
    mins += dur;
  }
  return mins;
});

const yearTotalHours = computed(() => Number((yearTotalMinutes.value / 60).toFixed(2)));

const yearPRCount = computed(() => {
  let count = 0;
  for (const w of yearWorkouts.value) {
    for (const ex of (w.exercises || [])) {
      for (const s of (ex.sets || [])) {
        const prsArr = Array.isArray(s?.prs) ? s.prs : (s?.prs ? [s.prs] : []);
        const personalArr = Array.isArray(s?.personalRecords) ? s.personalRecords : (s?.personalRecords ? [s.personalRecords] : []);
        count += [...prsArr, ...personalArr].filter(Boolean).length;
      }
    }
  }
  return count;
});

const yearWorkoutStreakWeeks = computed(() => {
  const now = new Date();
  const currentYear = now.getFullYear();
  const weeks: Record<string, boolean> = {};
  
  // Mark all weeks that have workouts in the selected year
  for (const w of yearWorkouts.value) {
    const d = new Date((w.start_time || 0) * 1000);
    weeks[weekKey(d)] = true;
  }
  
  let streak = 0;
  // Start from current date if selected year is current year, otherwise from Dec 31 of selected year
  let current = selectedYear.value === currentYear 
    ? startOfWeek(now) 
    : startOfWeek(new Date(selectedYear.value, 11, 31)); // Dec 31 of selected year
  
  // Count backwards only within the selected year
  while (weeks[weekKey(current)] && current.getFullYear() === selectedYear.value) {
    streak++;
    current.setDate(current.getDate() - 7);
  }
  
  return streak;
});

// Card types with localization support
const cardTypes = computed(() => [
  { id: "workout-streak", name: t("share.cards.workoutStreak"), emoji: "🔥", color: "#f59e0b" },
  { id: "total-volume", name: t("share.cards.totalVolume"), emoji: "💪", color: "#10b981" },
  { id: "personal-records", name: t("share.cards.personalRecords"), emoji: "🏆", color: "#8b5cf6" },
  { id: "hours-trained", name: t("share.cards.hoursTrained"), emoji: "⏱️", color: "#3b82f6" },
  { id: "top-exercise", name: t("share.cards.topExercise"), emoji: "🎯", color: "#06b6d4" },
  { id: "year-wrapped", name: t("share.cards.yearWrapped"), emoji: "✨", color: "#ec4899" }
]);

// Generate image/png from preview using html2canvas
const generateImage = async (): Promise<Blob | null> => {
  if (!previewRef.value) return null;
  
  generating.value = true;
  shareMessage.value = "";

  try {
    const canvas = await html2canvas(previewRef.value, {
      backgroundColor: null,
      scale: 2,
      logging: false,
      useCORS: true,
    });

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, "image/png");
    });
  } catch (error) {
    console.error("Failed to generate image:", error);
    shareMessage.value = t("share.generateFailed");
    return null;
  } finally {
    generating.value = false;
  }
};

// Download function
const downloadCard = async () => {
  const blob = await generateImage();
  if (!blob) return;

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `hevy-insights-${selectedCard.value}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  shareMessage.value = t("share.downloaded");
};

const fetchData = async () => {
  await store.fetchWorkouts();
  await store.fetchUserAccount();
  // Initialize selectedYear with the most recent year from available years
  if (availableYears.value.length > 0) {
    selectedYear.value = availableYears.value[0] ?? new Date().getFullYear(); // Most recent year
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="share-page">
    <!-- Header -->
    <div class="share-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ t("share.title") }}</h1>
          <p class="subtitle">{{ t("share.subtitle") }}</p>
        </div>

        <div class="header-actions">
          <!-- Settings Button -->
          <button @click="router.push('/settings')" class="settings-btn">
            ⚙️
          </button>
          
          <!-- User Badge -->
          <div v-if="userAccount" class="user-badge" @click="router.push('/profile')">
            <div class="user-avatar">{{ userAccount.username?.charAt(0).toUpperCase() }}</div>
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
      <p>{{ t("global.loadingSpinnerText") }}</p>
    </div>

    <!-- Content -->
    <div v-else class="share-content">
      <!-- Empty State - No Workouts -->
      <div v-if="totalWorkouts === 0" class="empty-state">
        <div class="empty-icon">📊</div>
        <h2>No workouts yet</h2>
        <p>Start tracking your workouts to create shareable cards!</p>
      </div>

      <!-- Show content when we have workouts -->
      <template v-else>
      <!-- Card Gallery Section -->
      <div class="share-section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-icon">🎨</span>
            <h2>{{ t("share.sections.cardGallery") }}</h2>
          </div>
        </div>
        
        <div class="section-content">
          <div class="card-types-grid">
            <button
              v-for="card in cardTypes"
              :key="card.id"
              @click="selectedCard = card.id"
              :class="['card-type-btn', { active: selectedCard === card.id }]"
              :style="{ '--card-color': card.color }"
            >
              <span class="card-emoji">{{ card.emoji }}</span>
              <span class="card-name">{{ card.name }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Preview & Share Section -->
      <div class="share-section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-icon">👁️</span>
            <h2>{{ t("share.sections.preview") }}</h2>
          </div>
        </div>
        
        <div class="section-content">
            <div class="preview-section">
              <!-- Success Message -->
              <transition name="fade">
                <div v-if="shareMessage" class="share-message">
                  {{ shareMessage }}
                </div>
              </transition>

              <!-- Workout Streak Card -->
              <div v-if="selectedCard === 'workout-streak'" ref="previewRef" class="preview-card streak-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="card-stat">
                    <div class="stat-badge">🔥 {{ t("share.cardLabels.streak") }}</div>
                    <div class="stat-number-wrapper">
                      <div class="stat-number">{{ workoutStreakWeeks }}</div>
                      <div class="stat-unit">{{ t("global.sw.weeks") }}</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-meta">
                      <div class="meta-item">
                        <span class="meta-icon">💪</span>
                        <span class="meta-text">{{ totalWorkouts }} {{ t("share.cardLabels.workouts") }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        <span class="meta-text">{{ totalHoursAll }}h {{ t("share.cardLabels.trained") }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.workoutStreak") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.workoutStreakFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Total Volume Card -->
              <div v-if="selectedCard === 'total-volume'" ref="previewRef" class="preview-card volume-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="card-stat">
                    <div class="stat-badge">💪 {{ t("share.cardLabels.totalVolume") }}</div>
                    <div class="stat-number-wrapper">
                      <div class="stat-number">{{ totalVolume > 0 ? totalVolumeDisplay.toLocaleString() : totalWorkouts }}</div>
                      <div class="stat-unit">{{ totalVolume > 0 ? getWeightUnit() : "workouts" }}</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-meta">
                      <div class="meta-item">
                        <span class="meta-icon">🏋️</span>
                        <span class="meta-text">{{ totalWorkouts }} {{ t("share.cardLabels.sessions")}}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        <span class="meta-text">{{ totalHoursAll }}h {{ t("share.cardLabels.trained")}}</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.strengthInNumbers") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.strengthInNumbersFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Personal Records Card -->
              <div v-if="selectedCard === 'personal-records'" ref="previewRef" class="preview-card pr-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="card-stat">
                    <div class="stat-badge">🏆 {{ t("share.cardLabels.personalRecords") }}</div>
                    <div class="stat-number-wrapper">
                      <div class="stat-number">{{ prCount }}</div>
                      <div class="stat-unit">{{ t("share.cardLabels.prsAchieved") }}</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-meta">
                      <div class="meta-item">
                        <span class="meta-icon">💪</span>
                        <span class="meta-text">{{ totalWorkouts }} {{ t("share.cardLabels.workouts") }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        <span class="meta-text">{{ totalHoursAll }}h {{ t("share.cardLabels.trained") }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.breakingBarriers") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.breakingBarriersFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Hours Trained Card -->
              <div v-if="selectedCard === 'hours-trained'" ref="previewRef" class="preview-card hours-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="card-stat">
                    <div class="stat-badge">⏱️ {{ t("share.cardLabels.timeInvested") }}</div>
                    <div class="stat-number-wrapper">
                      <div class="stat-number">{{ totalHoursAll }}</div>
                      <div class="stat-unit">{{ t("share.cardLabels.hoursTrained") }}</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-meta">
                      <div class="meta-item">
                        <span class="meta-icon">🏋️</span>
                        <span class="meta-text">{{ totalWorkouts }} {{ t("share.cardLabels.sessions") }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-icon">🏆</span>
                        <span class="meta-text">{{ prCount }} {{ t("global.sw.prs") }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.timeWellInvested") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.timeWellInvestedFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Top Exercise Card -->
              <div v-if="selectedCard === 'top-exercise'" ref="previewRef" class="preview-card exercise-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="card-stat">
                    <div class="stat-badge">🎯 {{ t("share.cardLabels.favoriteExercise") }}</div>
                    <div class="exercise-name">{{ mostTrainedExercise.name }}</div>
                    <div class="stat-number-wrapper">
                      <div class="stat-number">{{ mostTrainedExercise.count }}</div>
                      <div class="stat-unit">{{ t("share.cardLabels.timesTrained") }}</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-meta">
                      <div class="meta-item">
                        <span class="meta-icon">💪</span>
                        <span class="meta-text">{{ totalWorkouts }} {{ t("share.cardLabels.totalWorkouts") }}</span>
                      </div>
                      <div class="meta-item">
                        <span class="meta-icon">🏆</span>
                        <span class="meta-text">{{ prCount }} {{ t("global.sw.prs") }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.favoriteMove") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.favoriteMoveFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Year Selector for Year Wrapped Card -->
              <div v-if="selectedCard === 'year-wrapped'" class="year-selector">
                <label for="year-select">{{ t("share.cardLabels.selectYear") }}:</label>
                <select id="year-select" v-model="selectedYear" class="year-select">
                  <option v-for="year in availableYears" :key="year" :value="year">
                    {{ year }}
                  </option>
                </select>
              </div>

              <!-- Year Wrapped Card -->
              <div v-if="selectedCard === 'year-wrapped'" ref="previewRef" class="preview-card wrapped-card">
                <div class="card-background"></div>
                <div class="decorative-circles">
                  <div class="circle circle-1"></div>
                  <div class="circle circle-2"></div>
                  <div class="circle circle-3"></div>
                </div>
                <div class="card-content">
                  <div class="card-header-text">
                    <span class="username">{{ userAccount?.username }}</span>
                    <span class="platform">Hevy Insights</span>
                  </div>
                  <div class="wrapped-header">
                    <div class="wrapped-title">✨ {{ t("share.cardLabels.wrappedTitle", { year: selectedYear }) }}</div>
                    <div class="wrapped-subtitle">{{ t("share.cardLabels.wrappedSubtitle") }}</div>
                  </div>
                  <div class="card-stat-grid-enhanced">
                    <div class="wrapped-stat">
                      <div class="wrapped-emoji">🏋️</div>
                      <div class="wrapped-number">{{ yearTotalWorkouts }}</div>
                      <div class="wrapped-label">{{ t("share.cardLabels.workouts") }}</div>
                    </div>
                    <div class="wrapped-stat">
                      <div class="wrapped-emoji">⏱️</div>
                      <div class="wrapped-number">{{ yearTotalHours }}h</div>
                      <div class="wrapped-label">{{ t("share.cardLabels.trained") }}</div>
                    </div>
                    <div class="wrapped-stat">
                      <div class="wrapped-emoji">🏆</div>
                      <div class="wrapped-number">{{ yearPRCount }}</div>
                      <div class="wrapped-label">{{ t("global.sw.prs") }}</div>
                    </div>
                    <div class="wrapped-stat">
                      <div class="wrapped-emoji">🔥</div>
                      <div class="wrapped-number">{{ yearWorkoutStreakWeeks }}</div>
                      <div class="wrapped-label">{{ t("share.cardLabels.weekStreak") }}</div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <div class="card-footer-text">{{ t("share.cardMottos.yearInReview") }}</div>
                    <div class="card-footer-subtext">{{ t("share.cardMottos.yearInReviewFooter") }}</div>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="action-buttons">
                <button @click="downloadCard" :disabled="generating" class="action-btn download-btn">
                  <span v-if="!generating">📥 {{ t("share.downloadBtn") }}</span>
                  <span v-else>{{ t("share.generating") }}</span>
                </button>
              </div>
            </div>
          </div>
      </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.share-page {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles - Match Dashboard.vue */
.share-header {
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

/* Loading State */
.loading-container {
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

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  gap: 1rem;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-state h2 {
  color: var(--text-primary);
  font-size: 1.5rem;
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 1rem;
  margin: 0;
  max-width: 500px;
}

/* Content */
.share-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Dashboard Sections (Expandable/Collapsible) - Match Dashboard.vue */
.share-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-icon {
  font-size: 1.5rem;
}

.section-title h2 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
  font-weight: 600;
}

.section-content {
  padding: 0 1.5rem 1.5rem;
}

/* Card Types Grid */
.card-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}

.card-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 1rem;
  border-radius: 12px;
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.card-type-btn::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--card-color, var(--color-primary)), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.card-type-btn:hover {
  border-color: var(--card-color, var(--color-primary));
  transform: translateY(-4px);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--card-color, var(--color-primary)) 30%, rgba(0, 0, 0, 0.2));
}

.card-type-btn:hover::before {
  opacity: 0.1;
}

.card-type-btn.active {
  border-color: var(--card-color, var(--color-primary));
  background: color-mix(in srgb, var(--card-color, var(--color-primary)) 10%, var(--bg-card));
  box-shadow: 0 4px 16px color-mix(in srgb, var(--card-color, var(--color-primary)) 30%, transparent);
}

.card-type-btn.active::before {
  opacity: 0.15;
}

.card-emoji {
  font-size: 2.5rem;
  position: relative;
  z-index: 1;
}

.card-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.95rem;
  text-align: center;
  position: relative;
  z-index: 1;
}

/* Preview Section */
.preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.7rem;
}

/* Year Selector */
.year-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
}

.year-selector label {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.95rem;
}

.year-select {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
}

.year-select:hover {
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-primary, #10b981) 20%, transparent);
}

.year-select:focus {
  outline: none;
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary, #10b981) 20%, transparent);
}

/* Success Message */
.share-message {
  padding: 1rem 1.5rem;
  background: color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
  border-radius: 8px;
  color: var(--color-primary, #10b981);
  font-size: 0.95rem;
  text-align: center;
  width: 100%;
  max-width: 600px;
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Preview Cards */
.preview-card {
  width: 100%;
  max-width: 600px;
  aspect-ratio: 1;
  border-radius: 20px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.card-background {
  position: absolute;
  inset: 0;
  opacity: 0.2;
}

.streak-card .card-background {
  background: radial-gradient(circle at 30% 30%, #f59e0b, transparent 70%),
              radial-gradient(circle at 70% 70%, #ef4444, transparent 70%);
}

.volume-card .card-background {
  background: radial-gradient(circle at 30% 30%, #10b981, transparent 70%),
              radial-gradient(circle at 70% 70%, #06b6d4, transparent 70%);
}

.pr-card .card-background {
  background: radial-gradient(circle at 30% 30%, #8b5cf6, transparent 70%),
              radial-gradient(circle at 70% 70%, #ec4899, transparent 70%);
}

.hours-card .card-background {
  background: radial-gradient(circle at 30% 30%, #3b82f6, transparent 70%),
              radial-gradient(circle at 70% 70%, #6366f1, transparent 70%);
}

.exercise-card .card-background {
  background: radial-gradient(circle at 30% 30%, #06b6d4, transparent 70%),
              radial-gradient(circle at 70% 70%, #10b981, transparent 70%);
}

.wrapped-card .card-background {
  background: radial-gradient(circle at 30% 30%, #ec4899, transparent 70%),
              radial-gradient(circle at 70% 70%, #8b5cf6, transparent 70%);
}

/* Decorative circles */
.decorative-circles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -200px;
  right: -200px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -150px;
  left: -150px;
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-width: 3px;
  opacity: 0.5;
}

.card-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.97) 0%, rgba(30, 41, 59, 0.95) 100%);
  backdrop-filter: blur(20px);
}

.card-header-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #94a3b8;
  font-size: 0.95rem;
  margin-bottom: 1rem;
}

.username {
  font-weight: 700;
  color: #f8fafc;
  font-size: 1.1rem;
  letter-spacing: 0.5px;
}

.platform {
  opacity: 0.6;
  color: #cbd5e1;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
}

.card-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
  justify-content: center;
  padding: 1rem 0;
}

.stat-badge {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2));
  border: 2px solid rgba(16, 185, 129, 0.4);
  padding: 0.5rem 1.5rem;
  border-radius: 50px;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #10b981;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

.stat-number-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-number {
  font-size: 5.5rem;
  font-weight: 900;
  color: #10b981;
  line-height: 1;
  text-shadow: 0 0 40px rgba(16, 185, 129, 0.3);
  letter-spacing: -2px;
}

.stat-unit {
  font-size: 1.2rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.stat-divider {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #10b981, transparent);
  border-radius: 2px;
}

.stat-meta {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 50px;
  border: 1px solid rgba(100, 116, 139, 0.3);
}

.meta-icon {
  font-size: 1.2rem;
}

.meta-text {
  font-size: 0.95rem;
  color: #cbd5e1;
  font-weight: 500;
}

.exercise-name {
  font-size: 1.8rem;
  font-weight: 700;
  color: #f8fafc;
  text-align: center;
  padding: 0.5rem 1rem;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(100, 116, 139, 0.3);
  max-width: 90%;
  line-height: 1.3;
}

.card-footer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.card-footer-text {
  text-align: center;
  color: #64748b;
  font-size: 1rem;
  font-style: italic;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.card-footer-subtext {
  text-align: center;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

/* Year Wrapped Card - Enhanced */
.wrapped-header {
  text-align: center;
  margin-bottom: 1rem;
}

.wrapped-title {
  font-size: 2rem;
  font-weight: 900;
  color: #ec4899;
  letter-spacing: 3px;
  text-shadow: 0 0 30px rgba(236, 72, 153, 0.4);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.wrapped-subtitle {
  font-size: 1rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.card-stat-grid-enhanced {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
}

.wrapped-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 1rem;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 16px;
  border: 1px solid rgba(236, 72, 153, 0.3);
  transition: all 0.3s ease;
}

.wrapped-emoji {
  font-size: 2.5rem;
  line-height: 1;
}

.wrapped-number {
  font-size: 2.8rem;
  font-weight: 900;
  color: #ec4899;
  line-height: 1;
  text-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
}

.wrapped-label {
  font-size: 0.85rem;
  color: #94a3b8;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.action-btn {
  padding: 0.875rem 1.75rem;
  border-radius: 12px;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.download-btn {
  background: var(--color-primary, #10b981);
  color: white;
  min-width: 200px;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

/* Responsive Adjustments */
/* Mobile Responsive - Preserve card appearance on all screen sizes */
@media (max-width: 768px) {
  .share-page {
    padding: 1rem 0.3rem;
  }

  .share-header {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
  }

  .user-badge {
    display: none;
  }
  
  .settings-btn {
    display: none;
  }

  .header-content {
    gap: 1rem;
  }

  .title-section h1 {
    font-size: 1.75rem;
  }

  .subtitle {
    font-size: 0.9rem;
  }

  .card-types-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  /* Keep card dimensions consistent on mobile */
  .preview-card {
    width: 100%;
    max-width: 100%;
    aspect-ratio: 1080 / 1920;
    height: auto;
  }

  /* Keep card content proportions the same */
  .card-content {
    padding: 1.5rem 1.25rem;
  }
  
  .stat-badge {
    font-size: 0.75rem;
    padding: 0.4rem 1rem;
  }

  .stat-number {
    font-size: 4rem;
  }

  .stat-unit {
    font-size: 1rem;
  }

  .meta-item {
    font-size: 0.85rem;
    padding: 0.4rem 0.8rem;
  }

  .exercise-name {
    font-size: 1.4rem;
  }

  .card-footer {
    gap: 0.4rem;
  }

  .card-footer-text {
    font-size: 0.85rem;
  }

  .card-footer-subtext {
    font-size: 0.7rem;
  }

  .wrapped-title {
    font-size: 1.5rem;
  }

  .wrapped-subtitle {
    font-size: 0.85rem;
  }

  .wrapped-number {
    font-size: 2.2rem;
  }

  .wrapped-label {
    font-size: 0.75rem;
  }

  /* Keep decorative circles in same proportions */
  .circle-1 {
    width: 300px;
    height: 300px;
    top: -150px;
    right: -150px;
  }

  .circle-2 {
    width: 200px;
    height: 200px;
    bottom: -100px;
    left: -100px;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-btn {
    width: 100%;
  }

  .section-header {
    padding: 1rem;
  }

  .section-content {
    padding: 0 0.3rem 0.3rem;
  }
}

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.5rem;
  }

  .subtitle {
    font-size: 0.85rem;
  }

  .card-type-btn {
    padding: 1.25rem 0.75rem;
  }

  .card-emoji {
    font-size: 2rem;
  }

  .card-name {
    font-size: 0.85rem;
  }

  /* Maintain card appearance on small screens */
  .preview-card {
    width: 100%;
    max-width: 100%;
    aspect-ratio: 1080 / 1920;
    height: auto;
  }

  .card-content {
    padding: 1.5rem 1rem;
  }

  .stat-emoji {
    font-size: 3rem;
  }

  .stat-number {
    font-size: 3rem;
  }

  .stat-label {
    font-size: 1.1rem;
  }

  .stat-subtitle {
    font-size: 0.85rem;
  }

  .card-footer-text {
    font-size: 0.9rem;
  }

  .card-stat-grid {
    gap: 1.5rem;
  }

  .wrapped-emoji {
    font-size: 1.75rem;
  }

  .wrapped-number {
    font-size: 1.75rem;
  }

  .wrapped-label {
    font-size: 0.75rem;
  }

  .action-btn {
    padding: 0.75rem 1.25rem;
    font-size: 0.95rem;
  }
}
</style>
