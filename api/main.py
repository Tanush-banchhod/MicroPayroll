"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import payroll
from api.routers import companies, employees, attendance, payroll_runs

app = FastAPI(
    title="MicroPayroll API",
    description=(
        "Open-source payroll engine for micro-businesses (2–10 employees). "
        "Handles salary calculation, Indian compliance (PF/ESIC/PT), "
        "and WhatsApp-based attendance."
    ),
    version="0.2.0",
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
app.include_router(companies.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(payroll_runs.router)


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    return {"status": "ok", "service": "micropayroll-api"}
