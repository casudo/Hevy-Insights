<div align="center">
  <img alt="Logo" src="readme_images/multi_device_mockup.png"></a>
  <br>
  <h1>Hevy Insights</h1>
  This project is a used to gather data from Hevy API endpoints and visualize it in a web interface, acting as alternative for the Hevy PRO membership.

  ---

  <!-- Placeholder for badges -->
  ![GitHub License](https://img.shields.io/github/license/casudo/Hevy-Insights) ![GitHub release (with filter)](https://img.shields.io/github/v/release/casudo/Hevy-Insights) ![GitHub action checks](https://img.shields.io/github/check-runs/casudo/Hevy-Insights/main) ![GitHub issues](https://img.shields.io/github/issues/casudo/Hevy-Insights) ![GitHub last commit](https://img.shields.io/github/last-commit/casudo/Hevy-Insights)
</div>

> [!NOTE]
> Check it out at: [**Hevy Insights Online**](https://hevy.kida.one)

# About Hevy Insights <!-- omit from toc -->

Hevy Insights is a dynamic web application that provides insights and analytics of your workouts and exercises. It visualizes workout data from the Hevy app in a clean dashboard so that you can always keep track of your progress!

In the Hevy app you can only see your stats and progress up to 3 months for free, otherwise you need the paid Hevy PRO membership.
Hevy Insights allows you to log in with your Hevy credentials and fetch your workout data directly from Hevy's API, providing you with detailed visualizations and historical data up to the date of your account creation - no PRO membership required!

# Table of Contents <!-- omit from toc -->

- [Features](#features)
  - [Plateau \& Strength Detection](#plateau--strength-detection)
  - [Multi-Vendor Support](#multi-vendor-support)
- [Screenshots](#screenshots)
- [Login Comparison](#login-comparison)
- [Usage](#usage)
  - [Hosted Online](#hosted-online)
  - [Local Setup](#local-setup)
  - [Docker](#docker)
- [Future Goals](#future-goals)
- [Technical Documentation](#technical-documentation)
  - [Project Structure](#project-structure)
  - [High-Level-Flow](#high-level-flow)
    - [API Authentication Flow](#api-authentication-flow)
  - [API in Dev vs Prod](#api-in-dev-vs-prod)
    - [When nginx.conf is used](#when-nginxconf-is-used)
    - [Direct-to-Backend with CORS](#direct-to-backend-with-cors)
- [Legal Disclaimer](#legal-disclaimer)
- [License](#license)
- [Support](#support)

# Features

- **Authentication**: Multiple login options for flexibility:
  - **Hevy Credentials (OAuth2)**: Login with your Hevy username/email and password using OAuth2 with automatic reCAPTCHA v3 handling (no PRO membership required)
  - **Hevy PRO API Key**: Use your revokable Hevy PRO API key from [hevy.com/settings?developer](https://hevy.com/settings?developer)
  - **CSV Upload**: Upload your exported workout CSV file from the Hevy app
  - Authentication tokens are stored in **secure HttpOnly cookies** (not accessible to JavaScript, protecting against XSS attacks)
  - User preferences are stored in your browser's local storage
- **Dashboard**: Interactive charts and statistics of your workouts, including volume, muscle distribution and hours trained.
- **Workout History**: Workout logs with detailed exercise information up to the date of account creation - card or list design.
- **Exercises**: View all exercises with video thumbnails and detailed stats.
  - **Plateau Detection**: Automatically detects when your performance has plateaued on an exercise
  - **Strength Tracking**: Shows if you're gaining or losing strength over your recent sessions
  - **Multi-Vendor Support**: Track the same exercise even if trained with different vendors (e.g. Chest Flys from Gym A and Gym B) without mixing progress or stats.
- **Body Measurements**: Track your weight and body fat percentage over time with interactive charts.
- **Custom Settings**: Individualize your experience when using Hevy Insights.
- **Languages**: Language support for 🇺🇸, 🇩🇪 and 🇪🇸.

## Plateau & Strength Detection

Hevy Insights includes an intelligent analysis system that tracks your performance across the last 5 sessions (configurable) for each exercise and provides real-time feedback:

### Detection Types <!-- omit from toc -->

- **🟡 Plateau**: Your performance has stayed relatively consistent
  - Triggered when weight stays within **~0.5kg** and reps within **~1 rep** across at least 5 sessions
  
- **🟢 Gaining Strength**: You're making progress!
  - Triggered when weight increases by **>2kg** OR reps increase by **>2** (with stable/increasing weight) across at least 5 sessions
  
- **🔴 Declining Strength**: Performance is decreasing
  - Triggered when weight decreases by **>2kg** OR reps decrease by **>2** (with stable/ decreasing weight) across at least 5 sessions
  
- **⚪ Insufficient Data**: Not enough workout history yet
  - Displayed when an exercise has been performed fewer than **5 times**

### How It Works <!-- omit from toc -->

The analysis algorithm:

1. Collects data from your last N workout sessions for each exercise
2. Tracks the **maximum weight** and **reps at max weight** for each session
3. Compares the first half of sessions against the second half to identify trends
4. Displays a colored badge on each exercise card with the current status

This feature helps you identify when it's time to:

- **Increase weight** (when plateaued)
- **Celebrate progress** (when gaining)
- **Take recovery time** or **check form** (when declining)
- **Build more history** (when insufficient data)

## Multi-Vendor Support

It can happen that you train the same exercise (e.g. Chest Flys) in different gyms or with different equipment, which can lead to incorrect statistics because you are mixing two vendors together which may have a different weight progression. For example, you might have trained Chest Flys in Gym A which has a maximum weight of 80kg, and then you switch to Gym B which has a maximum weight of 110kg. 

If you mix the stats together, strength progression, personal records and other metrics will be skewed. In Hevy Insights you can create multiple vendors for the same exercise so that Hevy Insights can automatically assign each workout session to the correct vendor, so that you can track your progress accurately for each vendor without mixing them together.

[Image](/readme_images/exercises_multivendor.png)

# Screenshots

> [!NOTE]
> Screenshots as of **v1.3.0**

*Login Page*
![Login Page](/readme_images/login_page.png)

*Dashboard*
![Dashboard Page](/readme_images/dashboard_page.png)

*Workouts Page - Card Design*
![Workouts Page - Card Design](/readme_images/workout_page_card.png)

*Workouts Page - List Design*
![Workouts Page - List Design](/readme_images/workout_page_list.png)

---

# Login Comparison

You can decide based on your needs which login method suits you best:

> [!TIP]
> I recommed using the **Hevy Credentials Login** for the best experience since it shows the most data.

| Feature                      | Hevy Credentials Login       | Hevy PRO API Key Login       | CSV Upload                   |
| ---------------------------- | ---------------------------- | ---------------------------- | ---------------------------- |
| Requires Hevy PRO Membership | ✅ No                         | ❌ Yes                        | ✅ No                         |
| Data Freshness               | ✅ Live data from Hevy API    | ✅ Live data from Hevy API    | ❌ Static data from CSV file  |
| Data Range                   | ✅ Full history from Hevy API | ✅ Full history from Hevy API | ✅ Full history from CSV file |
| Personal Record Tracking     | ✅ Yes                        | ❌ No                         | ⚠️ Yes, but not in detail     |
| Muscle Distribution Data     | ✅ Yes                        | ❌ No                         | ⚠️ Not everything             |
| Media (Images/GIFs)          | ✅ Yes                        | ❌ No                         | ❌ No                         |
| Plateu Detection             | ✅ Yes                        | ✅ Yes                        | ✅ Yes                        |
| Workout Streaks              | ✅ Yes                        | ✅ Yes                        | ❌ No                         |
| Calories & Heart Rate Data   | ✅ Yes                        | ❌ No                         | ❌ No                         |
| Body Measurements            | ✅ Yes                        | ❌ No                         | ❌ No                         |
| Multi-Vendor Support         | ✅ Yes                        | ✅ Yes                        | ✅ Yes                        |

> [!IMPORTANT]
> **Why the differences in the login modes?** It's because not every login method provides the same data to use. The [Hevy PRO API](https://api.hevyapp.com/docs/#/) key login only provides data for a small amount of features compared to what you can see inside the Hevy app (which is using the **Hevy Credentials** login method). The CSV upload is the most basic one, it only provides the data that is contained in the CSV file you can export from the Hevy app, which is by far not everything that the Hevy API provides.

# Usage

You can either use Hevy Insights online or run it locally on your machine via multiple methods.

## Hosted Online

Navigate to the hosted version of Hevy Insights at: [https://hevy.kida.one](https://hevy.kida.one)

The latest version is always hosted there.

> [!IMPORTANT]
> **Authentication tokens** are stored in **secure HttpOnly cookies** on **your browser only**!
> These cookies are not accessible to JavaScript (XSS protection) and are automatically sent with API requests.  
> **User preferences** (theme, language, settings) are stored in your browser's local storage.

## Local Setup

Clone/download the repository and follow these steps:

1. Rename `.env.example` to `.env`.

2. Install the backend and frontend dependencies.

3. **Start the backend** (Terminal 1):

   `python backend/fastapi_server.py`

4. **Start the frontend** (Terminal 2):

   `cd frontend; npm run dev`

5. **Open your browser** and navigate to `http://localhost:5173`

6. **Login** with the desired login method.

## Docker

> [!NOTE]
> The front- and backend images are available for `linux/amd64` and `linux/arm64` architectures.

1. Run the containers:

  `docker-compose up -d`

  > [!NOTE]
  > You can find the [docker-compose.yaml](./docker-compose.yaml) file in the repository root folder.

2. Open your browser and navigate to `http://localhost:8123`

3. Login with the desired login method.

---

# Future Goals

- Better logging
- Add visual representation of trained muscle groups (body heatmap)
- In-depth muscle analysis page
- Remove emojis, use icons instead
- Resort/group CSS styles better
- Dashboard: Top stats: Display them more in rows instead of big "buttons". Maybe like "🏋️ 25 Total Workouts * 💪 282.741,5 kg Total Volume * ⏱️ 34h 15m Total Time Trained"
- CSV upload: PRs not shown and muscle regions missing
- To get more space on mobile: Dashboard charts: Hide Filters. Add something similar to the „i“ button which shows the filters
- Better tablet screen responsiveness
- Dashboard recent PRs: Add unit (seconds/formatted minutes) for "Best Duration" stat
- Workouts pages: PR "best duration" not localized and no unit shown
- Plateu detection not working correctly in Hevy PRO API key login mode
- Add ability on profile page to change account privacy settings (public/private) and opt-in/out of settings like "comments_push_enabled"
- "Clear all" button to flush localStorage?
- Switch `requests` library to `httpx` to be consistent?
- Let the user choose the primary and secondary colors in settings
- Switch to per page localization instead of using `global.{n}.{y}` and reusing the same string from other pages
- Support for distance-based workouts (running, cycling, etc.) and their specific stats (e.g., pace, distance)
  - Seperate distance stats for duraion-based workouts (e.g. Dead Hang)
- "Top 3 Best Sets" not actually showing the best sets for bodyweight exercises

---

# Technical Documentation

> [!NOTE]
> As of March 2026, **v1.8.6**

## Project Structure

```bash
hevy-insights/
├── backend/                   # Backend Components
│   ├── .dockerignore          # Docker ignore file for backend
│   ├── Dockerfile_backend     # Dockerfile for backend
│   ├── fastapi_server.py      # FastAPI server with REST endpoints
│   ├── hevy_api.py            # Hevy API module
│   ├── hevy_recaptcha.py      # reCAPTCHA v3 automation via Playwright
│   └── requirements.txt       # Python backend dependencies
└── frontend/                  # Frontend Components
    ├── public/                # Static assets
    ├── src/                   # Vue 3 TypeScript application
    │   ├── locales/           # i18n language files
    │   ├── router/            # Vue Router configuration with auth guards
    │   │   └── index.ts       # Router entry point
    │   ├── services/          # API communication layer (Axios)
    │   │   └── api.ts         # Axios instance and API functions
    │   ├── stores/            # Pinia store for state management
    │   │   └── hevy_cache.ts  # Hevy data caching
    │   ├── utils/             # Utility functions
    │   │   ├── csvCalculator.ts  # CSV data calculation 
    │   │   ├── csvParser.ts   # CSV data parsing
    │   │   ├── exerciseTypeDetector.ts  # Exercise type detection logic
    │   │   └── formatter.ts   # Data formatting functions
    │   ├── views/             # Page components (Login, Dashboard, Workouts, ...)
    │   ├── App.vue            # Root Vue component
    │   ├── main.ts            # Vue app entry point
    │   └── style.css          # Global styles
    ├── .dockerignore          # Docker ignore file for frontend
    ├── Dockerfile_frontend    # Dockerfile for frontend
    ├── index.html             # HTML entry point
    ├── nginx.conf             # Nginx configuration for production
    ├── package-lock.json      # npm package lock file
    ├── package.json           # Node.js dependencies
    ├── tsconfig.app.json      # TypeScript configuration for the app
    ├── tsconfig.json          # TypeScript configuration
    ├── tsconfig.node.json     # TypeScript configuration for Node.js
    └── vite.config.ts         # Vite build configuration
```

## High-Level-Flow

- **index.html**: Browser loads this HTML document first. It defines the root node `<div id="app"></div>` and includes `<script type="module" src="/src/main.ts">`.
- **main.ts**: Entry script runs. Vite serves ES modules and applies HMR in dev. We `createApp(App)`, install `Pinia` and the `Router`, then `mount("#app")`.
- **App.vue**: Root component renders the global shell (fixed sidebar + main). On mount and after each route change it checks `localStorage` for `hevy_access_token` to toggle sidebar visibility and protect routes.
- **Router**: Resolves the current URL (`/login`, `/dashboard`, `/workouts-card`, `/workouts-list`) and renders the matched view inside `<router-view />`. Auth guards check authentication status from backend via `/api/auth/status` endpoint.
- **View Components**: The matched page component (`Login.vue`, `Dashboard.vue`, `Workouts_Card.vue`, `.....vue`) runs `setup()` and lifecycle hooks (`onMounted`).
- **Pinia Store** (*frontend/src/stores/hevy_cache.ts*): Centralized state with 5‑minute caching for workouts (`workoutsLastFetched`). Exposes actions `fetchUserAccount()`, `fetchWorkouts(force)` and getters like `username`, `hasWorkouts`. Prevents redundant API calls when navigating.
- **Axios Service** (*frontend/src/services/api.ts*): Configures base URL with `withCredentials: true` for cookie support. Authentication is handled automatically via HttpOnly cookies set by the backend. All frontend API calls to the backend go through these typed helpers.
- **Backend** (FastAPI): Serves `/api` endpoints. Supports dual authentication (OAuth2 Bearer tokens or PRO API keys) via HttpOnly cookies. Proxies requests to the official Hevy API. Frontend receives JSON responses and Vue reactivity updates the UI.

### API Authentication Flow

**OAuth2 Authentication (Credentials):**

1. User logs in via `/api/login` endpoint with Hevy credentials
2. Backend automatically generates reCAPTCHA v3 token using Playwright (headless Chrome)
3. Backend authenticates with Hevy API using OAuth2 and receives `access_token` + `refresh_token`
4. Backend sets **HttpOnly cookies** (`hevy_access_token`, `hevy_refresh_token`, `hevy_token_expires_at`)
5. Browser automatically sends cookies with subsequent API requests
6. Backend reads authentication from cookies and proxies requests to Hevy API
7. On token expiration, backend automatically refreshes tokens via `/api/refresh_token` using refresh token cookie

**PRO API Key Authentication:**

1. User validates API key via `/api/validate_api_key` endpoint
2. Backend sets **HttpOnly cookies** (`hevy_api_key`, marker token)
3. Browser automatically sends cookies with subsequent API requests
4. Backend routes requests to Hevy PRO API endpoints

## API in Dev vs Prod

- In development, the frontend talks directly to the FastAPI server: the Axios base URL in [frontend/src/services/api.ts](frontend/src/services/api.ts) is `http://localhost:5000/api` when `import.meta.env.PROD` is false.
- In production, the Axios base URL is `/api` (same origin). Requests resolve as `https://your-domain/api/...` and are reverse‑proxied to the backend by Nginx.
- The `import.meta.env.PROD` flag is set automatically by Vite at build time. No extra configuration is required.

### When nginx.conf is used

- The file [frontend/nginx.conf](frontend/nginx.conf) is used when the built frontend is served by Nginx (e.g. on a server with Nginx).
- It performs two critical roles:
   - SPA fallback: routes like `/dashboard` and `/workouts-list` return `index.html` so client‑side routing works.
   - API proxy: requests to `/api/...` are forwarded to the FastAPI backend (e.g., `http://backend:5000`). This keeps a single public origin and avoids CORS in production.
- If your deployment does not use Nginx (e.g., serving static files from a CDN without proxying), ensure your hosting platform supports SPA fallback and adjust the API base accordingly.

### Direct-to-Backend with CORS

- In local development, the frontend dev server runs on `http://localhost:5173` and the backend on `http://localhost:5000`. Because these are different origins, FastAPI enables CORS middleware so the browser can call the backend directly.
- CORS setup in `fastapi_server.py`.
- In production behind Nginx, CORS is not required because the frontend and `/api` share the same origin.

# Legal Disclaimer

This project is not affiliated with or endorsed by Hevy or its parent company. It is a third-party application developed for personal use and educational purposes only. Users are responsible for complying with Hevy's terms of service when using this application. The developer assumes no liability for any issues arising from the use of this software.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Support

I work on this project in my free time and unpaid. If you find it useful and would like to support its development, consider buying me a coffee:

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/casudo)
