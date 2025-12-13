<div align="center">
  <img width="400" alt="Logo" src="readme_images/hevy_logo.webp"></a>
  <br>
  <h1>Hevy Insights</h1>
  This project is a used to gather data from Hevy API endpoints and visualize it in a web interface, acting as alternative for the Hevy PRO membership.

  ---

  <!-- Placeholder for badges -->
  ![GitHub License](https://img.shields.io/github/license/casudo/Hevy-Insights) ![GitHub release (with filter)](https://img.shields.io/github/v/release/casudo/Hevy-Insights) ![GitHub action checks](https://img.shields.io/github/check-runs/casudo/Hevy-Insights/main) ![GitHub issues](https://img.shields.io/github/issues/casudo/Hevy-Insights) ![GitHub last commit](https://img.shields.io/github/last-commit/casudo/Hevy-Insights)
</div>

> [!NOTE]
> This is a hobby project. Feel free to create issues and contribute.

# About Hevy Insights <!-- omit from toc -->

Hevy Insights is a dynamic web application that provides insights and analytics of your workouts and exercises. It visualizes workout data from the Hevy app in a clean dashboard so that you can always keep track of your progress!

In the Hevy app you can only see your stats and progress up to 3 months for free, otherwise you need the paid Hevy PRO membership.
Hevy Insights allows you to log in with your Hevy credentials and fetch your workout data directly from Hevy's API, providing you with detailed visualizations and historical data up to the date of your account creation - no PRO membership required!

# Table of Contents <!-- omit from toc -->

- [Features](#features)
- [Screenshots](#screenshots)
- [Usage](#usage)
  - [Hosted Online](#hosted-online)
  - [Local Setup](#local-setup)
- [Future Goals](#future-goals)
- [Technical Documentation](#technical-documentation)
  - [Project Structure](#project-structure)
    - [File Descriptions](#file-descriptions)
      - [Backend Files](#backend-files)
      - [Frontend Files](#frontend-files)
    - [Documentation \& Configuration](#documentation--configuration)
  - [High-Level-Flow](#high-level-flow)
    - [Authentication Flow](#authentication-flow)
  - [API in Dev vs Prod](#api-in-dev-vs-prod)
    - [When nginx.conf is used](#when-nginxconf-is-used)
    - [Direct-to-Backend with CORS](#direct-to-backend-with-cors)
- [Development](#development)
  - [Swagger Documentation](#swagger-documentation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Legal Disclaimer](#legal-disclaimer)
- [License](#license)

# Features

- **Authentication**: Login with Hevy credentials (no Hevy PRO membership required!). Credentials are stored in your browser's local storage **only**.
- **Dashboard**: Interactive charts and statistics of your workouts, including volume, muscle distribution and hours trained.
- **Workout History**: Workout logs with detailed exercise information up to the date of account creation - card or list design.

# Screenshots

> [!NOTE]
> Screenshots as of **v1.0.0**

*Login Page*
![Login Page](/readme_images/login_page.png)

*Dashboard*
![Dashboard Page](/readme_images/dashboard_page.png)

*Workouts Page - Card Design*
![Workouts Page - Card Design](/readme_images/workout_page_card.png)

*Workouts Page - List Design*
![Workouts Page - List Design](/readme_images/workout_page_list.png)

# Usage

You can either use Hevy Insights online or run it locally on your machine.

## Hosted Online

Navigate to the hosted version of Hevy Insights at: [https://hevy.kida.one](https://hevy.kida.one)

The latest version is always hosted there.

> [!IMPORTANT]
> **Only** your Hevy API token is stored **at your own browser's local storage**. No other data is stored!

## Local Setup

Clone/download the repository and follow these steps:

0. Install the backend and frontend dependencies as described in the [Development](#development) section below.

1. **Start the backend** (Terminal 1):

   `python backend/fastapi_server.py`

2. **Start the frontend** (Terminal 2):

   `cd frontend; npm run dev`

3. **Open your browser** and navigate to `http://localhost:5173`

4. **Login** with your Hevy username/email and password

---

# Future Goals

- Display time on Workout cards like "1h 15m" instead of "75 minutes"
- Translations for other languages
- Settings page where the user can select translations and other preferences (date format, theme, etc.)
- Better logging

---

# Technical Documentation

> [!NOTE]
> As of 13.12.2025, **v1.1.0**

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
    │   ├── router/            # Vue Router configuration with auth guards
    │   │   └── index.ts       # Router entry point
    │   ├── services/          # API communication layer (Axios)
    │   │   ├── api.ts         # Axios instance and API functions
    │   ├── stores/            # Pinia store for state management
    │   │   └── hevy_cache.ts  # Hevy data caching
    │   ├── views/             # Page components (Login, Dashboard, Workouts)
    │   │   ├── Dashboard.vue  # Dashboard page
    │   │   ├── Exercises.vue  # Exercises page
    │   │   ├── Login.vue      # Login page
    │   │   ├── Workouts_Card.vue   # Workouts page (card design)
    │   │   └── Workouts_List.vue   # Workouts page (list design)
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

### File Descriptions

#### Backend Files

- **`fastapi_server.py`**: FastAPI REST API server with multiple endpoints. Uses Pydantic models for request/response validation and provides auto-generated API docs at `/api/docs`.
- **`hevy_api.py`**: Hevy API module with `HevyClient` class, `HevyConfig` for configuration, and `HevyError` exception. Handles API requests/responses against the official Hevy API.
- **`requirements.txt`**: Python backend package dependencies.

#### Frontend Files

- **`src/router/index.ts`**: Vue Router configuration with navigation guards to protect authenticated routes.
- **`src/services/api.ts`**: Centralized API communication layer using Axios with automatic auth token injection against the Hevy Insights API backend.
- **`src/stores/hevy_cache.ts`**: Pinia store for caching Hevy API data with a 5-minute TTL.
- **`src/views/Dashboard.vue`**: Main dashboard with Chart.js visualizations (volume over time, muscle group distribution) and workout metrics.
- **`src/views/Exercises.vue`**: Exercises page with video thumbnails and detailed exercise stats.
- **`src/views/Login.vue`**: Login page with form for Hevy credentials, stores auth token in localStorage.
- **`src/views/Workouts_Card.vue`**: Paginated workout history browser with detailed exercise information (sets, reps, weight, RPE).
- **`src/views/Workouts_List.vue`**: Alternative workout history browser in list design.
- **`src/App.vue`**: Root component with navigation bar and router view.
- **`src/main.ts`**: Vue application initialization and router setup.
- **`src/style.css`**: Global styles for the application.
- **`index.html`**: HTML entry point.
- **`nginx.conf`**: Nginx configuration for serving the built frontend in production mode with SPA fallback and API proxying.
- **`package-lock.json`**: npm package lock file.
- **`package.json`**: Node.js dependencies (Vue 3, Vue Router, Axios, Chart.js, TypeScript, Vite).

### Documentation & Configuration

- **`swagger/swagger.yaml`**: OpenAPI specification documenting all official Hevy API endpoints, request/response schemas, and authentication requirements.
- **`.markdownlint.json`**: Configuration for Markdown linting rules. VS Code extension ID: [DavidAnson.vscode-markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)
- **`ruff.toml`**: Configuration file for Ruff, Python linter and formatter.

## High-Level-Flow

- **index.html**: Browser loads this HTML document first. It defines the root node `<div id="app"></div>` and includes `<script type="module" src="/src/main.ts">`.
- **main.ts**: Entry script runs. Vite serves ES modules and applies HMR in dev. We `createApp(App)`, install `Pinia` and the `Router`, then `mount("#app")`.
- **App.vue**: Root component renders the global shell (fixed sidebar + main). On mount and after each route change it checks `localStorage` for `hevy_auth_token` to toggle sidebar visibility and protect routes.
- **Router**: Resolves the current URL (`/login`, `/dashboard`, `/workouts-card`, `/workouts-list`) and renders the matched view inside `<router-view />`. Auth guards prevent accessing protected routes without a token.
- **View Components**: The matched page component (`Login.vue`, `Dashboard.vue`, `Workouts_Card.vue`, `Workouts_List.vue`) runs `setup()` and lifecycle hooks (`onMounted`).
   - **Login.vue**: Handles credential input and calls `authService.login()`. On success, stores `auth_token` in `localStorage` and redirects to `/dashboard`.
   - **Dashboard.vue**: Displays various statistics and charts about the user's workouts.
   - **Workouts_Card.vue**: Paginated card view of workouts with stats, description, per-exercise details (sets, reps, weight, RPE) and PR summaries on expanded exercises.
   - **Workouts_List.vue**: Alternative expandable list view with of the user's workouts.
   - **Exercises.vue**: Shows a list of exercises with video thumbnails and stats.
- **Pinia Store** (*frontend/src/stores/hevy_cache.ts*): Centralized state with 5‑minute caching for workouts (`workoutsLastFetched`). Exposes actions `fetchUserAccount()`, `fetchWorkouts(force)` and getters like `username`, `hasWorkouts`. Prevents redundant API calls when navigating.
- **Axios Service** (*frontend/src/services/api.ts*): Configures base URL and injects the `auth-token` header via interceptors. All frontend API calls to the backend go through these typed helpers.
- **Backend** (FastAPI): Serves `/api` endpoints. Validates `auth-token` and proxies requests to the official Hevy API. Frontend receives JSON responses and Vue reactivity updates the UI.

### Authentication Flow

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
- Typical CORS setup (illustrative) in `fastapi_server.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
)
```

- In production behind Nginx, CORS is not required because the frontend and `/api` share the same origin.

# Development

> [!IMPORTANT]
> If you are interested in contributing to the development of Hevy Insights, please create an issue and submit a pull request.
> For other inquiries, feel free to contact me -> [casudo](https://github.com/casudo)

Clone/download the repository and follow the steps below.

## Swagger Documentation

The OpenAPI specification for the Hevy API endpoints is located in `docs/swagger.yaml`.
You can see it online via [my GitHub Pages](https://casudo.github.io/Hevy-Insights).

## Backend Setup

1. Optional, but recommended: Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install backend dependencies:

   ```bash
   pip install -r backend\requirements.txt
   ```

3. Run the FastAPI backend:

   ```bash
   python backend/fastapi_server.py
   ```

   FastAPI endpoint documentation: `http://localhost:5000/api/docs`

## Frontend Setup

**Prerequisites**:

- Install [Node.js](https://nodejs.org/) (v24 or higher)
- Install [npm](https://www.npmjs.com/get-npm) (comes with Node.js, v11 or higher)

1. Navigate to frontend directory and install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Run the Vue development server:

   ```bash
   npm run dev
   ```

   Frontend will run on `http://localhost:5173`

# Legal Disclaimer

This project is not affiliated with or endorsed by Hevy or its parent company. It is a third-party application developed for personal use and educational purposes only. Users are responsible for complying with Hevy's terms of service when using this application. The developer assumes no liability for any issues arising from the use of this software.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
