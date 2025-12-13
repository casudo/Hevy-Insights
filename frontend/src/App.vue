<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authService } from "./services/api";

const router = useRouter();
const route = useRoute();
const showNav = ref(false);
const appVersion = "v1.1.0"; // Update version as needed
const isMobileSidebarOpen = ref(false);
const showTopbar = ref(true);
const showScrollTop = ref(false);

const updateNavVisibility = () => {
  // Show nav/topbar on all routes except login
  showNav.value = route.path !== "/login";
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const logout = () => {
  authService.logout();
  router.push("/login");
};

// On mount to DOM (Document Object Model)
onMounted(() => {
  updateNavVisibility();
  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    // Show topbar when scrolling up or near top; hide on scroll down
    showTopbar.value = y < 10 || y < lastY;
    // Show scroll to top button when scrolled down 300px
    showScrollTop.value = y > 300;
    lastY = y;
  };
  window.addEventListener("scroll", onScroll, { passive: true });
});

// Watch for route changes to update nav visibility
router.afterEach(() => {
  updateNavVisibility();
  isMobileSidebarOpen.value = false;
});

// Lock page scroll when sidebar is open
watch(isMobileSidebarOpen, (open) => {
  const cls = "sidebar-open";
  if (open) {
    document.body.classList.add(cls);
  } else {
    document.body.classList.remove(cls);
  }
});
</script>

<!-- =============================================================================== -->

<template>
  <div id="app">
    <!-- Mobile Top Bar -->
    <header v-if="showNav && showTopbar" class="topbar">
      <button class="menu-btn" @click="isMobileSidebarOpen = !isMobileSidebarOpen">☰</button>
      <router-link to="/dashboard" class="topbar-brand">
        <span class="brand-text">Hevy Insights</span>
      </router-link>
    </header>
    
    <!-- Sidebar Navigation -->
    <aside v-if="showNav" :class="['sidebar', { 'mobile-open': isMobileSidebarOpen }]">
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
        <router-link to="/exercises" class="nav-item">
          <span class="nav-icon">📚</span>
          <span class="nav-text">Exercises</span>
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

    <!-- Backdrop for mobile to close sidebar -->
    <div v-if="isMobileSidebarOpen" class="backdrop" @click="isMobileSidebarOpen = false"></div>
    
    <!-- Scroll to Top Button -->
    <button v-if="showScrollTop" class="scroll-to-top" @click="scrollToTop" title="Scroll to top">
      ↑
    </button>
    
    <!-- Main Content Area -->
    <main :class="{ 'with-sidebar': showNav, 'without-sidebar': !showNav, 'dimmed': isMobileSidebarOpen }">
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
  --topbar-height: 56px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg-primary);
  margin: 0;
  padding: 0;
  color: var(--text-primary);
  overflow-x: hidden;
}

/* Prevent any scrolling when sidebar is open */
body.sidebar-open {
  height: 100vh;
  overflow: hidden;
  overscroll-behavior: contain;
  touch-action: none;
}

/* Scroll to Top Button */
.scroll-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 52px;
  height: 52px;
  min-width: 52px;
  min-height: 52px;
  background: var(--emerald-primary);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 2.5rem;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
  z-index: 9999;
  display: grid;
  place-items: center;
  padding: 0;
  margin: 0;
  line-height: 1;
}

.scroll-to-top:hover {
  background: var(--emerald-dark);
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5);
}

.scroll-to-top:active {
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .scroll-to-top {
    bottom: 1.5rem;
    right: 1.5rem;
    width: 48px;
    height: 48px;
    min-width: 48px;
    min-height: 48px;
    font-size: 2rem;
    display: grid;
    place-items: center;
    line-height: 1;
  }
}

#app {
  min-height: 100vh;
  display: flex;
  background: var(--bg-primary);
  flex-direction: row; /* desktop: sidebar + content side-by-side */
}

/* Hide the mobile topbar on desktop to avoid blank space */
.topbar {
  display: none;
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
  /* Mobile: stack topbar above content */
  #app { flex-direction: column; }
  .topbar {
    height: var(--topbar-height);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0 0.75rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 1200;
    transition: transform 0.2s ease;
  }
  .menu-btn {
    background: rgba(16, 185, 129, 0.15);
    color: var(--emerald-primary);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    font-size: 1rem;
  }
  .topbar-brand { display: flex; align-items: center; gap: 0.5rem; color: var(--text-primary); text-decoration: none; font-weight: 600; }
  
  .sidebar { transform: translateX(-100%); transition: transform 0.3s ease; top: var(--topbar-height); height: calc(100vh - var(--topbar-height)); bottom: auto; overflow-y: auto; }
  .sidebar.mobile-open { transform: translateX(0); }
  
  /* Attach content directly under top bar without extra spacing */
  main.with-sidebar { margin-left: 0; width: 100%; }
  main.dimmed::after { content: ""; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 900; }
  .backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 950; }
  
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
