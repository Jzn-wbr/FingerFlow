# shared.py
import threading
import queue

FRAME_QUEUE_MAX = 2

frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAX)
latest_detection = None
latest_lock = threading.Lock()
stop_event = threading.Event()

# Updated by detection thread once per second.
processing_fps = 0.0
hand_fps = 0.0
capture_fps = 0.0
drop_fps = 0.0

# Rolling performance stats (ms). Updated by detection thread.
perf_stats = {
    "wait_ms": 0.0,
    "cvt_ms": 0.0,
    "detect_ms": 0.0,
    "post_ms": 0.0,
}

# latest_frame holds the most recent camera BGR frame (or None).
# Protected by `latest_lock` when written/read.
latest_frame = None
current_mode = "normal"
selected_mode = "normal"
topmost_enabled = True
ui_visible = True

MODEL_PATH_FULL = "model/hand_landmarker.task"
MODEL_PATH_LITE = "model/hand_landmarker_lite.task"

# Target capture FPS (best-effort, driver may ignore).
TARGET_FPS = 30

# Camera exposure controls (best-effort, may be ignored by driver).
# Set AUTO_EXPOSURE to False to force manual exposure.
AUTO_EXPOSURE = True
# Typical manual exposure values are driver-specific; start with -6..-4.
MANUAL_EXPOSURE = 0

# Preferred capture resolution to keep consistent aspect ratio
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Simple screen mapping coefficients.
# Increase SCALE_* to amplify movement from camera to screen (gives margin).
SCREEN_SCALE_X = 1.35
SCREEN_SCALE_Y = 1.8
# Optional offsets after scaling (positive Y moves cursor down).
SCREEN_OFFSET_X = -0.03
SCREEN_OFFSET_Y = -0.1

# Mode switching (only when hand is closed)
MODE_KEY_NORMAL = "N"
MODE_KEY_DRAW = "D"
MODE_KEY_ZOOM = "Z"
MODE_KEY_SCROLL = "S"
MODE_KEY_PAUSE = "P"
MODE_KEY_TOP = "T"

# Draw app executable (opened when entering draw mode)
DRAW_APP = "mspaint.exe"

# Hand-closed detection sensitivity (normalized)
FIST_THRESHOLD = 0.08

# Mouse smoothing tweaks
MOUSE_SMOOTH_ALPHA = 0.25
MOUSE_STEP_PX = 6

# Click stabilization to avoid tiny drags on press.
CLICK_FREEZE_MS = 240
