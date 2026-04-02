#!/usr/bin/env python3
"""
Debug test to trace blink detection logic.
"""

from focus_core import FocusAnalyzer

analyzer = FocusAnalyzer()

# Test one normal blink
print("Testing blink motion detection logic:")
print("="*60)

ear_sequence = [0.35, 0.35, 0.12, 0.12, 0.35, 0.35]

for i, ear_value in enumerate(ear_sequence):
    print(f"\nFrame {i}: EAR={ear_value:.2f}")
    print(f"  Before: _ear_state={analyzer._ear_state}, _blink_in_progress={analyzer._blink_in_progress}")
    
    # Manual logic to debug
    open_threshold = 0.22
    close_threshold = 0.16
    
    if ear_value < close_threshold:
        new_ear_state = "CLOSED"
        print(f"  EAR < {close_threshold} -> new_ear_state = CLOSED")
    elif ear_value > open_threshold:
        new_ear_state = "OPEN"
        print(f"  EAR > {open_threshold} ->new_ear_state = OPEN")
    else:
        new_ear_state = analyzer._ear_state
        print(f"  {close_threshold} <= EAR <= {open_threshold} -> new_ear_state (unchanged) = {new_ear_state}")
    
    # Check transition
    blink_detected = False
    if analyzer._ear_state == "OPEN" and new_ear_state == "CLOSED":
        print(f"  TRANSITION: OPEN -> CLOSED -> set _blink_in_progress=True")
        analyzer._blink_in_progress = True
    elif analyzer._ear_state == "CLOSED" and new_ear_state == "OPEN" and analyzer._blink_in_progress:
        print(f"  TRANSITION: CLOSED -> OPEN with blink_in_progress=True -> BLINK DETECTED!")
        blink_detected = True
        analyzer._blink_in_progress = False
    elif analyzer._ear_state == "CLOSED" and new_ear_state == "CLOSED":
        print(f"  STATE: CLOSED -> CLOSED -> stay closed (not a blink)")
        analyzer._blink_in_progress = False
    else:
        print(f"  STATE: {analyzer._ear_state} -> {new_ear_state} (no blink)")
    
    analyzer._ear_state = new_ear_state
    print(f"  After: _ear_state={analyzer._ear_state}, _blink_in_progress={analyzer._blink_in_progress}, blink_detected={blink_detected}")
