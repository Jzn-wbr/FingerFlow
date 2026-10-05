"""Display thread: shows camera with hand landmarks and skeleton overlay."""

from __future__ import annotations

import ctypes
import sys
import time
from typing import Iterable, Sequence, Tuple

import cv2
import numpy as np
import tkinter as tk

from . import shared
# Define hand connections (MediaPipe hand connections)
HAND_CONNECTIONS: Tuple[Tuple[int, int], ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


def draw_landmarks(frame, lm_list: Sequence[Tuple[float, float, float | None]]) -> None:
    h, w = frame.shape[:2]
    # draw connections
    for a, b in HAND_CONNECTIONS:
        if a < len(lm_list) and b < len(lm_list):
            ax, ay, _ = lm_list[a]
            bx, by, _ = lm_list[b]
            pt_a = (int(ax * w), int(ay * h))
            pt_b = (int(bx * w), int(by * h))
            cv2.line(frame, pt_a, pt_b, (0, 255, 0), 2)

    # draw landmarks
    for x, y, z in lm_list:
        pt = (int(x * w), int(y * h))
        cv2.circle(frame, pt, 4, (0, 0, 255), -1)


def _get_screen_size() -> Tuple[int | None, int | None]:
    """Try to read screen size via Tkinter without creating a window."""
    try:
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except Exception:
        return None, None


def _set_topmost(window_name: str, enabled: bool) -> None:
    """Toggle always-on-top for the OpenCV window."""
    try:
        cv2.setWindowProperty(
            window_name, cv2.WND_PROP_TOPMOST, 1 if enabled else 0
        )
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
            if hwnd:
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_SHOWWINDOW = 0x0040
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST if enabled else HWND_NOTOPMOST,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
                )
        except Exception:
            pass


