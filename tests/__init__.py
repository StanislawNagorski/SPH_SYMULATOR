# Test package — Phase 6 enforces SPHSIM_NO_REPORT=1 globally to prevent
# ./reports/ pollution during subprocess-based tests (RESEARCH §G.18, Pitfall 4).
# Module-level assignment runs once when unittest discovery imports tests.X.
import os
os.environ.setdefault('SPHSIM_NO_REPORT', '1')
