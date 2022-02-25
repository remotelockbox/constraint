#!/bin/sh

if [ -d venv ]; then
  source venv/bin/activate
fi

python3.9 -m constraint.cli $*