def _maybe_center_window(
    window_name: str, frame_shape: Iterable[int], screen_size: Tuple[int | None, int | None]
) -> bool:
    """Center the window once; return True if moved."""
    screen_w, screen_h = screen_size
    if screen_w is None or screen_h is None:
        return False

    h, w = frame_shape
    x = max(0, (screen_w - w) // 2)
    y = max(0, (screen_h - h) // 2)
    try:
        cv2.moveWindow(window_name, x, y)
    except Exception:
        return False
    return True


def display_thread(window_name: str = "FingerFlow") -> None:
    last_fps_ts = time.time()
    frames = 0
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    screen_size = _get_screen_size()

    _moved = False
    topmost_enabled = True
    last_topmost = topmost_enabled
    _set_topmost(window_name, topmost_enabled)
    with shared.latest_lock:
        shared.topmost_enabled = topmost_enabled

    panel_w = 280
    panel_padding = 18
    panel_gap = 14
    panel_font = cv2.FONT_HERSHEY_SIMPLEX
    panel_bg_top = np.array([36, 38, 48], dtype=np.float32)
    panel_bg_bottom = np.array([18, 20, 28], dtype=np.float32)
    panel_accent = (55, 140, 255)
    panel_text = (230, 230, 240)
    panel_muted = (150, 155, 170)
    panel_active = (80, 220, 140)
    panel_inactive = (70, 75, 90)
    panel_warn = (0, 200, 255)
    frame_w = getattr(shared, "FRAME_WIDTH", 640)
    frame_h = getattr(shared, "FRAME_HEIGHT", 480)
    blank_frame = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)

    def _draw_panel(
        panel,
        current_mode: str,
        selected_mode: str,
        is_topmost: bool,
    ) -> None:
        h, w = panel.shape[:2]
        grad = np.linspace(0.0, 1.0, h, dtype=np.float32).reshape(h, 1, 1)
        panel[:] = (panel_bg_top + (panel_bg_bottom - panel_bg_top) * grad).astype(
            np.uint8
        )

        cv2.rectangle(panel, (0, 0), (w - 1, h - 1), (45, 50, 65), 2)
        cv2.line(panel, (0, 72), (w, 72), (45, 50, 65), 1)

        cv2.putText(
            panel,
            "FINGERFLOW",
            (panel_padding, 30),
            panel_font,
            0.8,
            panel_text,
            2,
        )
        cv2.putText(
            panel,
            "MODE PANEL",
            (panel_padding, 55),
            panel_font,
            0.5,
            panel_muted,
            1,
        )

        status = current_mode.upper()
        status_color = panel_warn if current_mode == "mode select" else panel_active
        cv2.circle(panel, (panel_padding + 8, 98), 7, status_color, -1)
        cv2.putText(
            panel,
            f"STATUS: {status}",
            (panel_padding + 24, 104),
            panel_font,
            0.55,
            panel_text,
            1,
        )

        top_status = "ON" if is_topmost else "OFF"
        top_color = panel_active if is_topmost else panel_inactive
        cv2.circle(panel, (panel_padding + 8, 126), 6, top_color, -1)
        cv2.putText(
            panel,
            f"TOP: {top_status}",
            (panel_padding + 24, 132),
            panel_font,
            0.5,
            panel_text,
            1,
        )
        top_key = getattr(shared, "MODE_KEY_TOP", "F").upper()
        cv2.putText(
            panel,
            f"TOP toggle key: {top_key}",
            (panel_padding, 152),
            panel_font,
            0.45,
            panel_muted,
            1,
        )

        modes = [
            ("normal", getattr(shared, "MODE_KEY_NORMAL", "S")),
            ("draw", getattr(shared, "MODE_KEY_DRAW", "D")),
            ("zoom", getattr(shared, "MODE_KEY_ZOOM", "Z")),
            ("scroll", getattr(shared, "MODE_KEY_SCROLL", "S")),
            ("pause", getattr(shared, "MODE_KEY_PAUSE", "P")),
        ]
        y = 186
        for name, key in modes:
            active = selected_mode == name
            indicator_color = panel_active if active else panel_inactive
            text_color = panel_text if active else panel_muted

            cv2.circle(panel, (panel_padding + 8, y + 8), 6, indicator_color, -1)
            cv2.putText(
                panel,
                name.upper(),
                (panel_padding + 24, y + 14),
                panel_font,
                0.6,
                text_color,
                2 if active else 1,
            )

            key_box_w = 42
            key_box_h = 26
            key_x2 = w - panel_padding
            key_x1 = key_x2 - key_box_w
            key_y1 = y - 2
            key_y2 = key_y1 + key_box_h
            cv2.rectangle(
                panel, (key_x1, key_y1), (key_x2, key_y2), panel_accent, 2
            )
            cv2.putText(
                panel,
                key.upper(),
                (key_x1 + 12, key_y2 - 8),
                panel_font,
                0.6,
                panel_text,
                1,
            )

            y += 48

    while not shared.stop_event.is_set():
        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                shared.stop_event.set()
                break
        except Exception:
            pass

        with shared.latest_lock:
            current_mode = getattr(shared, "current_mode", "normal")
            selected_mode = getattr(shared, "selected_mode", current_mode)
            topmost_enabled = getattr(shared, "topmost_enabled", True)
            if not topmost_enabled:
                frame = blank_frame.copy()
                detection = None
            else:
                frame = (
                    None
                    if shared.latest_frame is None
                    else shared.latest_frame.copy()
                )
                detection = shared.latest_detection

        if topmost_enabled != last_topmost:
            _set_topmost(window_name, topmost_enabled)
            last_topmost = topmost_enabled

        if frame is None:
            time.sleep(0.01)
            continue

        if topmost_enabled:
            try:
                frame = cv2.flip(frame, 1)
            except Exception:
                pass

            # overlay landmarks if available. Since the frame is mirrored,
            # mirror the landmark X coordinates so overlay matches the image.
            if isinstance(detection, dict) and "landmarks" in detection:
                try:
                    lm = detection["landmarks"]
                    mirrored = [(1.0 - x, y, z) for (x, y, z) in lm]
                    draw_landmarks(frame, mirrored)
                except Exception:
                    pass

        frames += 1
        now = time.time()
        if now - last_fps_ts >= 1.0:
            fps = frames / (now - last_fps_ts)
            last_fps_ts = now
            frames = 0
        else:
            fps = None

        if fps is not None:
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

        # Build the composed layout (camera left, panel right).
        h, w = frame.shape[:2]
        panel = np.zeros((h, panel_w, 3), dtype=frame.dtype)
        _draw_panel(panel, current_mode, selected_mode, topmost_enabled)
        display_frame = np.zeros((h, w + panel_w, 3), dtype=frame.dtype)
        display_frame[:, :w] = frame
        display_frame[:, w:] = panel

        if not _moved:
            _moved = _maybe_center_window(
                window_name, display_frame.shape[:2], screen_size
            )

        cv2.imshow(window_name, display_frame)
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            shared.stop_event.set()
            break
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            shared.stop_event.set()
            break

    cv2.destroyAllWindows()
