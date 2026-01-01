<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useHevyCache } from "../stores/hevy_cache";

const store = useHevyCache();
const { locale, t } = useI18n();
const userAccount = computed(() => store.userAccount);
const dataSource = computed(() => store.dataSource);

// Color theme presets
const colorThemes = [
  { 
    name: t("settings.themes.green"), 
    value: "default",
    primary: "#10b981", 
    secondary: "#06b6d4",
    preview: "linear-gradient(135deg, #10b981, #06b6d4)"
  },
  { 
    name: t("settings.themes.purple"), 
    value: "purple",
    primary: "#8b5cf6", 
    secondary: "#ec4899",
    preview: "linear-gradient(135deg, #8b5cf6, #ec4899)"
  },
  { 
    name: t("settings.themes.blue"), 
    value: "blue",
    primary: "#3b82f6", 
    secondary: "#6366f1",
    preview: "linear-gradient(135deg, #3b82f6, #6366f1)"
  },
  { 
    name: t("settings.themes.orange"), 
    value: "orange",
    primary: "#f59e0b", 
    secondary: "#ef4444",
    preview: "linear-gradient(135deg, #f59e0b, #ef4444)"
  },
];

// Load saved settings from localStorage
const selectedTheme = ref<string>(localStorage.getItem("color-theme") || "default");

// Apply theme colors to CSS variables
const applyTheme = (themeValue: string) => {
  const theme = colorThemes.find(t => t.value === themeValue);
  if (theme) {
    document.documentElement.style.setProperty("--color-primary", theme.primary);
    document.documentElement.style.setProperty("--color-secondary", theme.secondary);
  }
};

// Watch for theme changes
watch(selectedTheme, (newTheme) => {
  localStorage.setItem("color-theme", newTheme);
  applyTheme(newTheme);
});

// Apply saved theme on mount
onMounted(() => {
  applyTheme(selectedTheme.value);
});

// Language settings
const languages = [
  { code: "en", name: "English", flag: "🇬🇧" },
  { code: "de", name: "Deutsch", flag: "🇩🇪" },
  { code: "es", name: "Español", flag: "🇪🇸" },
];

const selectedLanguage = ref<string>(localStorage.getItem("language") || "en");

// Watch for language changes
watch(selectedLanguage, (newLang) => {
  locale.value = newLang;
  localStorage.setItem("language", newLang);
});

// Date/Time Format settings
// const dateFormats = [
//   { label: "YYYY-MM-DD (2025-12-21)", value: "iso" },
//   { label: "DD.MM.YYYY (21.12.2025)", value: "eu" },
//   { label: "MM/DD/YYYY (12/21/2025)", value: "us" },
//   { label: "DD/MM/YYYY (21/12/2025)", value: "uk" },
// ];

// const graphAxisFormats = [
//   { label: "YYYY-MM (2025-12)", value: "year-month" },
//   { label: "MM-YYYY (12-2025)", value: "month-year" },
//   { label: "MMM YYYY (Dec 2025)", value: "short" },
//   { label: "Month YYYY (December 2025)", value: "long" },
// ];

const selectedDateFormat = ref<string>(localStorage.getItem("date-format") || "iso");
const selectedGraphAxisFormat = ref<string>(localStorage.getItem("graph-axis-format") || "year-month");

// Watch for format changes
watch(selectedDateFormat, (newFormat) => {
  localStorage.setItem("date-format", newFormat);
});

watch(selectedGraphAxisFormat, (newFormat) => {
  localStorage.setItem("graph-axis-format", newFormat);
});

// Plateau detection settings
const plateauSessions = ref<number>(store.plateauDetectionSessions);

watch(plateauSessions, (newValue) => {
  if (newValue >= 3 && newValue <= 100) {
    store.setPlateauDetectionSessions(newValue);
  }
});

// Reset to default
const resetSettings = () => {
  selectedTheme.value = "default";
  selectedLanguage.value = "en";
  selectedDateFormat.value = "iso";
  selectedGraphAxisFormat.value = "year-month";
  plateauSessions.value = 5;
  locale.value = "en";
  localStorage.setItem("language", "en");
  localStorage.setItem("date-format", "iso");
  localStorage.setItem("graph-axis-format", "year-month");
  store.setPlateauDetectionSessions(5);
};
</script>

<!-- =============================================================================== -->

