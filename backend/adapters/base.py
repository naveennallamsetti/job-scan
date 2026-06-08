import time

def normalize_fetch_output(result, source, latency_ms=0):
    if isinstance(result, dict) and "status" in result:
        return result

    if isinstance(result, list):
        return {
            "status": "SUCCESS" if len(result) > 0 else "NO_RESULTS",
            "source": source,
            "reason": None,
            "jobs": result,
            "metadata": {
                "job_count": len(result),
                "latency_ms": latency_ms
            }
        }

    return {
        "status": "FAILED",
        "source": source,
        "reason": "INVALID_RETURN_TYPE",
        "jobs": [],
        "metadata": {
            "job_count": 0,
            "latency_ms": latency_ms
        }
    }

def run_adapter(fetcher_func, source_name, *args, **kwargs):
    start_time = time.time()
    try:
        res = fetcher_func(*args, **kwargs)
        latency = int((time.time() - start_time) * 1000)
        return normalize_fetch_output(res, source_name, latency)
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "status": "FAILED",
            "source": source_name,
            "reason": str(e),
            "jobs": [],
            "metadata": {
                "job_count": 0,
                "latency_ms": latency
            }
        }
