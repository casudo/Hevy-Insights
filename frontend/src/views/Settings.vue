<script setup lang="ts">
import { ref, onMounted, watch } from "vue";

// Color theme presets
const colorThemes = [
  { 
    name: "Emerald/Cyan (Default)", 
    value: "default",
    primary: "#10b981", 
    secondary: "#06b6d4",
    preview: "linear-gradient(135deg, #10b981, #06b6d4)"
  },
  { 
    name: "Purple/Pink", 
    value: "purple",
    primary: "#8b5cf6", 
    secondary: "#ec4899",
    preview: "linear-gradient(135deg, #8b5cf6, #ec4899)"
  },
  { 
    name: "Blue/Indigo", 
    value: "blue",
    primary: "#3b82f6", 
    secondary: "#6366f1",
    preview: "linear-gradient(135deg, #3b82f6, #6366f1)"
  },
  { 
    name: "Orange/Red", 
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

// Reset to default
const resetSettings = () => {
  selectedTheme.value = "default";
};
</script>

<!-- =============================================================================== -->

<template>
  <div class="settings">
    <!-- Header Section -->
    <div class="settings-header">
      <div class="header-content">
        <div class="title-section">
          <h1>⚙️ Settings</h1>
          <p class="subtitle">Customize your dashboard experience</p>
        </div>
      </div>
    </div>

    <!-- Settings Content -->
    <div class="settings-content">
      <!-- Color Theme Section -->
      <div class="settings-section">
        <div class="section-header">
          <h2>🎨 Color Theme</h2>
          <p class="section-description">Choose your preferred color scheme for charts and accents</p>
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

      <!-- Actions -->
      <div class="settings-actions">
        <button @click="resetSettings" class="btn-secondary">
          Reset to Default
        </button>
        <button class="btn-primary" @click="$router.push('/dashboard')">
          Save & Return to Dashboard
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
  color: #f8fafc;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subtitle {
  margin: 0.5rem 0 0;
  color: #94a3b8;
  font-size: 1rem;
  font-weight: 400;
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

  .settings-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}
</style>
