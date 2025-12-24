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
- [Screenshots](#screenshots)
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

- **Authentication**: Either login with Hevy credentials (no Hevy PRO membership required! Credentials are stored in your browser's local storage **only**) or upload your exported workout CSV file from Hevy.
- **Dashboard**: Interactive charts and statistics of your workouts, including volume, muscle distribution and hours trained.
- **Workout History**: Workout logs with detailed exercise information up to the date of account creation - card or list design.
- **Exercises**: View all exercises with video thumbnails and detailed stats.
  - **Plateau Detection**: Automatically detects when your performance has plateaued on an exercise
  - **Strength Tracking**: Shows if you're gaining or losing strength over your recent sessions
- **Custom Settings**: Individualize your experience when using Hevy Insights.
- **Languages**: Language support for 🇺🇸, 🇩🇪 and 🇪🇸.

## Plateau & Strength Detection

Hevy Insights includes an intelligent analysis system that tracks your performance across the **last 5 sessions** for each exercise and provides real-time feedback:

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

1. Collects data from your last 5 workout sessions for each exercise
2. Tracks the **maximum weight** and **reps at max weight** for each session
3. Compares the first half of sessions against the second half to identify trends
4. Displays a colored badge on each exercise card with the current status

This feature helps you identify when it's time to:

- **Increase weight** (when plateaued)
- **Celebrate progress** (when gaining)
- **Take recovery time** or **check form** (when declining)
- **Build more history** (when insufficient data)

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

# Usage

You can either use Hevy Insights online or run it locally on your machine via multiple methods.

## Hosted Online

Navigate to the hosted version of Hevy Insights at: [https://hevy.kida.one](https://hevy.kida.one)

The latest version is always hosted there.

> [!IMPORTANT]
> **Only** your Hevy API token is stored **at your own browser's local storage**. No other data is stored!

## Local Setup

Clone/download the repository and follow these steps:

1. Rename `.env.example` to `.env`.

2. Install the backend and frontend dependencies.

3. **Start the backend** (Terminal 1):

   `python backend/fastapi_server.py`

4. **Start the frontend** (Terminal 2):

   `cd frontend; npm run dev`

5. **Open your browser** and navigate to `http://localhost:5173`

6. **Login** with your Hevy username/email and password

## Docker

1. Build the Docker images:

  `docker build -f backend/Dockerfile_backend -t casudo/hevy-insights-backend:latest .`

  `docker build -f frontend/Dockerfile_frontend -t casudo/hevy-insights-frontend:latest .`

1. Run the containers:

  `docker-compose up -d`

  > [!NOTE]
  > You can find the [docker-compose.yaml](./docker-compose.yaml) file in the repository root folder.

---

# Future Goals

- Better logging
- Replace localStorage with HTTP cookie
- Handle exercises with time (planks, jogging)
- On page switch, start at the top and not on the height where the user previously left the other page
- CSV upload: PRs not shown and muscle regions missing
- Mobile: Shrink login mode buttons
- Mobile: After logging in, the website appears to be zoomed in

---

# Technical Documentation

> [!NOTE]
> As of 19.12.2025, **v1.3.0**

## Project Structure

```bash
hevy-insights/
├── backend/                   # Backend Components
│   ├── fastapi_server.py      # FastAPI server with REST endpoints
│   ├── hevy_api.py            # Hevy API module
│   └── requirements.txt       # Python backend dependencies
└── frontend/                  # Frontend Components
    ├── public/                # Static assets
    ├── src/                   # Vue 3 TypeScript application
    │   ├── locales/          # i18n language files
    │   ├── router/            # Vue Router configuration with auth guards
    │   │   └── index.ts       # Router entry point
    │   ├── services/          # API communication layer (Axios)
    │   │   └── api.ts         # Axios instance and API functions
    │   ├── stores/            # Pinia store for state management
    │   │   └── hevy_cache.ts  # Hevy data caching
    │   ├── utils/             # Utility functions
    │   │   ├── csvCalculator.ts  # CSV data calculation 
    │   │   └── csvParser.ts   # CSV data parsing
    │   ├── views/             # Page components (Login, Dashboard, Workouts, ...)
    │   ├── App.vue            # Root Vue component
    │   ├── main.ts            # Vue app entry point
    │   └── style.css          # Global styles
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
- **App.vue**: Root component renders the global shell (fixed sidebar + main). On mount and after each route change it checks `localStorage` for `hevy_auth_token` to toggle sidebar visibility and protect routes.
- **Router**: Resolves the current URL (`/login`, `/dashboard`, `/workouts-card`, `/workouts-list`) and renders the matched view inside `<router-view />`. Auth guards prevent accessing protected routes without a token.
- **View Components**: The matched page component (`Login.vue`, `Dashboard.vue`, `Workouts_Card.vue`, `.....vue`) runs `setup()` and lifecycle hooks (`onMounted`).
- **Pinia Store** (*frontend/src/stores/hevy_cache.ts*): Centralized state with 5‑minute caching for workouts (`workoutsLastFetched`). Exposes actions `fetchUserAccount()`, `fetchWorkouts(force)` and getters like `username`, `hasWorkouts`. Prevents redundant API calls when navigating.
- **Axios Service** (*frontend/src/services/api.ts*): Configures base URL and injects the `auth-token` header via interceptors. All frontend API calls to the backend go through these typed helpers.
- **Backend** (FastAPI): Serves `/api` endpoints. Validates `auth-token` and proxies requests to the official Hevy API. Frontend receives JSON responses and Vue reactivity updates the UI.

### API Authentication Flow

1. User logs in via `/api/login` endpoint with Hevy credentials
2. Backend receives `auth_token` from Hevy API
3. Frontend stores token in localStorage
4. Subsequent API requests include token in `auth-token` header
5. Backend uses token to authenticate requests to Hevy API  

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
