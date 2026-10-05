"""Unit tests for FingerFlow hand gesture recognition and control."""

import unittest
import math
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock Windows-specific modules before importing mouse_control
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['keyboard'] = MagicMock()

# Now we can safely import
from fingerflow.mouse_control import (
    _landmark_distance,
    _is_fist,
    _palm_center,
    _map_to_screen,
    _ema_filter,
    _update_click_state,
)


class TestLandmarkDistance(unittest.TestCase):
    """Test landmark distance calculation."""

    def test_distance_between_two_points(self):
        """Test Euclidean distance between two landmarks."""
        landmarks = [
            (0.0, 0.0, None),  # Point A at origin
            (3.0, 4.0, None),  # Point B at (3, 4) - should be distance 5
        ]
        distance = _landmark_distance(landmarks, 0, 1)
        self.assertAlmostEqual(distance, 5.0, places=5)

    def test_distance_same_point(self):
        """Test distance when both points are identical."""
        landmarks = [(1.5, 2.5, None), (1.5, 2.5, None)]
        distance = _landmark_distance(landmarks, 0, 1)
        self.assertAlmostEqual(distance, 0.0, places=5)

    def test_distance_with_negative_coords(self):
        """Test distance with negative coordinates."""
        landmarks = [(-1.0, -1.0, None), (2.0, 3.0, None)]
        distance = _landmark_distance(landmarks, 0, 1)
        expected = math.sqrt((2.0 - (-1.0)) ** 2 + (3.0 - (-1.0)) ** 2)
        self.assertAlmostEqual(distance, expected, places=5)

    def test_distance_invalid_indices(self):
        """Test that invalid indices return None."""
        landmarks = [(0.0, 0.0, None)]
        distance = _landmark_distance(landmarks, 0, 10)
        self.assertIsNone(distance)

    def test_distance_negative_index(self):
        """Test that negative indices are handled (Python allows negative indexing)."""
        landmarks = [(0.0, 0.0, None), (1.0, 1.0, None)]
        distance = _landmark_distance(landmarks, 0, -1)
        self.assertAlmostEqual(distance, math.sqrt(2), places=5)


class TestIsFist(unittest.TestCase):
    """Test hand closed detection (fist detection)."""

    def test_open_hand_not_fist(self):
        """Test that open hand is not detected as fist."""
        # Simulating open hand with fingers far from palm
        landmarks = [
            (0.5, 0.5, None),    # Wrist (0)
            (0.5, 0.4, None),    # Thumb base (5)
            (0.6, 0.3, None),    # Thumb tip (4) - far from base
            (0.5, 0.2, None),    # Index base (9)
            (0.5, 0.0, None),    # Index tip (8) - far from base
            (0.5, 0.2, None),    # Middle base (13)
            (0.5, -0.1, None),   # Middle tip (12)
            (0.5, 0.2, None),    # Ring base (17)
            (0.5, -0.1, None),   # Ring tip (16)
            (0.5, 0.2, None),    # Pinky base (21 - padding)
            (0.5, -0.1, None),   # Pinky tip (20)
        ]
        # Pad with extra landmarks
        landmarks.extend([(0.5, 0.5, None)] * 11)
        
        is_fist = _is_fist(landmarks, threshold=0.08)
        self.assertFalse(is_fist)

    def test_closed_hand_is_fist(self):
        """Test that closed hand is detected as fist."""
        # Simulating closed hand with fingers close to palm
        palm_x, palm_y = 0.5, 0.5
        base_dist = 0.02
        
        landmarks = [
            (palm_x, palm_y, None),              # Wrist (0)
        ]
        # Add 20 landmarks with fingers close to palm
        for i in range(20):
            landmarks.append((palm_x + base_dist, palm_y + base_dist, None))
        
        is_fist = _is_fist(landmarks, threshold=0.08)
        self.assertTrue(is_fist)

    def test_fist_threshold_boundary(self):
        """Test fist detection at threshold boundary."""
        landmarks = [(0.5, 0.5, None)] * 21
        landmarks[8] = (0.5055, 0.5055, None)    # Index tip at distance ~0.0078
        landmarks[12] = (0.5055, 0.5055, None)   # Middle tip
        landmarks[16] = (0.5055, 0.5055, None)   # Ring tip
        landmarks[20] = (0.5055, 0.5055, None)   # Pinky tip
        
        is_fist_high = _is_fist(landmarks, threshold=0.02)
        self.assertTrue(is_fist_high)


