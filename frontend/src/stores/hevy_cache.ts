import { defineStore } from "pinia";
import { userService, workoutService } from "../services/api";

interface UserAccount {
  username: string;
  email: string;
  [key: string]: any;
}

interface Workout {
  id: string;
  [key: string]: any;
}


export const useHevyCache = defineStore("hevyCache", {
  state: () => ({
    userAccount: null as UserAccount | null,
    workouts: [] as Workout[],
    isLoadingUser: false,
    isLoadingWorkouts: false,
    workoutsLastFetched: null as number | null,
    error: null as string | null,
    dataSource: (localStorage.getItem("data_source") || "api") as "api" | "csv",
  }),

  getters: {
    username: (state) => {
      if (state.dataSource === "csv") {
        return "CSV User";
      }
      return state.userAccount?.username || null;
    },
    hasWorkouts: (state) => state.workouts.length > 0,
    isCSVMode: (state) => state.dataSource === "csv",
    // Cache workouts for 5 minutes (API only)
    shouldRefetchWorkouts: (state) => {
      if (state.dataSource === "csv") return false; // Never refetch CSV data
      if (!state.workoutsLastFetched) return true;
      const fiveMinutes = 5 * 60 * 1000;
      return Date.now() - state.workoutsLastFetched > fiveMinutes;
    },
  },

  actions: {
    async fetchUserAccount(force = false) {
      // In CSV mode, create a mock user account
      if (this.dataSource === "csv") {
        if (!this.userAccount || force) {
          this.userAccount = {
            username: "CSV User",
            email: "csv@import.local",
          };
        }
        return this.userAccount;
      }

      if (this.userAccount && !force) return this.userAccount;
      
      this.isLoadingUser = true;
      this.error = null;
      
      try {
        this.userAccount = await userService.getAccount();
        return this.userAccount;
      } catch (error: any) {
        this.error = error.message || "Failed to fetch user account";
        throw error;
      } finally {
        this.isLoadingUser = false;
      }
    },

    async fetchWorkouts(force = false) {
      // In CSV mode, load from localStorage - do NOT call API
      if (this.dataSource === "csv") {
        if (this.hasWorkouts && !force) {
          return this.workouts;
        }
        
        const csvData = localStorage.getItem("csv_workouts");
        if (csvData) {
          try {
            this.workouts = JSON.parse(csvData);
            this.workoutsLastFetched = Date.now();
          } catch (error) {
            console.error("Failed to parse CSV workouts from localStorage", error);
            this.workouts = [];
          }
        }
        // Always return here for CSV mode - never call API
        return this.workouts;
      }

      // Use cache if available and not forced
      if (this.hasWorkouts && !this.shouldRefetchWorkouts && !force) {
        if (import.meta.env.DEV) {
          console.debug("[hevyCache] Using cached workouts:", {
            count: this.workouts.length,
            lastFetched: this.workoutsLastFetched,
          });
        }
        return this.workouts;
      }

      this.isLoadingWorkouts = true;
      this.error = null;

      try {
        // Ensure we have username for API mode
        if (!this.username) {
          await this.fetchUserAccount();
        }

        // Safety check: username must exist for API calls
        if (!this.username) {
          throw new Error("Username not available for API requests");
        }

        const allWorkouts: Workout[] = [];

        // Fetch workouts in batches of 5 (username required) until exhausted
        let offset = 0;
        const pageSize = 5;
        // Loop until API returns no more workouts
        // Safeguard with a hard cap to avoid infinite loops in case of API issues
        const maxPages = 2000; // allows up to 10,000 workouts
        let pagesFetched = 0;
        while (pagesFetched < maxPages) {
          if (import.meta.env.DEV) {
            console.debug("[hevyCache] Fetching workouts page:", { offset });
          }
          const result = await workoutService.getWorkouts(this.username!, offset);
          const batch = result.workouts || [];
          if (import.meta.env.DEV) {
            console.debug("[hevyCache] Received batch:", { offset, size: batch.length });
          }
          if (batch.length === 0) break;
          allWorkouts.push(...batch);
          offset += pageSize;
          pagesFetched += 1;
        }

        this.workouts = allWorkouts;
        this.workoutsLastFetched = Date.now();
        if (import.meta.env.DEV) {
          console.debug("[hevyCache] Finished fetching workouts:", {
            total: this.workouts.length,
            pagesFetched,
          });
        }

        return this.workouts;
      } catch (error: any) {
        this.error = error.message || "Failed to fetch workouts";
        throw error;
      } finally {
        this.isLoadingWorkouts = false;
      }
    },

    loadCSVWorkouts(workouts: Workout[]) {
      this.dataSource = "csv";
      this.workouts = workouts;
      this.workoutsLastFetched = Date.now();
      localStorage.setItem("data_source", "csv");
      localStorage.setItem("csv_workouts", JSON.stringify(workouts));
    },

    switchToAPIMode() {
      this.dataSource = "api";
      this.workouts = [];
      this.workoutsLastFetched = null;
      localStorage.setItem("data_source", "api");
      localStorage.removeItem("csv_workouts");
    },

    clearCache() {
      this.workouts = [];
      this.workoutsLastFetched = null;
      if (this.dataSource === "csv") {
        localStorage.removeItem("csv_workouts");
      }
    },

    logout() {
      this.userAccount = null;
      this.workouts = [];
      this.workoutsLastFetched = null;
      this.error = null;
      this.dataSource = "api";
      localStorage.removeItem("data_source");
      localStorage.removeItem("csv_workouts");
    },
  },
});
