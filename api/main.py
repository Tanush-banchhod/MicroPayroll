"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import payroll

app = FastAPI(
    title="MicroPayroll API",
    description=(
        "Open-source payroll engine for micro-businesses (2–10 employees). "
        "Handles salary calculation, Indian compliance (PF/ESIC/PT), "
        "and WhatsApp-based attendance."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payroll.router)


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    return {"status": "ok", "service": "micropayroll-api"}
