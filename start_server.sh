#!/bin/sh
cd "$(dirname "$0")"
exec /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m uvicorn main:app --port 8006
