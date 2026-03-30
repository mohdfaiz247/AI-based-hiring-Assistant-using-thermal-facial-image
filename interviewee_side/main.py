#!/usr/bin/env python3
"""
AI Hiring Assistant - Application Entry Point

A PyQt6 desktop application for AI-powered recruitment workflow
with real-time computer vision capabilities.

All data is stored locally in ./user_data/{session_id}/
No external services or cloud storage are used.
"""

import sys
import os

# Add project root and interviewee_side to path for imports
_main_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_main_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _main_dir not in sys.path:
    sys.path.insert(0, _main_dir)

from src.app import run_app


if __name__ == "__main__":
    run_app()
