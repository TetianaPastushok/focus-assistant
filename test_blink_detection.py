#!/usr/bin/env python3
"""
Test script to verify blink motion detection works correctly.
Simulates EAR values changing over time to mimic real blink motion.
"""

from focus_core import FocusAnalyzer
from config import FocusConfig
import time

def test_blink_detection():
    """Test that true blink motion (OPEN -> CLOSED -> OPEN) is detected."""
    analyzer = FocusAnalyzer()
    
    # Simulate 4 seconds of eye movements
    # Each test case: simulated EAR values as if eyes are opening/closing
    test_cases = [
        # Case 1: Normal blink (OPEN -> CLOSED -> OPEN)
        {
            "name": "Normal blink",
            "ear_sequence": [0.35, 0.35, 0.12, 0.12, 0.35, 0.35],  # Open -> Close -> Open
            "expected_blinks": 1
        },
        # Case 2: Eyes stay closed (no blink - just closed)
        {
            "name": "Eyes stay closed (looking down)",
            "ear_sequence": [0.10, 0.10, 0.10, 0.10, 0.10],
            "expected_blinks": 0
        },
        # Case 3: Two blinks
        {
            "name": "Two blinks",
            "ear_sequence": [0.35, 0.12, 0.35, 0.35, 0.12, 0.35],
            "expected_blinks": 2
        },
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"{'='*60}")
        
        analyzer.reset(0.0)
        # Set current time well after zone change to avoid debounce
        analyzer._current_time = 1.0
        blink_count_before = analyzer.blink_count
        
        # We'll test _detect_blink_motion directly without needing real landmarks
        print(f"EAR sequence: {test['ear_sequence']}")
        
        blinks_detected = 0
        for i, ear_value in enumerate(test['ear_sequence']):
            # Call blink detection directly
            prev_state = analyzer._ear_state
            prev_blink_in_progress = analyzer._blink_in_progress
            blink = analyzer._detect_blink_motion(ear_value, "NORMAL")
            new_state = analyzer._ear_state
            if blink:
                blinks_detected += 1
                print(f"  Frame {i}: EAR={ear_value:.2f} ({prev_state}->{new_state}) -> BLINK DETECTED ✓")
            else:
                print(f"  Frame {i}: EAR={ear_value:.2f} ({prev_state}->{new_state}), blink_in_progress={analyzer._blink_in_progress}")
        
        print(f"\nResult: Detected {blinks_detected} blink(s), expected {test['expected_blinks']}")
        
        if blinks_detected == test['expected_blinks']:
            print(f"✓ PASS")
        else:
            print(f"✗ FAIL - Expected {test['expected_blinks']}, got {blinks_detected}")

if __name__ == "__main__":
    test_blink_detection()
    print("\n" + "="*60)
    print("Blink detection tests complete!")
    print("="*60)
