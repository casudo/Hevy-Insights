from fastapi import APIRouter

from app.api.routes import auth, body_measurements, system, user, workouts


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(workouts.router)
api_router.include_router(body_measurements.router)
api_router.include_router(system.router)
