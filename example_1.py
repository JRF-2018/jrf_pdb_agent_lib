#!/usr/bin/python3
__version__ = '0.0.1' # Time-stamp: <2025-05-28T13:50:59Z>

import jrf_pdb_agent_lib as pal

pal.login()

x = 42

r = pal.do("Do something good.")

print(r)
