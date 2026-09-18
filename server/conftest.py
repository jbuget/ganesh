"""Root pytest configuration: makes the src package importable.

`holidays` emits an informational warning about its future versioning strategy
when imported. We import it here once, silently, to keep a clean test output
without muffling the project's own warnings.
"""

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import holidays  # noqa: F401
