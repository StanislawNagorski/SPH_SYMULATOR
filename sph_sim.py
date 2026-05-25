#!/usr/bin/env python3
"""SPH Mediation Simulator — thin shim, full code in sphsim/ package.

UŻYCIE:
  python sph_sim.py --strategy <NAZWA> [opcje]
  python -m sphsim --strategy <NAZWA> [opcje]   # alternatywny entry point

Pełna dokumentacja: sphsim/cli/args.py docstring (visible via --help).
"""
from sphsim.cli.main import main

if __name__ == '__main__':
    main()
