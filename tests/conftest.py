"""Phase 6 — pytest conftest (compatibility safety-net).

Sets SPHSIM_NO_REPORT=1 for any pytest-based test run so future migration
away from unittest does not regress on the test-pollution prophylaxis.
Current test runner is unittest; this file is harmless if pytest is not
installed (Python simply does not import it).

See RESEARCH §G.18 Rozwiązanie 1 — Env var (PREFEROWANE).
"""
import os

os.environ.setdefault('SPHSIM_NO_REPORT', '1')
