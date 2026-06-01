from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter instance imported by both main.py (for wiring)
# and routes/sentiment.py (for the @limiter.limit decorators).
# Keeping it in its own module avoids circular imports.
limiter = Limiter(key_func=get_remote_address)
