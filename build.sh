#!/bin/sh

if [ ! -d venv ]; then
  python3.9 -m venv venv
fi

source venv/bin/activate
pip3.9 install -r requirements.txt
