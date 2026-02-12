import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Dashboard from "../views/Dashboard.vue";
import WorkoutsCard from "../views/Workouts_Card.vue";
import WorkoutsList from "../views/Workouts_List.vue";
import Exercises from "../views/Exercises.vue";
import Settings from "../views/Settings.vue";
import Share from "../views/Share.vue";
import BodyMeasurements from "../views/BodyMeasurements.vue";
import Profile from "../views/Profile.vue";

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0, behavior: "smooth" };
  },
  routes: [
    {
      path: "/",
      redirect: "/dashboard",
    },
    {
      path: "/login",
      name: "Login",
      component: Login,
    },
    {
      path: "/dashboard",
      name: "Dashboard",
      component: Dashboard,
      meta: { requiresAuth: true },
    },
    {
      path: "/workouts-card",
      name: "Workouts_Card",
      component: WorkoutsCard,
      meta: { requiresAuth: true },
    },
    {
      path: "/workouts-list",
      name: "Workouts_List",
      component: WorkoutsList,
      meta: { requiresAuth: true },
    },
    {
      path: "/exercises",
      name: "Exercises",
      component: Exercises,
      meta: { requiresAuth: true },
    },
    {
      path: "/share",
      name: "Share",
      component: Share,
      meta: { requiresAuth: true },
    },    
    {
      path: "/body-measurements",
      name: "BodyMeasurements",
      component: BodyMeasurements,
      meta: { requiresAuth: true },
    },
    {
      path: "/profile",
      name: "Profile",
      component: Profile,
      meta: { requiresAuth: true },
    },
    {
      path: "/settings",
      name: "Settings",
      component: Settings,
      meta: { requiresAuth: true },
    },
    // Catch-all for unknown paths
    {
      path: "/:pathMatch(.*)*",
      name: "NotFoundRedirect",
      // We'll redirect based on auth in the global guard
      component: Dashboard,
      meta: { requiresAuth: true },
    },
  ],
});

// Navigation guard to check authentication
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("hevy_access_token");
  
  if (to.meta.requiresAuth && !token) {
    return next("/login");
  }

  if (to.path === "/login" && token) {
    return next("/dashboard");
  }

  // If route is unmatched (catch-all), send to dashboard or login
  const isCatchAll = to.name === "NotFoundRedirect";
  if (isCatchAll) {
    return next(token ? "/dashboard" : "/login");
  }

  return next();
});

export default router;
