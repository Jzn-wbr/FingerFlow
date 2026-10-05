"""Hand landmark detection thread."""

from __future__ import annotations

import os
from pathlib import Path
import time
import logging
import sys
from queue import Empty
from typing import List, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision

from . import shared
from .shared import frame_queue, latest_lock, stop_event

logger = logging.getLogger(__name__)

Landmark = Tuple[float, float, float | None]


def _resolve_model_path() -> str:
    env_path = os.environ.get("FINGERFLOW_MODEL_PATH")
    if env_path:
        return env_path

    candidates = [
        getattr(shared, "MODEL_PATH_LITE", None),
        getattr(shared, "MODEL_PATH_FULL", None),
    ]
    base_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    for candidate in candidates:
        if not candidate:
            continue
        direct_path = Path(candidate)
        if direct_path.exists():
            return str(direct_path)
        bundled_path = base_root / candidate
        if bundled_path.exists():
            return str(bundled_path)
    return candidates[-1] or "model/hand_landmarker.task"


def _make_landmarker() -> vision.HandLandmarker:
    model_path = _resolve_model_path()
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info("Using model path: %s", model_path)
    base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        running_mode=vision.RunningMode.VIDEO,
    )
    return vision.HandLandmarker.create_from_options(options)


def detection_thread() -> None:
    logger.info("Detection thread starting")
    try:
        landmarker = _make_landmarker()
    except Exception:
        logger.exception("Failed to initialize hand landmarker")
        return
    last_fps_ts = time.time()
    last_log_ts = time.time()
    frames = 0
    hand_frames = 0
    last_timestamp_ms = None
    last_perf_ts = time.time()
    perf_counts = 0
    perf_wait = 0.0
    perf_cvt = 0.0
    perf_detect = 0.0
    perf_post = 0.0

    while not stop_event.is_set():
        wait_start = time.perf_counter()
        try:
            frame, timestamp = frame_queue.get(timeout=0.05)
        except Empty:
            continue
        wait_end = time.perf_counter()

        perf_wait += (wait_end - wait_start)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cvt_end = time.perf_counter()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Ensure monotonically increasing timestamps (ms) for VIDEO mode.
        ts_ms = int(timestamp)
        if last_timestamp_ms is not None and ts_ms <= last_timestamp_ms:
            ts_ms = last_timestamp_ms + 1
        last_timestamp_ms = ts_ms
        result = landmarker.detect_for_video(mp_image, ts_ms)
        detect_end = time.perf_counter()
        frames += 1
        now = time.time()
        if now - last_fps_ts >= 1.0:
            with latest_lock:
                shared.processing_fps = frames / (now - last_fps_ts)
                shared.hand_fps = hand_frames / (now - last_fps_ts)
            if now - last_log_ts >= 5.0:
                proc_fps = frames / (now - last_fps_ts)
                hand_fps = hand_frames / (now - last_fps_ts)
                logger.info("Processing fps %.1f, hand fps %.1f", proc_fps, hand_fps)
                last_log_ts = now
            last_fps_ts = now
            frames = 0
            hand_frames = 0
        if result.hand_landmarks:
            hand_frames += 1
            # collect all 21 landmarks (normalized) for the first detected hand
            lm_list: List[Landmark] = []
            for lm in result.hand_landmarks[0]:
                # lm has attributes x,y (normalized 0..1) and maybe z
                z_v = getattr(lm, "z", None)
                lm_list.append((lm.x, lm.y, z_v))

            with latest_lock:
                # store a dict so display can draw all landmarks and mouse can use the tip
                shared.latest_detection = {
                    "landmarks": lm_list,
                    "timestamp": time.time(),
                }
        else:
            # No hands detected in this frame: clear last detection so UI doesn't keep drawing old landmarks
            with latest_lock:
                shared.latest_detection = None

        post_end = time.perf_counter()
        perf_cvt += (cvt_end - wait_end)
        perf_detect += (detect_end - cvt_end)
        perf_post += (post_end - detect_end)
        perf_counts += 1
        if (now - last_perf_ts) >= 2.0 and perf_counts:
            avg_wait = (perf_wait / perf_counts) * 1000.0
            avg_cvt = (perf_cvt / perf_counts) * 1000.0
            avg_detect = (perf_detect / perf_counts) * 1000.0
            avg_post = (perf_post / perf_counts) * 1000.0
            with latest_lock:
                shared.perf_stats = {
                    "wait_ms": avg_wait,
                    "cvt_ms": avg_cvt,
                    "detect_ms": avg_detect,
                    "post_ms": avg_post,
                }
            last_perf_ts = now
            perf_counts = 0
            perf_wait = 0.0
            perf_cvt = 0.0
            perf_detect = 0.0
            perf_post = 0.0
