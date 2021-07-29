#!/usr/bin/env python3.9

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from constraint.cli import entry

if __name__ == '__main__':
    entry()