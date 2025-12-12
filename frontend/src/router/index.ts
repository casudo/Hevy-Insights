import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Dashboard from "../views/Dashboard.vue";
import WorkoutsCard from "../views/Workouts_Card.vue";
import WorkoutsList from "../views/Workouts_List.vue";

const router = createRouter({
  history: createWebHistory(),
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
  ],
});

// Navigation guard to check authentication
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("hevy_auth_token");
  
  if (to.meta.requiresAuth && !token) {
    next("/login");
  } else if (to.path === "/login" && token) {
    next("/dashboard");
  } else {
    next();
  }
});

export default router;
