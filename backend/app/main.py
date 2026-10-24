from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, mailboxes, leads, campaigns, stats, tracking

app = FastAPI(title="Cold Email System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mailboxes.router)
app.include_router(leads.router)
app.include_router(campaigns.router)
app.include_router(stats.router)
app.include_router(tracking.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
