import axios from "axios";

// Use relative API in production (proxied by Nginx); localhost in dev
const API_BASE_URL = import.meta.env.PROD ? "/api" : "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Enable sending cookies with requests
});

// ===============================================================================

// Authentication Service
export const authService = {
  async login(emailOrUsername: string, password: string) {
    // OAuth2 login with automatic reCAPTCHA token generation
    // Backend will set HttpOnly cookies automatically
    const response = await api.post("/login", {
      emailOrUsername,
      password,
    });
    return response.data;
  },

  async validateApiKey(apiKey: string) {
    // Validate Hevy PRO API key
    // Backend will set HttpOnly cookies if valid
    const response = await api.post("/validate_api_key", {
      api_key: apiKey,
    });
    return response.data;
  },

  async logout() {
    // Call backend to clear authentication cookies
    try {
      await api.post("/logout");
    } catch (error) {
      console.error("Logout error:", error);
    }
  },

  async getAuthStatus() {
    // Check authentication status from backend
    try {
      const response = await api.get("/auth/status");
      return response.data;
    } catch (error) {
      return {
        authenticated: false,
        auth_mode: null,
      };
    }
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
    // Backend determines OAuth2 vs API key mode from cookies
    // Hevy PRO API key mode uses page-based pagination
    const page = Math.floor(offset / 10) + 1;
    const response = await api.get("/workouts", {
      params: { username, offset, page, page_size: 10 },
    });
    return response.data;
  },
};

// Body Measurement Service
export const bodyMeasurementService = {
  async getMeasurements() {
    const response = await api.get("/body_measurements");
    return response.data;
  },

  async addMeasurement(data: { weight_kg: number; date: string }) {
    const response = await api.post("/body_measurements_batch", data);
    return response.data;
  },
};

// Version Service
export const versionService = {
  async checkForUpdates() {
    try {
      const response = await api.get("/version/check");
      return response.data;
    } catch (error) {
      console.error("Failed to check for updates:", error);
      return {
        current_version: null,
        latest_version: null,
        update_available: false,
        error: "Failed to check for updates",
      };
    }
  },
};

export default api;
