"""
Minimal in-process failed-attempt limiter for the login endpoint.

No Redis in this deployment, so this is per-worker state: with 2 uvicorn
workers the effective threshold is ~2x MAX_ATTEMPTS and it resets on
restart. That's fine for its job - it turns "unlimited password guesses"
into "a dozen, then locked for 15 minutes", which stops online brute
force without needing shared infrastructure.
"""
import threading
import time

MAX_ATTEMPTS = 6
WINDOW_SECONDS = 15 * 60

_lock = threading.Lock()
_failures: dict[str, list[float]] = {}


def _recent(key: str, now: float) -> list[float]:
    times = [t for t in _failures.get(key, ()) if now - t < WINDOW_SECONDS]
    if times:
        _failures[key] = times
    else:
        _failures.pop(key, None)
    return times


def is_locked(key: str) -> bool:
    with _lock:
        return len(_recent(key, time.time())) >= MAX_ATTEMPTS


def record_failure(key: str) -> None:
    with _lock:
        now = time.time()
        times = _recent(key, now)
        times.append(now)
        _failures[key] = times


def clear(key: str) -> None:
    with _lock:
        _failures.pop(key, None)


def client_ip(request) -> str:
    """Real client IP - Render (and most PaaS) put it first in
    X-Forwarded-For; request.client.host would be the load balancer."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
