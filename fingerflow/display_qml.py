"""Modern QML UI for high-performance display."""

from __future__ import annotations

import time
from pathlib import Path
import os
import sys
import ctypes
import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtQml, QtQuick

from . import shared

# MediaPipe hand connections (same as OpenCV display).
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
    for a, b in HAND_CONNECTIONS:
        if a < len(lm_list) and b < len(lm_list):
            ax, ay, _ = lm_list[a]
            bx, by, _ = lm_list[b]
            pt_a = (int(ax * w), int(ay * h))
            pt_b = (int(bx * w), int(by * h))
            cv2.line(frame, pt_a, pt_b, (64, 220, 140), 2)

    for i, (x, y, _) in enumerate(lm_list):
        pt = (int(x * w), int(y * h))
        cv2.circle(frame, pt, 4, (40, 140, 255), -1)


def _to_qimage(frame_bgr: np.ndarray) -> QtGui.QImage:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    bytes_per_line = rgb.strides[0]
    qimg = QtGui.QImage(
        rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888
    )
    return qimg.copy()


class CameraProvider(QtQuick.QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QtQuick.QQuickImageProvider.ImageType.Pixmap)
        self._pixmap = QtGui.QPixmap(2, 2)
        self._pixmap.fill(QtGui.QColor(15, 18, 26))

    def set_image(self, image: QtGui.QImage) -> None:
        self._pixmap = QtGui.QPixmap.fromImage(image)

    def requestPixmap(self, _id, size, requested_size):
        pm = self._pixmap
        if size is not None:
            size.setWidth(pm.width())
            size.setHeight(pm.height())
        return pm


class UiState(QtCore.QObject):
    imageCounterChanged = QtCore.Signal()
    modeChanged = QtCore.Signal()
    selectedModeChanged = QtCore.Signal()
    topmostChanged = QtCore.Signal()
    displayFpsChanged = QtCore.Signal()
    processingFpsChanged = QtCore.Signal()
    handFpsChanged = QtCore.Signal()
    captureFpsChanged = QtCore.Signal()
    dropFpsChanged = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self._image_counter = 0
        self._mode = "normal"
        self._selected_mode = "normal"
        self._topmost = True
        self._display_fps = 0.0
        self._processing_fps = 0.0
        self._hand_fps = 0.0
        self._capture_fps = 0.0
        self._drop_fps = 0.0

    @QtCore.Property(int, notify=imageCounterChanged)
    def imageCounter(self) -> int:
        return self._image_counter

    def bump_image(self) -> None:
        self._image_counter += 1
        self.imageCounterChanged.emit()

    @QtCore.Property(str, notify=modeChanged)
    def mode(self) -> str:
        return self._mode

    def set_mode(self, value: str) -> None:
        if value != self._mode:
            self._mode = value
            self.modeChanged.emit()

    @QtCore.Property(str, notify=selectedModeChanged)
    def selectedMode(self) -> str:
        return self._selected_mode

    def set_selected_mode(self, value: str) -> None:
        if value != self._selected_mode:
            self._selected_mode = value
            self.selectedModeChanged.emit()

    @QtCore.Property(bool, notify=topmostChanged)
    def topmost(self) -> bool:
        return self._topmost

    def set_topmost(self, value: bool) -> None:
        if value != self._topmost:
            self._topmost = value
            self.topmostChanged.emit()

    @QtCore.Property(float, notify=displayFpsChanged)
    def displayFps(self) -> float:
        return self._display_fps

    def set_display_fps(self, value: float) -> None:
        if value != self._display_fps:
            self._display_fps = value
            self.displayFpsChanged.emit()

    @QtCore.Property(float, notify=processingFpsChanged)
    def processingFps(self) -> float:
        return self._processing_fps

    def set_processing_fps(self, value: float) -> None:
        if value != self._processing_fps:
            self._processing_fps = value
            self.processingFpsChanged.emit()

    @QtCore.Property(float, notify=handFpsChanged)
    def handFps(self) -> float:
        return self._hand_fps

    def set_hand_fps(self, value: float) -> None:
        if value != self._hand_fps:
            self._hand_fps = value
            self.handFpsChanged.emit()

    @QtCore.Property(float, notify=captureFpsChanged)
    def captureFps(self) -> float:
        return self._capture_fps

    def set_capture_fps(self, value: float) -> None:
        if value != self._capture_fps:
            self._capture_fps = value
            self.captureFpsChanged.emit()

    @QtCore.Property(float, notify=dropFpsChanged)
    def dropFps(self) -> float:
        return self._drop_fps

    def set_drop_fps(self, value: float) -> None:
        if value != self._drop_fps:
            self._drop_fps = value
            self.dropFpsChanged.emit()


def _set_windows_app_id(app_id: str) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _load_app_icon(icon_path: Path) -> QtGui.QIcon | None:
    if not icon_path.exists():
        return None

    if sys.platform.startswith("win"):
        ico_path = icon_path.with_suffix(".ico")
        if not ico_path.exists():
            pix = QtGui.QPixmap(str(icon_path))
            if not pix.isNull():
                try:
                    pix.save(str(ico_path), "ICO")
                except Exception:
                    pass
        if ico_path.exists():
            icon = QtGui.QIcon(str(ico_path))
            if not icon.isNull():
                return icon

    icon = QtGui.QIcon(str(icon_path))
    return None if icon.isNull() else icon


