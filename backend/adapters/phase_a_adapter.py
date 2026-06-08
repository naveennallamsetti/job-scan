import logging
from backend.adapters.base import create_result_envelope

def run_phase_a_adapter(fetcher_func, *args, **kwargs):
    try:
        res = fetcher_func(*args, **kwargs)
        # Check if it already returned an envelope
        if isinstance(res, dict) and "status" in res:
            return res
        # If it returned a list, wrap it
        if not res:
            return create_result_envelope("NO_RESULTS", "phase_a", None, [])
        return create_result_envelope("SUCCESS", "phase_a", None, res)
    except Exception as e:
        return create_result_envelope("FAILED", "phase_a", str(e), [])
