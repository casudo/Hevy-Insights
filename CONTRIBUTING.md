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
