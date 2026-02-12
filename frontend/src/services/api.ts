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
  const accessToken = localStorage.getItem("hevy_access_token");
  const apiKey = localStorage.getItem("hevy_api_key");
  
  if (apiKey) {
    config.headers["api-key"] = apiKey;
  } else if (accessToken && accessToken !== "csv_mode" && accessToken !== "api_key_mode") {
    // Use Bearer authentication for OAuth2
    config.headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return config;
});

// Add response interceptor for automatic token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If we get a 401 and haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem("hevy_refresh_token");
      const accessToken = localStorage.getItem("hevy_access_token");
      
      if (refreshToken && accessToken !== "csv_mode" && accessToken !== "api_key_mode") {
        try {
          // Try to refresh the token
          const response = await api.post("/refresh_token", {
            refresh_token: refreshToken,
            access_token: accessToken,
          });
          
          const { access_token, refresh_token, expires_at } = response.data;
          
          // Update stored tokens
          localStorage.setItem("hevy_access_token", access_token);
          if (refresh_token) {
            localStorage.setItem("hevy_refresh_token", refresh_token);
          }
          if (expires_at) {
            localStorage.setItem("hevy_token_expires_at", expires_at.toString());
          }
          
          // Retry the original request with new token
          originalRequest.headers["Authorization"] = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem("hevy_access_token");
          localStorage.removeItem("hevy_refresh_token");
          localStorage.removeItem("hevy_token_expires_at");
          window.location.href = "/";
          return Promise.reject(refreshError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

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
