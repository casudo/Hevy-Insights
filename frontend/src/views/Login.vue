<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { authService } from "../services/api";
import { useHevyCache } from "../stores/hevy_cache";
import { readCSVFile, parseCSV, validateCSVFile } from "../utils/csvParser";

const router = useRouter();
const { t } = useI18n();
const store = useHevyCache();

// Mode selection
type LoginMode = "credentials" | "csv";
const loginMode = ref<LoginMode>("credentials");

// Credentials login
const emailOrUsername = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

// CSV upload
const csvFile = ref<File | null>(null);
const csvError = ref("");
const uploadLoading = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

const handleLogin = async () => {
  if (!emailOrUsername.value || !password.value) {
    error.value = t("login.api.errors.emptyFields");
    return;
  }

  loading.value = true;
  error.value = "";

  // Attempt login via API service
  try {
    const result = await authService.login(emailOrUsername.value, password.value);
    
    if (result.auth_token) {
      localStorage.setItem("hevy_auth_token", result.auth_token);
      await store.switchToAPIMode();
      router.push("/dashboard");
    } else {
      error.value = t("login.api.errors.loginFailed");
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || t("login.api.errors.invalidCredentials");
  } finally {
    loading.value = false;
  }
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    csvFile.value = target.files[0];
    csvError.value = "";
  }
};

const handleCSVUpload = async () => {
  if (!csvFile.value) {
    csvError.value = t("login.csv.errors.noFile");
    return;
  }

  uploadLoading.value = true;
  csvError.value = "";

  // Try to "login" with CSV file
  try {
    // Validate file
    try {
      const isValid = await validateCSVFile(csvFile.value);
      if (!isValid) {
        csvError.value = t("login.csv.errors.invalidFile");
        return;
      }
    } catch (err: any) {
      csvError.value = err?.message || t("login.csv.errors.invalidFile");
      return;
    }

    // Read and parse CSV
    const content = await readCSVFile(csvFile.value);
    const workouts = parseCSV(content);

    if (workouts.length === 0) {
      csvError.value = t("login.csv.errors.emptyFile");
      uploadLoading.value = false;
      return;
    }

    // Store data and switch to CSV mode
    store.loadCSVWorkouts(workouts);
    localStorage.setItem("hevy_auth_token", "csv_mode");

    // Navigate to dashboard
    router.push("/dashboard");
  } catch (err: any) {
    csvError.value = err.message || t("login.csv.errors.uploadFailed");
  } finally {
    uploadLoading.value = false;
  }
};

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const removeFile = () => {
  csvFile.value = null;
  csvError.value = "";
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};
</script>

<!-- =============================================================================== -->

