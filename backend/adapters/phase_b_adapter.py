import logging
from backend.adapters.base import create_result_envelope

def run_phase_b_adapter(fetcher_func, *args, **kwargs):
    try:
        res = fetcher_func(*args, **kwargs)
        if isinstance(res, dict) and "status" in res:
            return res
        if not res:
            return create_result_envelope("NO_RESULTS", "phase_b", None, [])
        return create_result_envelope("SUCCESS", "phase_b", None, res)
    except Exception as e:
        return create_result_envelope("FAILED", "phase_b", str(e), [])