class TestPalmCenter(unittest.TestCase):
    """Test palm center calculation."""

    def test_palm_center_simple(self):
        """Test palm center with simple symmetric hand."""
        landmarks = [
            (0.5, 0.5, None),   # Wrist (0)
            (0.5, 0.48, None),  # Thumb base (1)
            (0.49, 0.5, None),  # Index base (5)
            (0.49, 0.52, None), # Middle base (9)
            (0.51, 0.52, None), # Ring base (13)
            (0.51, 0.5, None),  # Pinky base (17)
        ]
        # Pad to 21 landmarks
        landmarks.extend([(0.5, 0.5, None)] * 15)
        
        palm = _palm_center(landmarks)
        self.assertIsNotNone(palm)
        # Palm center should be flipped horizontally
        x, y = palm
        self.assertAlmostEqual(x, 0.5, places=2)  # Horizontally centered
        self.assertAlmostEqual(y, 0.5, places=2)  # Vertically centered

    def test_palm_center_empty(self):
        """Test palm center with empty landmarks."""
        landmarks = []
        palm = _palm_center(landmarks)
        self.assertIsNone(palm)

    def test_palm_center_horizontal_flip(self):
        """Test that palm center is horizontally flipped."""
        landmarks = [(0.25, 0.5, None)] * 21
        
        palm = _palm_center(landmarks)
        x, y = palm
        # Should be flipped: 1.0 - 0.25 = 0.75
        self.assertAlmostEqual(x, 0.75, places=1)


class TestMapToScreen(unittest.TestCase):
    """Test normalized coordinate to screen pixel mapping."""

    def test_center_mapping(self):
        """Test that center normalized coords map to center of screen."""
        x_screen, y_screen = _map_to_screen(0.5, 0.5, scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)
        # Should map to center
        self.assertGreater(x_screen, 0)
        self.assertGreater(y_screen, 0)

    def test_zero_coords_mapping(self):
        """Test that (0, 0) normalized maps to top-left."""
        x_screen, y_screen = _map_to_screen(0.0, 0.0, scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)
        self.assertEqual(x_screen, 0)
        self.assertEqual(y_screen, 0)

    def test_one_coords_mapping(self):
        """Test that (1, 1) normalized maps correctly."""
        x_screen, y_screen = _map_to_screen(1.0, 1.0, scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)
        # Should be clamped or at screen size
        self.assertGreaterEqual(x_screen, 0)
        self.assertGreaterEqual(y_screen, 0)

    def test_scale_amplifies_movement(self):
        """Test that scale factors amplify movement."""
        x1, y1 = _map_to_screen(0.6, 0.6, scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)
        x2, y2 = _map_to_screen(0.6, 0.6, scale_x=2.0, scale_y=2.0, offset_x=0.0, offset_y=0.0)
        # Higher scale should result in larger screen displacement
        self.assertGreater(abs(x2 - x1), 0)
        self.assertGreater(abs(y2 - y1), 0)

    def test_offset_shifts_position(self):
        """Test that offsets shift the mapped position."""
        x1, y1 = _map_to_screen(0.5, 0.5, scale_x=1.0, scale_y=1.0, offset_x=0.0, offset_y=0.0)
        x2, y2 = _map_to_screen(0.5, 0.5, scale_x=1.0, scale_y=1.0, offset_x=0.1, offset_y=0.1)
        # With positive offset, position should shift right/down
        self.assertGreater(x2, x1)
        self.assertGreater(y2, y1)


class TestEmaFilter(unittest.TestCase):
    """Test exponential moving average smoothing filter."""

    def test_first_call_no_filter(self):
        """Test that first call returns target (no previous value)."""
        target = (100, 200)
        result = _ema_filter(target, last_filtered=None, alpha=0.25)
        self.assertEqual(result, (100.0, 200.0))

    def test_filter_smooths_jump(self):
        """Test that filter smooths abrupt changes."""
        target1 = (100, 100)
        result1 = _ema_filter(target1, last_filtered=None, alpha=0.25)
        
        target2 = (200, 200)  # Big jump
        result2 = _ema_filter(target2, last_filtered=result1, alpha=0.25)
        
        # Result should be between last and target
        self.assertGreater(result2[0], result1[0])
        self.assertLess(result2[0], target2[0])

    def test_high_alpha_follows_target(self):
        """Test that high alpha (closer to 1) follows target more closely."""
        last = (100, 100)
        target = (200, 200)
        
        result_low = _ema_filter(target, last_filtered=last, alpha=0.1)
        result_high = _ema_filter(target, last_filtered=last, alpha=0.9)
        
        # High alpha should be closer to target
        self.assertGreater(result_high[0], result_low[0])

    def test_alpha_zero_no_change(self):
        """Test that alpha=0 doesn't change position."""
        last = (100, 100)
        target = (200, 200)
        result = _ema_filter(target, last_filtered=last, alpha=0.0)
        self.assertEqual(result, last)


