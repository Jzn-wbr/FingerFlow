# main.py
import warnings
import os
import sys
import ctypes
import threading
import time
import logging

# Allow running as a script (PyInstaller entrypoint) or as a package.
if __package__ in (None, ""):
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    __package__ = "fingerflow"

from .shared import stop_event

# Suppress a known third-party deprecation warning coming from protobuf's
# SymbolDatabase.GetPrototype() usage in some installed packages.
# This warning is harmless for runtime but noisy; to avoid changing
# installed packages we silence that specific message here.
warnings.filterwarnings(
    "ignore",
    message=r"SymbolDatabase.GetPrototype\(\) is deprecated.*",
    category=UserWarning,
)

from .capture import capture_thread
from .detection import detection_thread
from .mouse_control import mouse_thread
from .display_qml import display_loop

def _setup_logging() -> str:
    log_root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    log_dir = os.path.join(log_root, "FingerFlow", "logs")
    os.makedirs(log_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(log_dir, f"fingerflow-{stamp}.log")
    handlers = [logging.FileHandler(log_path, encoding="utf-8")]
    if os.environ.get("FINGERFLOW_CONSOLE_LOG", "0") == "1":
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("mediapipe").setLevel(logging.WARNING)
    logging.info("Log file: %s", log_path)
    logging.info("Executable: %s", sys.executable)
    logging.info("Frozen: %s", getattr(sys, "frozen", False))
    logging.info("MEIPASS: %s", getattr(sys, "_MEIPASS", ""))
    return log_path


def main() -> None:
    _setup_logging()
    if sys.platform.startswith("win"):
        try:
            HIGH_PRIORITY_CLASS = 0x00000080
            ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(),
                HIGH_PRIORITY_CLASS,
            )
        except Exception:
            pass

    if os.environ.get("FINGERFLOW_KEEPALIVE", "0") == "1":
        def _keepalive_loop() -> None:
            burn_ms = float(os.environ.get("FINGERFLOW_KEEPALIVE_BURN_MS", "5"))
            period_ms = float(os.environ.get("FINGERFLOW_KEEPALIVE_PERIOD_MS", "50"))
            while not stop_event.is_set():
                start = time.perf_counter()
                target = burn_ms / 1000.0
                while (time.perf_counter() - start) < target:
                    pass
                sleep_for = max(0.0, (period_ms - burn_ms) / 1000.0)
                time.sleep(sleep_for)

        threading.Thread(target=_keepalive_loop, daemon=True).start()

    t1 = threading.Thread(target=capture_thread, daemon=True)
    t2 = threading.Thread(target=detection_thread, daemon=True)
    t3 = threading.Thread(target=mouse_thread, daemon=True)

    t1.start()
    t2.start()
    t3.start()
    print("\n\n\nRunning. Close the window or press CTRL+C to stop.")
    try:
        # QML must run on the main thread for best performance.
        display_loop()
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopping...")
    # main will exit when stop_event is set (either by Ctrl+C or by the
    # display close-button). Threads are daemonized, so the process will
    # terminate once this main thread finishes.


if __name__ == "__main__":
    main()
