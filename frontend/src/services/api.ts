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

// Authentication Service
export const authService = {
  async login(emailOrUsername: string, password: string) {
    // OAuth2 login with automatic reCAPTCHA token generation
    const response = await api.post("/login", {
      emailOrUsername,
      password,
    });
    return response.data;
  },

  async refreshToken(refreshToken: string, accessToken?: string) {
    const response = await api.post("/refresh_token", {
      refresh_token: refreshToken,
      access_token: accessToken,
    });
    return response.data;
  },

  async validateApiKey(apiKey: string) {
    const response = await api.post("/validate_api_key", {
      api_key: apiKey,
    });
    return response.data;
  },

  logout() {
    localStorage.removeItem("hevy_access_token");
    localStorage.removeItem("hevy_refresh_token");
    localStorage.removeItem("hevy_token_expires_at");
    localStorage.removeItem("hevy_api_key");
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
    // Check if using API key (PRO mode)
    const apiKey = localStorage.getItem("hevy_api_key");
    
    if (apiKey) {
      // Use page-based pagination for PRO API
      const page = Math.floor(offset / 10) + 1; // Convert offset to page number
      const response = await api.get("/workouts", {
        params: { page, page_size: 10 },
      });
      return response.data;
    } else {
      // Use offset-based pagination for free API
      const response = await api.get("/workouts", {
        params: { username, offset },
      });
      return response.data;
    }
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
