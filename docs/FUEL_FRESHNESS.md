# Fuel feed cache lifetime

The original cache kept the first successful download until FuelLoc exited. A long-running app therefore kept returning old prices even when the user changed filters or reloaded the page.

FuelLoc now reuses a successful download for at most five minutes. After that, the next fuel request downloads the feed again. Reloading the workspace, changing region/type, or turning fuel mode off and on makes fuel requests. There is no background polling, and an unchanged displayed price does not update by itself.

This bounds local caching, not the reporting delay in the upstream feed. Five minutes is a local reuse policy, not a claim about the feed's update interval. A failed refresh clears the expired cache and uses the existing unavailable-feed UI; it does not present expired data as a successful new lookup. The next request can retry immediately. A lock prevents simultaneous local requests from racing cache replacement.

Run `python -m unittest discover -s tests -p test_fuel_cache.py` to verify fresh reuse, expiry, failure without stale fallback, and recovery with a controlled monotonic clock and in-memory feed. Both expiry tests failed against the original process-lifetime cache.
