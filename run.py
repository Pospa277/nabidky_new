#!/usr/bin/env python3
"""Spouštěcí skript pro nabídkový generátor."""
import os
import uvicorn

if __name__ == "__main__":
    # Zajistí správný working directory, i když spouštíte odjinud
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
