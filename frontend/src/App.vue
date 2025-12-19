<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authService } from "./services/api";
import { useHevyCache } from "./stores/hevy_cache";

const router = useRouter();
const route = useRoute();
const store = useHevyCache();
const userAccount = computed(() => store.userAccount);
const showNav = ref(false);
const appVersion = "v1.3.0"; // Update version as needed
const isMobileSidebarOpen = ref(false);
const showTopbar = ref(true);
const showScrollTop = ref(false);

// Apply theme from localStorage
const applyTheme = () => {
  const savedTheme = localStorage.getItem("color-theme") || "default";
  const colorThemes: Record<string, { primary: string; secondary: string }> = {
    default: { primary: "#10b981", secondary: "#06b6d4" },
    purple: { primary: "#8b5cf6", secondary: "#ec4899" },
    blue: { primary: "#3b82f6", secondary: "#6366f1" },
    orange: { primary: "#f59e0b", secondary: "#ef4444" }
  };
  const theme = colorThemes[savedTheme] || colorThemes.default;
  document.documentElement.style.setProperty("--color-primary", theme!.primary);
  document.documentElement.style.setProperty("--color-secondary", theme!.secondary);
};

const updateNavVisibility = () => {
  // Show nav/topbar on all routes except login
  showNav.value = route.path !== "/login";
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const logout = () => {
  authService.logout();
  store.logout();
  router.push("/login");
};

// On mount to DOM (Document Object Model)
onMounted(() => {
  // Apply theme on initial load
  applyTheme();

  updateNavVisibility();
  // Keep topbar always visible on mobile
  showTopbar.value = true;
  const onScroll = () => {
    const y = window.scrollY;
    // Show scroll to top button when scrolled down 300px
    showScrollTop.value = y > 300;
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
        <span class="brand-text">Hevy Insights<span v-if="userAccount" class="brand-username"> {{ $t('nav.brandTextFor') }} {{ userAccount.username }}</span></span>
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
          <span class="nav-text">{{ $t('nav.dashboard') }}</span>
        </router-link>
        <router-link to="/workouts-card" class="nav-item">
          <span class="nav-icon">🏋️</span>
          <span class="nav-text">{{ $t('nav.workoutsCard') }}</span>
        </router-link>
        <router-link to="/workouts-list" class="nav-item">
          <span class="nav-icon">🏋️</span>
          <span class="nav-text">{{ $t('nav.workoutsList') }}</span>
        </router-link>
        <router-link to="/exercises" class="nav-item">
          <span class="nav-icon">📚</span>
          <span class="nav-text">{{ $t('nav.exercises') }}</span>
        </router-link>
        <!-- 
        <router-link to="/share" class="nav-item">
          <span class="nav-icon">📤</span>
          <span class="nav-text">{{ $t('nav.share') }}</span>
        </router-link> -->
        <!-- Remove, since already included next to profile badge? -->
        <router-link to="/settings" class="nav-item">
          <span class="nav-icon">⚙️</span>
          <span class="nav-text">{{ $t('nav.settings') }}</span>
        </router-link>        
      </nav>

      <div class="sidebar-footer">
        <div class="version-info">{{ appVersion }}</div>
        <button @click="logout" class="logout-btn">
          <span class="nav-icon">🚪</span>
          <span class="nav-text">{{ $t('nav.logout') }}</span>
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
      
      <!-- Global Footer (shown on all pages except login) -->
      <footer v-if="showNav" class="global-footer">
        <div class="footer-content">
          <div class="footer-buttons">
            <a href="mailto:hevy@kida.one" target="_blank" class="footer-btn">
              📧 Contact me
            </a>
            <a href="https://buymeacoffee.com/casudo" target="_blank" class="footer-btn">
              ☕ Buy me a coffee
            </a>
            <a href="https://github.com/casudo/Hevy-Insights" target="_blank" class="footer-btn">
              ⭐ Star on GitHub
            </a>
            <a href="https://github.com/casudo/Hevy-Insights/issues/new" target="_blank" class="footer-btn">
              🐛 Report a bug
            </a>
          </div>
          <div class="footer-love">
            Made with ❤️ by casudo
          </div>
        </div>
      </footer>
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
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;
  --text-primary: #ffffff;
  --text-secondary: #94a3b8;
  --emerald-primary: #10b981;
  --emerald-dark: #059669;
  --emerald-darker: #047857;
  --cyan-accent: #06b6d4;
  --border-color: #334155;
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
  background: var(--color-primary, #10b981);
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
  filter: brightness(1.2);
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
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%);
  backdrop-filter: blur(8px);
  border-right: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 20%, var(--border-color));
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: 2px 0 10px var(--shadow), inset -1px 0 0 color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
}

.sidebar-header {
  padding: 1.5rem 1.25rem;
  border-bottom: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 15%, var(--border-color));
  background: linear-gradient(90deg, color-mix(in srgb, var(--color-primary, #10b981) 5%, transparent), transparent);
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
  color: var(--color-primary, #10b981);
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent));
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
  background: color-mix(in srgb, var(--color-primary, #10b981) 10%, transparent);
}

.nav-item.router-link-active {
  color: var(--color-primary, #10b981);
  background: color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
}

.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 70%;
  background: var(--color-primary, #10b981);
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
  border-top: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 15%, var(--border-color));
  background: linear-gradient(90deg, color-mix(in srgb, var(--color-primary, #10b981) 3%, transparent), transparent);
}

.version-info {
  color: color-mix(in srgb, var(--color-primary, #10b981) 60%, var(--text-secondary));
  font-size: 0.8rem;
  margin: 0 0 0.5rem 0.5rem;
  font-weight: 500;
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

/* Global Footer */
.global-footer {
  padding: 1.5rem 1.5rem 1rem 1.5rem; /* Top, Right, Bottom, Left */
  background: linear-gradient(180deg, transparent 0%, rgba(30, 41, 59, 0.5) 100%);
  border-top: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 10%, var(--border-color));
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
}

.footer-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.4);
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.footer-btn:hover {
  border-color: var(--color-primary, #10b981);
  color: var(--color-primary, #10b981);
  background: rgba(30, 41, 59, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary, #10b981) 20%, transparent);
}

.footer-love {
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: center;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  :root {
    --sidebar-width: 220px;
  }
  
  /* Footer buttons grid */
  .footer-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    width: 100%;
    max-width: 400px;
  }
  
  .footer-btn {
    justify-content: center;
    padding: 0.625rem 1rem;
    font-size: 0.875rem;
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
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1200;
  }
  
  main.with-sidebar {
    padding-top: var(--topbar-height);
  }
  
  main.without-sidebar {
    padding-top: 0;
  }
  
  .topbar.hidden {
    transform: translateY(-100%);
    opacity: 0;
  }
  .menu-btn {
    background: color-mix(in srgb, var(--color-primary, #10b981) 15%, transparent);
    color: var(--color-primary, #10b981);
    border: 1px solid color-mix(in srgb, var(--color-primary, #10b981) 30%, transparent);
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    font-size: 1rem;
  }
  .topbar-brand { display: flex; align-items: center; gap: 0.5rem; color: var(--text-primary); text-decoration: none; font-weight: 600; }
  .brand-username { font-weight: 500; color: var(--text-secondary); font-style: italic;}
  
  .sidebar-header {
    display: none;
  }
  
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
  
  .sidebar-nav {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 0.5rem;
  }
  
  .sidebar-nav .nav-item {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    min-height: 48px;
  }
}
</style>
