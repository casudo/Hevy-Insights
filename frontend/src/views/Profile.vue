<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useHevyCache } from "../stores/hevy_cache";
import { formatDate } from "../utils/formatters";

const { t } = useI18n();
const store = useHevyCache();
const router = useRouter();

// State
const userHeight = ref(parseFloat(localStorage.getItem("user_height") || "0"));
const tempHeight = ref(userHeight.value || 0);
const isSaving = ref(false);
const showSuccessMessage = ref(false);

// Computed
const userAccount = computed(() => store.userAccount);
const loading = computed(() => store.isLoadingUser);

// Save user height
const saveHeight = () => {
  if (tempHeight.value && tempHeight.value > 0) {
    isSaving.value = true;
    
    // Save to localStorage
    localStorage.setItem("user_height", tempHeight.value.toString());
    userHeight.value = tempHeight.value;
    
    // Update Pinia store
    store.setUserHeight(tempHeight.value);
    
    // Show success message
    showSuccessMessage.value = true;
    setTimeout(() => {
      showSuccessMessage.value = false;
      isSaving.value = false;
    }, 2000);
  }
};

const resetHeight = () => {
  tempHeight.value = userHeight.value;
};

// Format birthday date
const formatBirthday = (dateString: string) => {
  if (!dateString) return "-";
  return formatDate(new Date(dateString));
};

onMounted(async () => {
  await store.fetchUserAccount();
});
</script>

<!-- =============================================================================== -->

