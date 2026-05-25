import time
from contextlib import contextmanager

@contextmanager
def timed(label: str):
    start = time.perf_counter()
    yield
    print(f"{label} took {time.perf_counter() - start:.4f} seconds")
