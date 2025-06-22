"""
Configuration file untuk TA Daily Process Tool
"""

import os

# Default output path untuk hasil pemrosesan
DEFAULT_OUTPUT_PATH = os.path.join(os.getcwd(), "output")

# Database configuration (sudah ada di TA_daily_process_module.py)
# Bisa ditambahkan konfigurasi lain di sini jika diperlukan

# GUI Settings
GUI_TITLE = "TA Daily Process Tool - Telkomsel"
GUI_VERSION = "1.0"
GUI_WIDTH = 800
GUI_HEIGHT = 700

# Colors (Telkomsel theme)
HEADER_COLOR = "#FF6B35"  # Orange Telkomsel
BUTTON_COLOR = "#5E81AC"  # Blue
SUCCESS_COLOR = "#A3BE8C"  # Green 