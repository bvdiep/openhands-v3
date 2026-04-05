import time
import threading
from collections import defaultdict

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)  # key -> [timestamps]
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            # Clean old entries
            self._requests[key] = [
                t for t in self._requests[key]
                if now - t < self.window_seconds
            ]
            if len(self._requests[key]) >= self.max_requests:
                return True
            self._requests[key].append(now)
            return False

# Pre-configured limiters
login_limiter = RateLimiter(max_requests=5, window_seconds=60)    # 5 attempts per minute
api_limiter = RateLimiter(max_requests=30, window_seconds=60)     # 30 requests per minute
