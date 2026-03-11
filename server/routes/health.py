"""
Health, status, and log inspection endpoints.
"""

from fastapi import APIRouter, Query

from server.config import FEATURE_NAMES
from server.utils.logging import read_log
from server.utils.stats import compute_stats

router = APIRouter()

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100


@router.get("/")
async def root():
    return {"status": "ok", "message": "IDS middleware is active"}


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": True,
        "binary_model": "rf_model.joblib",
        "feature_count": len(FEATURE_NAMES),
    }


@router.get("/logs/stats")
async def get_stats():
    return compute_stats(read_log())


@router.get("/logs")
async def get_logs(
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-based)",
    ),
    page_size: int = Query(
        PAGE_SIZE_DEFAULT,
        ge=1,
        le=PAGE_SIZE_MAX,
        description=f"Entries per page (max {PAGE_SIZE_MAX})",
    ),
    classification: str | None = Query(
        None,
        description="Filter by binary result: 'Normal' or 'Attack'",
    ),
    client_ip: str | None = Query(
        None,
        description="Filter by exact client IP address",
    ),
    search: str | None = Query(
        None,
        description="Substring search across endpoint and client_ip",
    ),
    sort: str = Query(
        "desc",
        description="Sort by timestamp: 'asc' or 'desc'",
    ),
):
    """Return paginated IDS detection log entries."""
    logs = read_log()

    # ── Filters ──────────────────────────────────────────────
    if classification:
        logs = [e for e in logs if e["binary_classification"] == classification]

    if client_ip:
        logs = [e for e in logs if e["client_ip"] == client_ip]

    if search:
        q = search.lower()
        logs = [
            e for e in logs
            if q in e["endpoint"].lower() or q in e["client_ip"].lower()
        ]

    # ── Sort ─────────────────────────────────────────────────
    if sort == "desc":
        logs = list(reversed(logs))

    # ── Pagination ───────────────────────────────────────────
    total = len(logs)
    total_pages = max(1, -(-total // page_size))   # ceiling division
    page = min(page, total_pages)                   # clamp to valid range
    offset = (page - 1) * page_size
    entries = logs[offset: offset + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "entries": entries,
    }
