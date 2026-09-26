from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limiter. Note for Render deployments:
# If scaled to multiple instances, rate limits will be tracked per-instance
# since we are not using a shared Redis store. For stricter limits, a shared store is needed.
limiter = Limiter(key_func=get_remote_address)
