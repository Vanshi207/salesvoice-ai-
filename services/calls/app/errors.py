class TransientError(Exception):
    """A temporary failure (timeout, 429 rate limit, 5xx). Worth retrying later."""
