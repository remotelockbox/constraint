#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'constraint'))

from constraint.cli import entry

entry()
