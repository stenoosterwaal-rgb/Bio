from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app import database
from app.routers import topics, exams, attempts, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="VWO Bio Tracker", lifespan=lifespan)

app.include_router(topics.router,    prefix="/api/topics",    tags=["topics"])
app.include_router(exams.router,     prefix="/api/exams",     tags=["exams"])
app.include_router(attempts.router,  prefix="/api/attempts",  tags=["attempts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

app.mount("/", StaticFiles(directory="static", html=True), name="static")
