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
  - [Swagger Documentation](#swagger-documentation)

## Translations

If you want to improve current translations or add new languages, you can do so by editing the JSON files located in the `frontend/src/locales/` directory.

To add a new language, copy the default `en.json` file and rename it to the desired [ISO-639-1 language code](https://en.wikipedia.org/wiki/ISO_639-1) (e.g., `pt.json` for Portuguese). Then, translate the strings accordingly.

> [!WARNING]
> You must be able to read the original strings in English to provide accurate translations.

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

3. Run the FastAPI backend:

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

### Swagger Documentation

The OpenAPI specification for the Hevy API endpoints is located in `docs/swagger.yaml`.
You can see it online via [my GitHub Pages](https://casudo.github.io/Hevy-Insights).