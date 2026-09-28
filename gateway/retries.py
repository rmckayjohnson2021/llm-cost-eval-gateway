RETRYABLE_ERRORS = {"timeout", "rate_limit", "provider_outage"}


def is_retryable(error_type: str | None) -> bool:
    return error_type in RETRYABLE_ERRORS
