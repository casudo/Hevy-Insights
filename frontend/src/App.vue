<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authService } from "./services/api";

const router = useRouter();
const route = useRoute();
const showNav = ref(false);
const appVersion = "v1.0.0"; // Update version as needed

const checkAuth = () => {
  const token = localStorage.getItem("hevy_auth_token");
  showNav.value = !!token && route.path !== "/login"; // Show nav if token exists AND not on login page
};

const logout = () => {
  authService.logout();
  router.push("/login");
};

// Check auth status on mount to DOM (Document Object Model)
onMounted(checkAuth);

// Watch for route changes to update nav visibility
router.afterEach(() => {
  checkAuth();
});
</script>

<!-- =============================================================================== -->

<template>
  <div id="app">
    <!-- Sidebar Navigation -->
    <aside v-if="showNav" class="sidebar">
      <div class="sidebar-header">
        <router-link to="/dashboard" class="sidebar-brand">
          <span class="brand-icon">💪</span>
          <span class="brand-text">Hevy Insights</span>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/dashboard" class="nav-item">
          <span class="nav-icon">📊</span>
          <span class="nav-text">Dashboard</span>
        </router-link>
        <router-link to="/workouts-card" class="nav-item">
          <span class="nav-icon">🏋️</span>
          <span class="nav-text">Workouts (Card)</span>
        </router-link>
        <router-link to="/workouts-list" class="nav-item">
          <span class="nav-icon">🏋️</span>
          <span class="nav-text">Workouts (List)</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="version-info">{{ appVersion }}</div>
        <button @click="logout" class="logout-btn">
          <span class="nav-icon">🚪</span>
          <span class="nav-text">Logout</span>
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main :class="{ 'with-sidebar': showNav, 'without-sidebar': !showNav }">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --bg-primary: #1e1e2e;
  --bg-secondary: #27293d;
  --bg-card: #27293d;
  --bg-card-hover: #2f3147;
  --text-primary: #ffffff;
  --text-secondary: #9A9A9A;
  --emerald-primary: #10b981;
  --emerald-dark: #059669;
  --emerald-darker: #047857;
  --cyan-accent: #06b6d4;
  --border-color: #2b3553;
  --shadow: rgba(0, 0, 0, 0.3);
  --sidebar-width: 260px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg-primary);
  margin: 0;
  padding: 0;
  color: var(--text-primary);
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  display: flex;
  background: var(--bg-primary);
}

/* Sidebar Styles */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: 2px 0 10px var(--shadow);
}

.sidebar-header {
  padding: 1.5rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.sidebar-brand:hover {
  color: var(--emerald-primary);
}

.brand-icon {
  font-size: 1.75rem;
}

.brand-text {
  font-size: 1.125rem;
}

.sidebar-nav {
  flex: 1;
  padding: 1.5rem 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1.25rem;
  margin: 0.25rem 0.75rem;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.95rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  position: relative;
}

.nav-item:hover {
  color: var(--text-primary);
  background: rgba(16, 185, 129, 0.1);
}

.nav-item.router-link-active {
  color: var(--emerald-primary);
  background: rgba(16, 185, 129, 0.15);
}

.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 70%;
  background: var(--emerald-primary);
  border-radius: 0 4px 4px 0;
}

.nav-icon {
  font-size: 1.25rem;
  width: 24px;
  text-align: center;
}

.nav-text {
  flex: 1;
}

.sidebar-footer {
  padding: 1rem 0.75rem;
  border-top: 1px solid var(--border-color);
}

.version-info {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin: 0 0 0.5rem 0.5rem;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1.25rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  font-size: 0.95rem;
  text-align: left;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
}

/* Main Content Area */
main.with-sidebar {
  margin-left: var(--sidebar-width);
  width: calc(100% - var(--sidebar-width));
  min-height: 100vh;
}

main.without-sidebar {
  width: 100%;
  min-height: 100vh;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  :root {
    --sidebar-width: 220px;
  }
  
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.mobile-open {
    transform: translateX(0);
  }
  
  main.with-sidebar {
    margin-left: 0;
    width: 100%;
  }
  
  .brand-text {
    font-size: 1rem;
  }
  
  .nav-item {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
}
</style>
