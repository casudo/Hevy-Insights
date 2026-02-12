# Contributing to Hevy Insights <!-- omit from toc -->

Thanks for your potential interest in contributing to Hevy Insights! There are several ways you can help improve the project, whether it's through code contributions, documentation, bug reports, or feature requests.

> [!IMPORTANT]
> Even if you are not a developer you can contribute by adding new languages and help with translations. See [more info here](#translations).

## Table of Contents <!-- omit from toc -->

- [Translations](#translations)
- [Development](#development)
  - [Setup development environment](#setup-development-environment)
    - [Backend Setup](#backend-setup)
    - [Frontend Setup](#frontend-setup)
  - [Playwright for reCAPTCHA Automation](#playwright-for-recaptcha-automation)
    - [What does Playwright do?](#what-does-playwright-do)
    - [Performance Considerations](#performance-considerations)
  - [Swagger Documentation](#swagger-documentation)

## Translations

To add a new language to Hevy Insights, follow these steps:

1. **Create Language File**

   - Add a new JSON file in `frontend/src/locales/` (e.g., `fr.json` for French). Filename must be in [ISO-639-1 language code](https://en.wikipedia.org/wiki/ISO_639-1) format.
   - Copy the structure from `en.json` and translate all strings
   - Follow the nested structure: `dashboard`, `exercises`, `workouts`, `...`.

   > [!WARNING]
   > You must be able to read the original strings in English to provide accurate translations.

2. **Register Language in Index**
   - Open `frontend/src/locales/index.ts`
   - Import your language file: `import fr from './fr.json';`
   - Add it to the messages object: `messages: { en, de, es, fr }`

3. **Update Settings Component**
   - Open `frontend/src/views/Settings.vue`
   - Add your language to the language selector dropdown
   - Include the flag emoji and native language name

4. **Handle Exercise Localization**
   - Hevy API provides localized exercise titles (e.g. `de_title` and `es_title`)
   - For new languages, add a corresponding field pattern (e.g. `fr_title`)
   - Update these files to check for the new field:
     - `frontend/src/views/Dashboard.vue` - plateauExercises & recentPRs computed property
     - `frontend/src/views/Exercises.vue` - getLocalizedTitle() function
   - The pattern matches the language code: if locale is "fr", check for `fr_title`

5. **Test Thoroughly**
   - Verify all UI strings are translated
   - Check that exercise names display correctly
   - Test language switching in Settings
   - Confirm plateau navigation works with localized exercise names

**Example for French:**

```typescript
// In getLocalizedTitle() or plateauExercises:
if (locale === "fr" && exercise.fr_title) {
  localizedTitle = exercise.fr_title;
}
```

Once you're done commit your changes and create a pull request.

## Development

> [!IMPORTANT]
> If you are interested in contributing to the development of Hevy Insights, please create an issue and submit a pull request.
> For other inquiries, feel free to contact me -> [casudo](https://github.com/casudo)

Clone/download the repository and follow the [Setup development environment](#setup-development-environment) guide.

### Setup development environment

#### Backend Setup

1. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install backend dependencies:

   ```bash
   pip install -r backend\requirements.txt
   ```

3. Install Playwright and browser binaries (for reCAPTCHA automation):

   ```bash
   playwright install chromium
   ```

   > [!NOTE]
   > The `playwright install chromium` command downloads the Chromium browser (~300MB). This only needs to be done once per environment.

4. Run the FastAPI backend:

   ```bash
   python backend/fastapi_server.py
   ```

   FastAPI endpoint documentation: `http://localhost:5000/api/docs`

#### Frontend Setup

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

### Playwright for reCAPTCHA Automation

Hevy Insights uses [Playwright](https://playwright.dev/) to automate reCAPTCHA v3 token generation during OAuth2 login. This section covers how to work with Playwright during development.

#### What does Playwright do?

The `backend/hevy_recaptcha.py` module uses Playwright to:

1. Launch a headless Chrome browser
2. Navigate to Hevy's login page
3. Execute JavaScript to generate/fetch a reCAPTCHA v3 Enterprise token
4. Return the token to the backend for authentication

This happens automatically when users log in with Hevy credentials.

#### Performance Considerations

- **Browser Reuse**: Playwright browser stays open during FastAPI's lifetime (not launched per request)
- **Token Caching**: reCAPTCHA tokens are cached for 15 seconds to reduce browser usage
- **Cache Invalidation**: Cache is cleared after each login attempt to prevent token reuse errors

### Swagger Documentation

The OpenAPI specification for the Hevy API endpoints is located in `docs/swagger.yaml`.
You can see it online via [my GitHub Pages](https://casudo.github.io/Hevy-Insights).
