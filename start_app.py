#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Startskript

Dette skriptet starter applikasjonen.
"""

import sys
import os

# Legg til gjeldende mappe til sys.path hvis den ikke allerede er der
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Start applikasjonen
from app import main
if __name__ == "__main__":
    main() 