<template>
  <div class="settings">
    <!-- Header Section -->
    <div class="settings-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ t("settings.title") }}</h1>
          <p class="subtitle">{{ t("settings.subtitle") }}</p>
        </div>

        <div class="header-actions">
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

    <!-- Settings Content -->
    <div class="settings-content">
      <!-- Color Theme Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>🎨 {{ t("settings.themes.title") }}</h2>
          <p class="section-description">{{ t("settings.themes.description") }}</p>
        </div>

        <div class="theme-grid">
          <div
            v-for="theme in colorThemes"
            :key="theme.value"
            @click="selectedTheme = theme.value"
            :class="['theme-card', { active: selectedTheme === theme.value }]"
          >
            <div class="theme-preview" :style="{ background: theme.preview }"></div>
            <div class="theme-info">
              <div class="theme-name">{{ theme.name }}</div>
              <div class="theme-colors">
                <span class="color-dot" :style="{ background: theme.primary }"></span>
                <span class="color-dot" :style="{ background: theme.secondary }"></span>
              </div>
            </div>
            <div v-if="selectedTheme === theme.value" class="theme-check">✓</div>
          </div>
        </div>
      </div>

      <!-- Language Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>🌐 {{ t('settings.language.title') }}</h2>
          <p class="section-description">{{ t('settings.language.description') }}</p>
        </div>

        <div class="language-grid">
          <div
            v-for="lang in languages"
            :key="lang.code"
            @click="selectedLanguage = lang.code"
            :class="['language-card', { active: selectedLanguage === lang.code }]"
          >
            <span class="language-flag">{{ lang.flag }}</span>
            <div class="language-name">{{ lang.name }}</div>
            <div v-if="selectedLanguage === lang.code" class="language-check">✓</div>
          </div>
        </div>
      </div>

      <!-- Date/Time Format Section -->
      <!--  <div class="settings-section">
        <div class="section-header">
          <h2>📅 {{ t("settings.dateTimeFormat.title") }}</h2>
          <p class="section-description">{{ t("settings.dateTimeFormat.description") }}</p>
        </div>

        <div class="format-subsection">
          <h3>{{ t("settings.dateTimeFormat.dateFormat") }}</h3>
          <div class="format-options">
            <label
              v-for="format in dateFormats"
              :key="format.value"
              :class="['format-option', { active: selectedDateFormat === format.value }]"
            >
              <input
                type="radio"
                :value="format.value"
                v-model="selectedDateFormat"
                class="format-radio"
              />
              <span class="format-label">{{ format.label }}</span>
              <div v-if="selectedDateFormat === format.value" class="format-check">✓</div>
            </label>
          </div>
        </div>

        <div class="format-subsection">
          <h3>{{ t("settings.dateTimeFormat.graphAxisFormat") }}</h3>
          <div class="format-options">
            <label
              v-for="format in graphAxisFormats"
              :key="format.value"
              :class="['format-option', { active: selectedGraphAxisFormat === format.value }]"
            >
              <input
                type="radio"
                :value="format.value"
                v-model="selectedGraphAxisFormat"
                class="format-radio"
              />
              <span class="format-label">{{ format.label }}</span>
              <div v-if="selectedGraphAxisFormat === format.value" class="format-check">✓</div>
            </label>
          </div>
        </div>
      </div>  -->

      <!-- Weight Unit Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>⚖️ {{ t('settings.weightUnit.title') }}</h2>
          <p class="section-description">{{ t('settings.weightUnit.description') }}</p>
        </div>

        <div class="weight-unit-options">
          <div
            v-for="unit in weightUnits"
            :key="unit.value"
            @click="selectedWeightUnit = unit.value"
            :class="['weight-unit-card', { active: selectedWeightUnit === unit.value }]"
          >
            <div class="unit-name">{{ unit.label }}</div>
            <div v-if="selectedWeightUnit === unit.value" class="unit-check">✓</div>
          </div>
        </div>
      </div>

      <!-- Plateau Detection Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>📊 {{ t('settings.plateauDetection.title') }}</h2>
          <p class="section-description">{{ t('settings.plateauDetection.description') }}</p>
        </div>

        <div class="plateau-settings">
          <label class="plateau-label">
            {{ t('settings.plateauDetection.sessionsLabel') }}
            <input
              type="number"
              v-model.number="plateauSessions"
              min="3"
              max="100"
              class="plateau-input"
            />
          </label>
          <p class="plateau-hint">{{ t('settings.plateauDetection.hint') }}</p>
        </div>
      </div>

      <!-- Data Management Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>💾 {{ t('settings.dataManagement.title') }}</h2>
          <p class="section-description">{{ t('settings.dataManagement.description') }}</p>
        </div>

        <div class="data-info-card">
          <div class="data-info-row">
            <span class="data-label">{{ t('settings.dataManagement.dataSource') }}</span>
            <span class="data-value" :class="dataSource">
              {{ dataSource === "csv" ? "CSV Upload" : "Hevy API" }}
            </span>
          </div>
          <p v-if="dataSource === 'csv'" class="data-note">
            {{ t('settings.dataManagement.csvNote') }}
          </p>
        </div>
      </div>

      <!-- Actions -->
      <div class="settings-actions">
        <button @click="resetSettings" class="btn-secondary">
          {{ t('settings.resetButton') }}
        </button>
        <button class="btn-primary" @click="$router.push('/dashboard')">
          {{ t('settings.saveButton') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: #0f172a;
}

/* Header Styles */
.settings-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
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

.back-btn {
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

.back-btn:hover {
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
}

/* Settings Content */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  padding: 2rem;
  transition: all 0.3s ease;
}

.settings-section:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0 0 0.5rem;
  color: #f8fafc;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-description {
  margin: 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

/* Theme Grid */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}