<template>
  <div class="login-wrapper">
    <!-- Animated Background -->
    <div class="background-gradient">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- Login Card -->
    <div class="login-container">
      <div class="login-card">
        <!-- Header Section -->
        <div class="login-header">
          <div class="logo-container">
            <div class="logo-icon">🏋️</div>
            <h1 class="logo-text">Hevy Insights</h1>
          </div>
          <p class="welcome-text">{{ t('login.welcome') }}</p>
        </div>

        <!-- Mode Toggle -->
        <div class="mode-toggle">
          <button
            type="button"
            class="mode-button"
            :class="{ active: loginMode === 'credentials' }"
            @click="loginMode = 'credentials'"
          >
            <span class="mode-icon">🔑</span>
            <span>{{ t('login.api.modeButton') }}</span>
          </button>
          <button
            type="button"
            class="mode-button"
            :class="{ active: loginMode === 'csv' }"
            @click="loginMode = 'csv'"
          >
            <span class="mode-icon">📂</span>
            <span>{{ t('login.csv.modeButton') }}</span>
          </button>
        </div>

        <!-- Credentials Login Form -->
        <form v-if="loginMode === 'credentials'" @submit.prevent="handleLogin" class="login-form">
          <div class="input-group">
            <label for="username" class="input-label">
              <span class="label-icon">👤</span>
              {{ t('login.api.usernameOrEmail') }}
            </label>
            <input
              id="username"
              v-model="emailOrUsername"
              type="text"
              class="input-field"
              :placeholder="t('login.api.usernamePlaceholder')"
              required
              :disabled="loading"
              autocomplete="username"
            />
          </div>

          <div class="input-group">
            <label for="password" class="input-label">
              <span class="label-icon">🔒</span>
              {{ t('login.api.password') }}
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              class="input-field"
              :placeholder="t('login.api.passwordPlaceholder')"
              required
              :disabled="loading"
              autocomplete="current-password"
            />
          </div>

          <!-- Error Message -->
          <transition name="fade">
            <div v-if="error" class="error-alert">
              <span class="error-icon">⚠️</span>
              <span class="error-text">{{ error }}</span>
            </div>
          </transition>

          <!-- Submit Button -->
          <button type="submit" class="submit-button" :disabled="loading">
            <span v-if="!loading" class="button-content">
              <span class="button-text">{{ t('login.api.loginButton') }}</span>
            </span>
            <span v-else class="button-loading">
              <span class="loading-spinner"></span>
              <span>{{ t('login.api.loggingIn') }}</span>
            </span>
          </button>
        </form>

        <!-- CSV Upload Form -->
        <div v-else class="csv-upload-form">
          <div class="upload-info">
            <span class="info-icon">ℹ️</span>
            <p class="info-text">{{ t("login.csv.description") }}</p>
          </div>

          <!-- File Input (Hidden) -->
          <input
            ref="fileInputRef"
            type="file"
            accept=".csv"
            @change="handleFileSelect"
            class="file-input-hidden"
          />

          <!-- File Upload Area -->
          <div
            class="file-upload-area"
            :class="{ 'has-file': csvFile }"
            @click="!csvFile && triggerFileInput()"
          >
            <div v-if="!csvFile" class="upload-prompt">
              <span class="upload-icon">📁</span>
              <p class="upload-title">{{ t("login.csv.selectFile") }}</p>
              <p class="upload-subtitle">{{ t("login.csv.dragDrop") }}</p>
              <button type="button" class="browse-button" @click.stop="triggerFileInput">
                {{ t("login.csv.browse") }}
              </button>
            </div>

            <div v-else class="file-preview">
              <div class="file-info">
                <span class="file-icon">📄</span>
                <div class="file-details">
                  <p class="file-name">{{ csvFile.name }}</p>
                  <p class="file-size">{{ (csvFile.size / 1024).toFixed(2) }} KB</p>
                </div>
              </div>
              <button type="button" class="remove-button" @click.stop="removeFile">
                <span>✕</span>
              </button>
            </div>
          </div>

          <!-- Error Message -->
          <transition name="fade">
            <div v-if="csvError" class="error-alert">
              <span class="error-icon">⚠️</span>
              <span class="error-text">{{ csvError }}</span>
            </div>
          </transition>

          <!-- Upload Button -->
          <button
            type="button"
            class="submit-button"
            :disabled="!csvFile || uploadLoading"
            @click="handleCSVUpload"
          >
            <span v-if="!uploadLoading" class="button-content">
              <span class="button-text">{{ t("login.csv.uploadButton") }}</span>
            </span>
            <span v-else class="button-loading">
              <span class="loading-spinner"></span>
              <span>{{ t("login.csv.uploading") }}</span>
            </span>
          </button>
        </div>

        <!-- Footer -->
        <div class="login-footer">
          <div class="divider"></div>
          <p class="footer-text">
            {{ t('login.madeBy') }} <strong><a href="https://github.com/casudo/Hevy-Insights" target="_blank" rel="noopener noreferrer">casudo</a></strong> • {{ t('login.tagline') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- =============================================================================== -->

<style scoped>
/* Wrapper and Background */
.login-wrapper {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #0a0a0f;
}

.background-gradient {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: radial-gradient(circle at 50% 50%, #1e1e2e 0%, #0a0a0f 100%);
  width: 100vw;
  height: 100vh;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #10b981, #059669);
  top: -200px;
  left: -200px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #06b6d4, #0891b2);
  bottom: -250px;
  right: -250px;
  animation-delay: -7s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: linear-gradient(135deg, #047857, #065f46);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(50px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-30px, 30px) scale(0.9);
  }
}

/* Login Container */
.login-container {
  position: relative;
  z-index: 10;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 4rem;
}

.login-card {
  background: rgba(30, 30, 46, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 32px;
  padding: 2.25rem 2rem;
  width: min(550px, 90vw);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 80px rgba(16, 185, 129, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-card:hover {
  border-color: rgba(16, 185, 129, 0.3);
  box-shadow: 
    0 24px 72px rgba(0, 0, 0, 0.6),
    0 0 100px rgba(16, 185, 129, 0.15);
  transform: translateY(-4px);
}

/* Header Section */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logo-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.9rem;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
  }
}

.logo-text {
  margin: 0;
  font-size: 1.9rem;
  font-weight: 700;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
  line-height: 1.25;
  padding-bottom: 0.1rem;
  display: inline-block;
}

.welcome-text {
  margin: 0;
  color: #9A9A9A;
  font-size: 1.05rem;
  font-weight: 400;
}

/* Form Section */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 480px;
  margin: 0 auto;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #e5e7eb;
  font-size: 0.9rem;
  letter-spacing: 0.25px;
}

.label-icon {
  font-size: 1.125rem;
}

.input-field {
  padding: 0.85rem 1rem;
  border: 2px solid rgba(16, 185, 129, 0.15);
  background: rgba(15, 15, 25, 0.8);
  color: #ffffff;
  border-radius: 12px;
  font-size: 0.95rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  width: 100%;
}

.input-field:hover {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(20, 20, 30, 0.9);
}

.input-field:focus {
  outline: none;
  border-color: #10b981;
  background: rgba(25, 25, 35, 1);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}

.input-field:disabled {
  background: rgba(10, 10, 20, 0.6);
  cursor: not-allowed;
  opacity: 0.5;
}

.input-field::placeholder {
  color: #6c6c80;
}

/* Error Alert */
.error-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-left: 4px solid #ef4444;
  border-radius: 12px;
  animation: shake 0.4s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

.error-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.error-text {
  color: #fca5a5;
  font-size: 0.9rem;
  font-weight: 500;
}

/* Fade Transition */
.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Submit Button */
.submit-button {
  margin-top: 0.5rem;
  padding: 0.9rem 1.25rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.975rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.submit-button::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.submit-button:hover:not(:disabled)::before {
  opacity: 1;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.45);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-content,
.button-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  position: relative;
  z-index: 1;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  gap: 0.75rem;
  padding: 0.5rem;
  background: rgba(15, 15, 25, 0.8);
  border-radius: 16px;
  margin-bottom: 2rem;
}

.mode-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.85rem 1.25rem;
  background: transparent;
  color: #9A9A9A;
  border: 2px solid transparent;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
}

.mode-button:hover {
  color: #e5e7eb;
  background: rgba(16, 185, 129, 0.05);
}

.mode-button.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-color: #10b981;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.mode-icon {
  font-size: 1.125rem;
}

/* CSV Upload Form */
.csv-upload-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.upload-info {
  display: flex;
  align-items: start;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: rgba(6, 182, 212, 0.05);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-left: 4px solid #06b6d4;
  border-radius: 12px;
}

.info-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.info-text {
  margin: 0;
  color: #9dd7e5;
  font-size: 0.9rem;
  line-height: 1.5;
}

.file-input-hidden {
  display: none;
}

.file-upload-area {
  padding: 1rem 1rem;
  border: 2px dashed rgba(16, 185, 129, 0.3);
  border-radius: 16px;
  background: rgba(15, 15, 25, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-upload-area:hover {
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(20, 20, 30, 0.8);
}

.file-upload-area.has-file {
  cursor: default;
  border-style: solid;
  padding: 1.5rem;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
}

.upload-icon {
  font-size: 3rem;
  opacity: 0.7;
}

.upload-title {
  margin: 0;
  color: #e5e7eb;
  font-size: 1.1rem;
  font-weight: 600;
}

.upload-subtitle {
  margin: 0;
  color: #9A9A9A;
  font-size: 0.9rem;
}

.browse-button {
  margin-top: 0.5rem;
  padding: 0.65rem 1.5rem;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
}

.browse-button:hover {
  background: rgba(16, 185, 129, 0.25);
  border-color: rgba(16, 185, 129, 0.5);
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0;
  color: #e5e7eb;
  font-size: 0.95rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  margin: 0.25rem 0 0 0;
  color: #9A9A9A;
  font-size: 0.85rem;
}

.remove-button {
  width: 32px;
  height: 32px;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  font-size: 1.125rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.remove-button:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: rgba(239, 68, 68, 0.5);
}

/* Footer */
.login-footer {
  margin-top: 2.5rem;
}

.divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(16, 185, 129, 0.3),
    transparent
  );
  margin-bottom: 1.5rem;
}

.footer-text {
  text-align: center;
  color: #6c6c80;
  font-size: 0.85rem;
  margin: 0;
}

.footer-text strong {
  color: #10b981;
  font-weight: 600;
}

/* Keep footer link green across states */
.footer-text a {
  color: #10b981;
  text-decoration: none;
}
.footer-text a:visited {
  color: #10b981; /* avoid purple visited color */
}

/* Responsive Design */
@media (max-width: 1024px) {
  .login-container {
    padding: 2rem;
  }

  .login-card {
    width: min(760px, 94vw);
    padding: 3.25rem 2.75rem;
  }
}

@media (max-width: 768px) {
  .login-container {
    padding: 1.5rem;
  }

  .login-card {
    width: 100%;
    padding: 2.25rem 1.75rem;
  }

  .logo-icon {
    width: 56px;
    height: 56px;
    font-size: 1.9rem;
  }

  .logo-text {
    font-size: 1.9rem;
  }
}

@media (max-width: 640px) {
  .login-container {
    padding: 1rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
    border-radius: 20px;
  }

  .logo-icon {
    width: 48px;
    height: 48px;
    font-size: 1.75rem;
  }

  .logo-text {
    font-size: 1.75rem;
  }

  .welcome-text {
    font-size: 0.875rem;
  }

  .input-field {
    padding: 0.875rem 1rem;
    font-size: 0.95rem;
  }

  .submit-button {
    padding: 1rem 1.25rem;
    font-size: 1rem;
  }

  .orb-1, .orb-2, .orb-3 {
    opacity: 0.3;
  }
}

@media (max-width: 380px) {
  .login-card {
    padding: 1.5rem 1.25rem;
  }

  .logo-container {
    flex-direction: column;
    gap: 0.5rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }
}

/* Landscape mobile optimization */
@media (max-height: 600px) and (orientation: landscape) {
  .login-container {
    padding: 1rem;
    align-items: flex-start;
    overflow-y: auto;
  }

  .login-card {
    margin: 1rem auto;
    padding: 1.5rem;
  }

  .login-header {
    margin-bottom: 1.5rem;
  }

  .login-form {
    gap: 1.25rem;
  }

  .login-footer {
    margin-top: 1.5rem;
  }
}
</style>