class TestUpdateClickState(unittest.TestCase):
    """Test click state hysteresis logic."""

    def test_press_on_short_distance(self):
        """Test that click activates when distance goes below threshold."""
        press_called = False
        release_called = False
        
        def press_fn():
            nonlocal press_called
            press_called = True
        
        def release_fn():
            nonlocal release_called
            release_called = True
        
        # Initial state: not pressed, distance below threshold
        result = _update_click_state(0.04, pressed=False, press_fn=press_fn, release_fn=release_fn)
        
        self.assertTrue(result)  # Should now be pressed
        self.assertTrue(press_called)
        self.assertFalse(release_called)

    def test_release_on_large_distance(self):
        """Test that click releases when distance exceeds threshold."""
        press_called = False
        release_called = False
        
        def press_fn():
            nonlocal press_called
            press_called = True
        
        def release_fn():
            nonlocal release_called
            release_called = True
        
        # State: pressed, distance above release threshold
        result = _update_click_state(0.07, pressed=True, press_fn=press_fn, release_fn=release_fn)
        
        self.assertFalse(result)  # Should now be released
        self.assertFalse(press_called)
        self.assertTrue(release_called)

    def test_hysteresis_prevents_jitter(self):
        """Test that hysteresis prevents rapid toggling."""
        # Start pressed at touch threshold
        result = _update_click_state(0.055, pressed=True, press_fn=lambda: None, release_fn=lambda: None)
        self.assertTrue(result)  # Should remain pressed
        
        # Slightly above touch but below release threshold
        result = _update_click_state(0.060, pressed=True, press_fn=lambda: None, release_fn=lambda: None)
        self.assertTrue(result)  # Should remain pressed due to hysteresis

    def test_none_distance_releases(self):
        """Test that None distance (no hand) releases click."""
        release_called = False
        
        def release_fn():
            nonlocal release_called
            release_called = True
        
        result = _update_click_state(None, pressed=True, press_fn=lambda: None, release_fn=release_fn)
        
        self.assertFalse(result)  # Should be released
        self.assertTrue(release_called)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple functions."""

    def test_full_gesture_pipeline(self):
        """Test a complete hand tracking gesture pipeline."""
        # Simulated 21-point hand landmark
        landmarks = [
            (0.5, 0.5, 0.1),    # Wrist
            (0.48, 0.48, 0.1),  # Thumb CMC
            (0.47, 0.46, 0.1),  # Thumb MCP
            (0.46, 0.44, 0.1),  # Thumb IP
            (0.45, 0.42, 0.1),  # Thumb tip
            (0.48, 0.40, 0.1),  # Index MCP
            (0.47, 0.35, 0.1),  # Index PIP
            (0.46, 0.30, 0.1),  # Index DIP
            (0.45, 0.25, 0.1),  # Index tip
            (0.50, 0.38, 0.1),  # Middle MCP
            (0.50, 0.30, 0.1),  # Middle PIP
            (0.50, 0.22, 0.1),  # Middle DIP
            (0.50, 0.14, 0.1),  # Middle tip
            (0.52, 0.38, 0.1),  # Ring MCP
            (0.53, 0.30, 0.1),  # Ring PIP
            (0.54, 0.22, 0.1),  # Ring DIP
            (0.55, 0.14, 0.1),  # Ring tip
            (0.54, 0.40, 0.1),  # Pinky MCP
            (0.56, 0.32, 0.1),  # Pinky PIP
            (0.58, 0.24, 0.1),  # Pinky DIP
            (0.60, 0.16, 0.1),  # Pinky tip
        ]

        # Test palm center calculation
        palm = _palm_center(landmarks)
        self.assertIsNotNone(palm)
        px, py = palm
        self.assertGreaterEqual(px, 0.0)
        self.assertLessEqual(px, 1.0)

        # Test screen mapping
        x_screen, y_screen = _map_to_screen(px, py, 1.25, 1.25, -0.03, -0.1)
        self.assertGreaterEqual(x_screen, 0)
        self.assertGreaterEqual(y_screen, 0)

        # Test not a fist
        is_fist = _is_fist(landmarks, threshold=0.08)
        self.assertFalse(is_fist)

        # Test left click distance (thumb-index)
        click_dist = _landmark_distance(landmarks, 4, 8)
        self.assertIsNotNone(click_dist)
        self.assertGreater(click_dist, 0)


if __name__ == "__main__":
    unittest.main()
