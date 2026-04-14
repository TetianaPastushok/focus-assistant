import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from focus_core import FocusAnalyzer
from config import FocusConfig


class TestFocusAnalyzer(unittest.TestCase):
    """Unit tests for FocusAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.cfg = FocusConfig()
        self.analyzer = FocusAnalyzer(cfg=self.cfg, enable_ai=False)  # Disable AI for testing

    def test_initialization(self):
        """Test that FocusAnalyzer initializes correctly."""
        self.assertIsInstance(self.analyzer, FocusAnalyzer)
        self.assertEqual(self.analyzer.mode, self.cfg.experiment_mode)
        self.assertFalse(self.analyzer.enable_ai)

    def test_set_enable_ai(self):
        """Test enabling/disabling AI."""
        self.analyzer.set_enable_ai(True)
        self.assertTrue(self.analyzer.enable_ai)
        self.analyzer.set_enable_ai(False)
        self.assertFalse(self.analyzer.enable_ai)

    def test_reset(self):
        """Test session reset."""
        start_time = 100.0
        self.analyzer.reset(start_time)
        self.assertEqual(self.analyzer.session_start_time, start_time)
        self.assertEqual(self.analyzer.blink_count, 0)
        self.assertEqual(self.analyzer.distraction_count, 0)

    def test_calculate_ear(self):
        """Test Eye Aspect Ratio calculation."""
        # Mock landmarks for left eye
        mock_landmarks = MagicMock()
        # Simulate eye points (simplified)
        mock_landmarks.landmark = [MagicMock() for _ in range(478)]
        for i, lm in enumerate(mock_landmarks.landmark):
            lm.x = 0.5
            lm.y = 0.5

        ear = self.analyzer.calculate_ear(mock_landmarks, [33, 160, 158, 133, 153, 144], 640, 480)
        self.assertIsInstance(ear, float)
        self.assertGreaterEqual(ear, 0.0)

    def test_build_intervention_static(self):
        """Test intervention building without AI."""
        metrics = {"focus_score": 0.8, "perclos": 15.0}
        result = self.analyzer._build_intervention("WARNING", "DISTRACTION", metrics)
        self.assertIn("intervention_level", result)
        self.assertIn("intervention_message", result)
        self.assertEqual(result["intervention_level"], "WARNING")

    def test_build_intervention_with_ai(self):
        """Test intervention building with AI (mocked)."""
        self.analyzer.enable_ai = True
        self.analyzer.gemini_client = MagicMock()
        self.analyzer.gemini_client.generate_advice.return_value = "Mock AI advice"

        metrics = {"focus_score": 0.8, "perclos": 15.0}
        result = self.analyzer._build_intervention("WARNING", "DISTRACTION", metrics)
        self.assertEqual(result["intervention_message"], "Mock AI advice")


if __name__ == '__main__':
    unittest.main()