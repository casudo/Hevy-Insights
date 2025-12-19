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

// Reset to default
const resetSettings = () => {
  selectedTheme.value = "default";
  selectedLanguage.value = "en";
  locale.value = "en";
  localStorage.setItem("language", "en");
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
