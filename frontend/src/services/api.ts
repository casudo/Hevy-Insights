import axios from "axios";

// Use relative API in production (proxied by Nginx); localhost in dev
const API_BASE_URL = import.meta.env.PROD ? "/api" : "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ===============================================================================

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("hevy_auth_token");
  if (token) {
    config.headers["auth-token"] = token;
  }
  return config;
});

// Authentication Service
export const authService = {
  async login(emailOrUsername: string, password: string) {
    const response = await api.post("/login", {
      emailOrUsername,
      password,
    });
    return response.data;
  },

  async validateToken(authToken: string) {
    const response = await api.post("/validate", {
      auth_token: authToken,
    });
    return response.data;
  },

  logout() {
    localStorage.removeItem("hevy_auth_token");
  },
};

// User Service
export const userService = {
  async getAccount() {
    const response = await api.get("/user/account");
    return response.data;
  },
};

// Workout Service
export const workoutService = {
  async getWorkouts(username: string, offset: number = 0) {
    const response = await api.get("/workouts", {
      params: { username, offset },
    });
    return response.data;
  },
};

export default api;
