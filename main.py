from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from db.mongodb import learning_logs
from services.signal_engine import analyze_market
from routes.v3_routes import router as v3_router
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router

from services.backtester import BackTester
from db.mongodb import backtest_results

from contextlib import asynccontextmanager
from services.scheduler_service import SchedulerService


from db.mongodb import paper_trades, closed_trades
from services.performance_service import PerformanceService

from services.learning_engine import LearningEngine
from services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):

    SchedulerService.startup()

    yield

    SchedulerService.shutdown()


app = FastAPI(title="Market AI V2", version="3.0", lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://localhost:54646",  # Flutter web/devtools origin observed in UI
    "http://localhost:10000",  # Backend origin
    "http://127.0.0.1:10000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v3_router)
app.include_router(auth_router)
app.include_router(user_router)

# All V3 endpoints are now managed by v3_routes.py
# No duplicate endpoints here - router handles all /v3/* routes
