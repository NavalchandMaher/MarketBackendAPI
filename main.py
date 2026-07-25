from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.v3_routes import router as v3_router
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router

from contextlib import asynccontextmanager
from services.common.scheduler_service import SchedulerService


@asynccontextmanager
async def lifespan(app: FastAPI):

    SchedulerService.startup()

    yield

    SchedulerService.shutdown()


app = FastAPI(title="Market AI V2", version="3.0", lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://localhost:54646",  # Flutter web/devtools origin observed in UI
    "http://localhost:5000",  # Local Flutter web-server origin
    "http://127.0.0.1:5000",
    "http://localhost:10000",  # Backend origin
    "http://127.0.0.1:10000",
]

# Flutter web chooses an available development port unless one is supplied on
# the command line.  Keeping a fixed list here therefore causes authenticated
# mutations (such as POST /v3/strategies) to fail during the browser's CORS
# preflight request.  Limit the flexible rule to loopback hosts so this does
# not grant cross-origin access to arbitrary remote sites.
LOCAL_DEVELOPMENT_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(?::\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=LOCAL_DEVELOPMENT_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v3_router)
app.include_router(auth_router)
app.include_router(user_router)

# All V3 endpoints are now managed by v3_routes.py
# No duplicate endpoints here - router handles all /v3/* routes
