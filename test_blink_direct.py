#!/usr/bin/env python3
"""
Debug test that directly calls the method and extracts results.
"""

from focus_core import FocusAnalyzer

analyzer = FocusAnalyzer()

# Test with realistic EAR values
# Normal open eyes: 0.25-0.35
# Eyes gradually closing: 0.25 -> 0.12 -> 0.08 (closed) -> 0.12 -> 0.25 (opening)
ear_sequence = [
    0.30,  # Fully open
    0.25,  # Still open
    0.15,  # Starting to close (hysteresis)
    0.08,  # Closed
    0.06,  # Fully closed
    0.12,  # Starting to open
    0.20,  # Opening
    0.30,  # Fully open
    0.32,  # Remains open
]

# Set current time well after zone change to avoid debounce
analyzer._current_time = 1.0

print("Testing with more realistic EAR values (closed < 0.10, closed/open hysteresis 0.10-0.15):")
for i, ear_value in enumerate(ear_sequence):
    print(f"Frame {i}: EAR={ear_value:.2f}, Before state: {analyzer._ear_state}")
    blink = analyzer._detect_blink_motion(ear_value, "NORMAL")
    print(f"  After state: {analyzer._ear_state}, blink_detected={blink}, blink_in_progress={analyzer._blink_in_progress}")