.theme-card {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.theme-card:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 50%, transparent);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.theme-card.active {
  border-color: var(--color-primary, #10b981);
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
  box-shadow: 0 0 0 1px var(--color-primary, #10b981) inset;
}

.theme-preview {
  height: 80px;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.theme-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.theme-name {
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 600;
}

.theme-colors {
  display: flex;
  gap: 0.5rem;
}

.color-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.theme-check {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary, #10b981);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-primary, #10b981) 40%, transparent);
}

/* Language Grid */
.language-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.language-card {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.language-card:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 50%, transparent);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.language-card.active {
  border-color: var(--color-primary, #10b981);
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
  box-shadow: 0 0 0 1px var(--color-primary, #10b981) inset;
}

.language-flag {
  font-size: 2rem;
}

.language-name {
  color: #f8fafc;
  font-size: 1rem;
  font-weight: 600;
  flex: 1;
}

.language-check {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary, #10b981);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-primary, #10b981) 40%, transparent);
}
/* Date/Time Format Options */
.format-subsection {
  margin-bottom: 2rem;
}

.format-subsection:last-child {
  margin-bottom: 0;
}

.format-subsection h3 {
  margin: 0 0 1rem;
  color: #f8fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.format-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.format-option {
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(51, 65, 85, 0.5);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.format-option:hover {
  border-color: color-mix(in srgb, var(--color-primary, #10b981) 50%, transparent);
  transform: translateX(4px);
}

.format-option.active {
  border-color: var(--color-primary, #10b981);
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
}

.format-radio {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(148, 163, 184, 0.5);
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.format-radio:checked {
  border-color: var(--color-primary, #10b981);
  background: var(--color-primary, #10b981);
}

.format-radio:checked::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: white;
}

.format-label {
  flex: 1;
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 500;
}

.format-check {
  position: absolute;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
  color: var(--color-primary, #10b981);
  font-weight: 700;
  font-size: 1.2rem;
}
/* Plateau Detection Settings */
.plateau-settings {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
}

.plateau-label {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #f8fafc;
  font-size: 1rem;
  font-weight: 600;
}

.plateau-input {
  width: 80px;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.5);
  border: 2px solid rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  color: #f8fafc;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  transition: all 0.3s ease;
}

.plateau-input:focus {
  outline: none;
  border-color: var(--color-primary, #10b981);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary, #10b981) 20%, transparent);
}

.plateau-hint {
  margin-top: 0.75rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Data Management */
.data-info-card {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
}

.data-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
}

.data-label {
  color: #94a3b8;
  font-size: 0.95rem;
  font-weight: 500;
}

.data-value {
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.7);
}

.data-value.csv {
  background: rgba(6, 182, 212, 0.1);
  border-color: rgba(6, 182, 212, 0.3);
  color: #06b6d4;
}

.data-value.api {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.data-note {
  margin: 1rem 0 0;
  padding: 1rem;
  background: rgba(6, 182, 212, 0.05);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-left: 4px solid #06b6d4;
  border-radius: 8px;
  color: #9dd7e5;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Actions */
.settings-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary, #10b981), var(--color-secondary, #06b6d4));
  color: white;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.btn-secondary {
  background: rgba(51, 65, 85, 0.5);
  color: #94a3b8;
  border: 1px solid rgba(51, 65, 85, 0.5);
}

.btn-secondary:hover {
  background: rgba(51, 65, 85, 0.7);
  color: #f8fafc;
  border-color: rgba(148, 163, 184, 0.5);
}

/* Responsive */
@media (max-width: 768px) {
  .settings {
    padding: 1.5rem 1rem;
  }

  .title-section h1 {
    font-size: 1.875rem;
  }

  .settings-section {
    padding: 1.5rem;
  }

  .theme-grid {
    grid-template-columns: 1fr;
  }

  .language-grid {
    grid-template-columns: 1fr;
  }

  .data-info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .settings-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.625rem;
  }
}
</style>