def display_loop(window_title: str = "FingerFlow") -> None:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")
    _set_windows_app_id("FingerFlow")
    app = QtGui.QGuiApplication([])
    
    # Set application icon for taskbar/windows.
    icon_path = Path(__file__).parent / "ui" / "Logo_fingerflow_V2.png"
    app_icon = _load_app_icon(icon_path)
    if app_icon is not None:
        app.setWindowIcon(app_icon)

    engine = QtQml.QQmlApplicationEngine()

    provider = CameraProvider()
    engine.addImageProvider("camera", provider)

    ui_state = UiState()
    engine.rootContext().setContextProperty("uiState", ui_state)
    engine.rootContext().setContextProperty(
        "modeKeyNormal", getattr(shared, "MODE_KEY_NORMAL", "N")
    )
    engine.rootContext().setContextProperty(
        "modeKeyDraw", getattr(shared, "MODE_KEY_DRAW", "D")
    )
    engine.rootContext().setContextProperty(
        "modeKeyZoom", getattr(shared, "MODE_KEY_ZOOM", "Z")
    )
    engine.rootContext().setContextProperty(
        "modeKeyScroll", getattr(shared, "MODE_KEY_SCROLL", "S")
    )
    engine.rootContext().setContextProperty(
        "modeKeyPause", getattr(shared, "MODE_KEY_PAUSE", "P")
    )
    engine.rootContext().setContextProperty(
        "modeKeyTop", getattr(shared, "MODE_KEY_TOP", "T")
    )
    engine.rootContext().setContextProperty(
        "defaultFrameW", getattr(shared, "FRAME_WIDTH", 640)
    )
    engine.rootContext().setContextProperty(
        "defaultFrameH", getattr(shared, "FRAME_HEIGHT", 480)
    )
    engine.rootContext().setContextProperty(
        "uiAssetPath", str((Path(__file__).parent / "ui").as_posix())
    )
    engine.rootContext().setContextProperty(
        "gestureIconUrl",
        QtCore.QUrl.fromLocalFile(
            str(Path(__file__).parent / "ui" / "main_close.png")
        ),
    )

    qml_path = Path(__file__).parent / "ui" / "fingerflow.qml"
    engine.load(QtCore.QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError("Failed to load QML UI.")

    root = engine.rootObjects()[0]
    root.setTitle(window_title)
    if app_icon is not None:
        root.setIcon(app_icon)

    def _on_quit() -> None:
        shared.stop_event.set()

    app.aboutToQuit.connect(_on_quit)

    last_fps_ts = time.time()
    frames = 0
    display_fps = 0.0
    last_topmost = None
    ui_visible = True

    def _tick() -> None:
        nonlocal frames, last_fps_ts, display_fps, last_topmost, ui_visible

        with shared.latest_lock:
            current_mode = getattr(shared, "current_mode", "normal")
            selected_mode = getattr(shared, "selected_mode", current_mode)
            topmost_enabled = getattr(shared, "topmost_enabled", True)
            proc_fps = getattr(shared, "processing_fps", 0.0)
            hand_fps = getattr(shared, "hand_fps", 0.0)
            capture_fps = getattr(shared, "capture_fps", 0.0)
            drop_fps = getattr(shared, "drop_fps", 0.0)

        if topmost_enabled and not ui_visible:
            root.show()
            ui_visible = True
        elif not topmost_enabled and ui_visible:
            root.hide()
            ui_visible = False

        # Slow down UI polling when hidden to reduce overhead.
        target_interval = 16 if ui_visible else 200
        if timer.interval() != target_interval:
            timer.setInterval(target_interval)

        with shared.latest_lock:
            shared.ui_visible = ui_visible

        camera_enabled = bool(topmost_enabled)
        frame = None
        detection = None
        if ui_visible and camera_enabled:
            with shared.latest_lock:
                frame = (
                    None if shared.latest_frame is None else shared.latest_frame.copy()
                )
                detection = shared.latest_detection

        if frame is not None:
            frame = cv2.flip(frame, 1)
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
                display_fps = frames / (now - last_fps_ts)
                last_fps_ts = now
                frames = 0

            qimg = _to_qimage(frame)
            provider.set_image(qimg)
            ui_state.bump_image()
        elif not camera_enabled:
            frames = 0
            display_fps = 0.0
        elif not ui_visible:
            frames = 0

        ui_state.set_mode(str(current_mode))
        ui_state.set_selected_mode(str(selected_mode))
        ui_state.set_topmost(bool(topmost_enabled))
        ui_state.set_display_fps(float(display_fps))
        ui_state.set_processing_fps(float(proc_fps))
        ui_state.set_hand_fps(float(hand_fps))
        ui_state.set_capture_fps(float(capture_fps))
        ui_state.set_drop_fps(float(drop_fps))

        if topmost_enabled != last_topmost:
            last_topmost = topmost_enabled
            flags = root.flags()
            if topmost_enabled:
                root.setFlags(flags | QtCore.Qt.WindowType.WindowStaysOnTopHint)
            else:
                root.setFlags(flags & ~QtCore.Qt.WindowType.WindowStaysOnTopHint)

        if shared.stop_event.is_set():
            app.quit()

    timer = QtCore.QTimer()
    timer.timeout.connect(_tick)
    timer.start(16)

    app.exec()
