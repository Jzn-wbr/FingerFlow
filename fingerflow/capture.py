"""Camera capture thread."""

from __future__ import annotations

from queue import Full
import time
import logging

import cv2

from . import shared
from .shared import frame_queue, stop_event

logger = logging.getLogger(__name__)


def _apply_preferred_resolution(cap: cv2.VideoCapture) -> None:
    """Best-effort camera sizing to keep downstream aspect ratio stable."""
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, shared.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, shared.FRAME_HEIGHT)
        target_fps = getattr(shared, "TARGET_FPS", 30)
        if target_fps:
            cap.set(cv2.CAP_PROP_FPS, float(target_fps))
        auto_exposure = getattr(shared, "AUTO_EXPOSURE", True)
        # For DSHOW, 0.75 = auto, 0.25 = manual (driver-dependent).
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75 if auto_exposure else 0.25)
        if not auto_exposure:
            manual_exposure = getattr(shared, "MANUAL_EXPOSURE", None)
            if manual_exposure is not None:
                cap.set(cv2.CAP_PROP_EXPOSURE, float(manual_exposure))
    except Exception:
        # Ignore failures if backend does not support setting size.
        pass


def capture_thread() -> None:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    _apply_preferred_resolution(cap)
    logger.info("Camera opened: %s", cap.isOpened())
    try:
        backend = cap.getBackendName()
    except Exception:
        backend = "unknown"
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info("Camera backend: %s, width: %.0f, height: %.0f, fps: %.1f", backend, width, height, fps)
    last_fps_ts = time.time()
    last_log_ts = time.time()
    frames = 0
    drops = 0
    fail_count = 0
    last_open_ts = time.time()

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            fail_count += 1
            # Backoff to avoid busy looping if the camera is unavailable.
            time.sleep(min(0.5, 0.05 * fail_count))
            # Periodically reopen the camera to recover from disconnects.
            if fail_count >= 20 or (time.time() - last_open_ts) > 5.0:
                logger.warning("Camera read failed %s times, reopening.", fail_count)
                try:
                    cap.release()
                except Exception:
                    pass
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                _apply_preferred_resolution(cap)
                last_open_ts = time.time()
                fail_count = 0
            continue

        fail_count = 0
        timestamp = int(time.monotonic() * 1000)
        # Keep a recent frame available for display (copy to avoid races)
        with shared.latest_lock:
            if getattr(shared, "ui_visible", True):
                try:
                    shared.latest_frame = frame.copy()
                except Exception:
                    shared.latest_frame = None
            else:
                shared.latest_frame = None

        try:
            frame_queue.put((frame, timestamp), timeout=0.01)
        except Full:
            # queue pleine = on skip
            drops += 1

        frames += 1
        now = time.time()
        if now - last_fps_ts >= 1.0:
            with shared.latest_lock:
                shared.capture_fps = frames / (now - last_fps_ts)
                shared.drop_fps = drops / (now - last_fps_ts)
            if now - last_log_ts >= 5.0:
                drop_fps = drops / (now - last_fps_ts)
                capture_fps = frames / (now - last_fps_ts)
                if drop_fps > 2.0 or capture_fps < 10.0:
                    logger.warning(
                        "Capture fps %.1f, drop fps %.1f", capture_fps, drop_fps
                    )
                last_log_ts = now
            last_fps_ts = now
            frames = 0
            drops = 0

    cap.release()