<template>
  <div class="profile">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1>{{ t('profile.title') }}</h1>
          <p class="subtitle">{{ t('profile.subtitle') }}</p>
        </div>
        <div class="header-actions">
          <button class="settings-btn" @click="router.push('/settings')" title="Settings">
            ⚙️
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ t('profile.loading') }}</p>
    </div>

    <!-- Main Content -->
    <div v-else class="profile-content">
      <!-- Two Column Layout -->
      <div class="profile-grid">
        <!-- User Info Section -->
        <div class="dashboard-section">
          <div class="section-header">
            <div class="section-title">
              <span class="section-icon">👤</span>
              <h2>{{ t('profile.userInfo.title') }}</h2>
            </div>
          </div>
          <div class="section-content">
            <div class="profile-card">
              <div class="profile-avatar-container">
                <img 
                  v-if="userAccount?.profile_pic" 
                  :src="userAccount.profile_pic" 
                  :alt="userAccount.username"
                  class="profile-avatar-large"
                />
                <div v-else class="profile-avatar-large profile-avatar-placeholder">
                  {{ userAccount?.username?.[0]?.toUpperCase() || "U" }}
                </div>
              </div>
              <div class="profile-details">
                <div class="detail-row">
                  <span class="detail-label">{{ t('profile.userInfo.username') }}</span>
                  <span class="detail-value">{{ userAccount?.username || "-" }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">{{ t('profile.userInfo.email') }}</span>
                  <span class="detail-value">{{ userAccount?.email || "-" }}</span>
                </div>
                <div class="detail-row" v-if="userAccount?.birthday">
                  <span class="detail-label">{{ t('profile.userInfo.birthday') }}</span>
                  <span class="detail-value">{{ formatBirthday(userAccount.birthday) }}</span>
                </div>
                <div class="detail-row detail-row-full" v-if="userAccount?.description">
                  <span class="detail-label">{{ t('profile.userInfo.bio') }}</span>
                  <span class="detail-value detail-bio">{{ userAccount.description }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Height Settings Section -->
        <div class="dashboard-section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-icon">📏</span>
            <h2>{{ t('profile.heightSettings.title') }}</h2>
          </div>
        </div>
        <div class="section-content">
          <div class="settings-card">
            <p class="settings-description">
              {{ t('profile.heightSettings.description') }}
            </p>
            
            <div class="form-group">
              <label>{{ t('global.sw.height') }} (cm)</label>
              <div class="input-with-actions">
                <input 
                  v-model.number="tempHeight" 
                  type="number" 
                  step="0.1"
                  min="0"
                  max="250"
                  class="form-input"
                /> <!-- dear god if sultan kösen inputs his height  -->
                <div class="action-buttons">
                  <button 
                    class="btn-secondary" 
                    @click="resetHeight"
                    :disabled="tempHeight === userHeight"
                  >
                    {{ t('global.sw.reset') }}
                  </button>
                  <button 
                    class="btn-primary" 
                    @click="saveHeight"
                    :disabled="!tempHeight || tempHeight <= 0 || tempHeight === userHeight || isSaving"
                  >
                    <span v-if="isSaving">{{ t('profile.heightSettings.saving') }}</span>
                    <span v-else>{{ t('profile.heightSettings.save') }}</span>
                  </button>
                </div>
              </div>
              <small class="help-text">
                {{ t('profile.heightSettings.heightNote') }}
              </small>
            </div>

            <!-- Success Message -->
            <div v-if="showSuccessMessage" class="success-message">
              <span class="success-icon">✓</span>
              {{ t('profile.heightSettings.heightSaved') }}
            </div>

            <!-- Current Value Display -->
            <div class="current-value" v-if="userHeight > 0">
              <span class="value-label">{{ t('profile.heightSettings.currentHeight') }}:</span>
              <span class="value-display">{{ userHeight }} cm</span>
            </div>
            
            <!-- No Height Set Placeholder -->
            <div class="no-height-placeholder" v-else>
              <span class="placeholder-icon">📏</span>
              <span class="placeholder-text">{{ t('profile.heightSettings.noHeightSet') }}</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<!-- =============================================================================== -->

<style scoped>
.profile {
  padding: 1.5rem 1.25rem;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Header Styles */
.dashboard-header {
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

/* Dashboard Section */
.profile-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

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
  background: rgba(30, 41, 59, 0.4);
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
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

.section-content {
  padding: 1.5rem;
}

/* Profile Card */
.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem;
}

.profile-avatar-container {
  width: 100%;
  display: flex;
  justify-content: center;
}

.profile-avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
  flex-shrink: 0;
}

.profile-avatar-placeholder {
  background: linear-gradient(135deg, var(--color-primary, #10b981), var(--color-secondary, #06b6d4));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 2.5rem;
  text-transform: uppercase;
}

.profile-details {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.detail-row-full {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.detail-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.detail-value {
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-bio {
  font-weight: 400;
  line-height: 1.5;
  word-break: break-word;
}

/* Settings Card */
.settings-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-description {
  color: var(--text-secondary);
  font-size: 0.9375rem;
  line-height: 1.6;
  margin: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-group label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.input-with-actions {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.form-input {
  flex: 1;
  min-width: 200px;
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

.action-buttons {
  display: flex;
  gap: 0.75rem;
}

.help-text {
  display: block;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  line-height: 1.5;
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

.btn-secondary:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.15);
  border-color: var(--color-primary, #10b981);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Success Message */
.success-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 8px;
  color: #10b981;
  font-weight: 600;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-icon {
  font-size: 1.25rem;
  font-weight: 700;
}

/* Current Value Display */
.current-value {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.4);
}

.value-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.value-display {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-primary);
}

/* No Height Placeholder */
.no-height-placeholder {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(241, 245, 249, 0.05);
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
}

.placeholder-icon {
  font-size: 1.5rem;
  opacity: 0.6;
}

.placeholder-text {
  font-size: 0.9375rem;
  font-style: italic;
}

/* Responsive */
@media (max-width: 968px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile {
    padding: 1rem 0.5rem;
  }

  .dashboard-header {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
  }

  .header-content {
    gap: 0rem;
  }

  .settings-btn {
    display: none;
  }

  .profile-avatar-large {
    width: 80px;
    height: 80px;
    font-size: 2rem;
  }

  .detail-row {
    flex-direction: column;
    gap: 0.25rem;
    text-align: center;
  }

  .detail-row-full {
    text-align: left;
  }

  .input-with-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .form-input {
    min-width: 100%;
  }

  .action-buttons {
    width: 100%;
  }

  .action-buttons button {
    flex: 1;
  }
}

@media (max-width: 480px) {
  .title-section h1 {
    font-size: 1.625rem;
  }
}
</style>
