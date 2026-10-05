"""Modern GUI using DearPyGui for high-performance display."""

from __future__ import annotations

import time
from typing import Sequence, Tuple

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

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
        cv2.putText(
            frame,
            str(i),
            (pt[0] + 4, pt[1] - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (220, 220, 230),
            1,
        )


def _build_theme() -> None:
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (16, 18, 24, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (28, 30, 40, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (36, 40, 54, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (232, 234, 242, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (48, 54, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (40, 46, 60, 255))
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 14, 14)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
    dpg.bind_theme(theme)


def _set_topmost(enabled: bool) -> None:
    try:
        dpg.set_viewport_always_top(enabled)
    except Exception:
        pass


def _make_gradient(
    width: int,
    height: int,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
    use_float: bool,
) -> np.ndarray:
    """Return a vertical gradient RGBA texture."""
    top = np.array(top_color, dtype=np.float32)
    bottom = np.array(bottom_color, dtype=np.float32)
    grad = np.linspace(0.0, 1.0, height, dtype=np.float32).reshape(height, 1, 1)
    rgb = top + (bottom - top) * grad
    rgb = np.repeat(rgb, width, axis=1)
    alpha = np.full((height, width, 1), 255.0, dtype=np.float32)
    rgba = np.concatenate([rgb, alpha], axis=2)
    if use_float:
        return (rgba / 255.0).astype(np.float32)
    return rgba.astype(np.uint8)


def display_loop(window_title: str = "FingerFlow") -> None:
    panel_w = 320
    window_padding = 14
    item_spacing = 10
    default_w = getattr(shared, "FRAME_WIDTH", 640)
    default_h = getattr(shared, "FRAME_HEIGHT", 480)
    accent = (90, 170, 255, 255)
    muted = (160, 166, 182, 255)
    active = (90, 230, 150, 255)
    warn = (20, 210, 255, 255)
    bg_top = (16, 18, 24)
    bg_bottom = (8, 10, 16)
    panel_top = (30, 32, 46)
    panel_bottom = (18, 20, 30)
    shadow = (0, 0, 0, 110)

    dpg.create_context()
    _build_theme()

    texture_tag = "camera_texture"
    image_tag = "camera_image"
    bg_texture_tag = "bg_gradient"
    panel_texture_tag = "panel_gradient"

    fmt_uchar = getattr(dpg, "mvFormat_Uchar_rgba", None)
    fmt_float = getattr(dpg, "mvFormat_Float_rgba", None)
    texture_format = fmt_uchar or fmt_float
    use_float = texture_format == fmt_float

    with dpg.texture_registry(show=False):
        dpg.add_raw_texture(
            640,
            480,
            np.zeros((480, 640, 4), dtype=np.float32 if use_float else np.uint8),
            format=texture_format,
            tag=texture_tag,
        )
        dpg.add_raw_texture(
            256,
            256,
            _make_gradient(256, 256, bg_top, bg_bottom, use_float),
            format=texture_format,
            tag=bg_texture_tag,
        )
        dpg.add_raw_texture(
            256,
            256,
            _make_gradient(256, 256, panel_top, panel_bottom, use_float),
            format=texture_format,
            tag=panel_texture_tag,
        )

    with dpg.window(tag="main_window", no_title_bar=True, no_resize=True, no_move=True):
        dpg.add_draw_layer(tag="bg_layer")
        dpg.add_draw_layer(tag="panel_layer")
        with dpg.group(horizontal=True):
            with dpg.child_window(tag="view_panel", border=False, width=default_w, height=default_h):
                dpg.add_image(texture_tag, tag=image_tag)
            with dpg.child_window(
                width=panel_w, height=default_h, tag="side_panel", border=False, autosize_y=False
            ):
                dpg.add_text("FINGERFLOW", color=accent)
                with dpg.group(horizontal=True):
                    dpg.add_text("CONTROL PANEL", color=muted)
                    dpg.add_spacer(width=8)
                    dpg.add_button(label="INFO", width=54, height=22, tag="info_button")
                dpg.add_separator()
                dpg.add_text("STATUS", color=muted)
                dpg.add_text("mode select", tag="status_value", color=warn)
                dpg.add_spacer(height=4)
                dpg.add_text("TOPMOST", color=muted)
                dpg.add_text("ON", tag="topmost_value", color=active)
                dpg.add_separator()
                dpg.add_text("MODES", color=muted)
                dpg.add_text("NORMAL", tag="mode_normal", color=active)
                dpg.add_text("DRAW", tag="mode_draw", color=muted)
                dpg.add_text("ZOOM", tag="mode_zoom", color=muted)
                dpg.add_text("SCROLL", tag="mode_scroll", color=muted)
                dpg.add_text("PAUSE", tag="mode_pause", color=muted)
                dpg.add_separator()
                dpg.add_text("DISPLAY FPS", color=muted)
                dpg.add_text("--", tag="fps_value", color=accent)
                dpg.add_spacer(height=2)
                dpg.add_text("PROC FPS", color=muted)
                dpg.add_text("--", tag="proc_fps_value", color=accent)
                dpg.add_spacer(height=8)
                dpg.add_text("KEYS", color=muted)
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_NORMAL', 'N').upper()}: normal",
                    tag="key_normal",
                )
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_DRAW', 'D').upper()}: draw",
                    tag="key_draw",
                )
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_ZOOM', 'Z').upper()}: zoom",
                    tag="key_zoom",
                )
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_SCROLL', 'S').upper()}: scroll",
                    tag="key_scroll",
                )
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_PAUSE', 'P').upper()}: pause",
                    tag="key_pause",
                )
                dpg.add_text(
                    f"{getattr(shared, 'MODE_KEY_TOP', 'T').upper()}: topmost",
                    tag="key_top",
                )

    with dpg.window(
        tag="info_popup",
        modal=True,
        show=False,
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        width=380,
        height=210,
    ):
        dpg.add_text("FINGERFLOW STATUS", color=accent)
        dpg.add_text(
            "Preview + tracking in real time.\n"
            "Capture/detection stay on worker threads.\n"
            "UI is GPU-driven for smooth rendering.",
            color=muted,
        )
        dpg.add_spacer(height=8)
        dpg.add_text("TIPS", color=muted)
        dpg.add_text("Keep lighting stable for best tracking.", color=muted)
        dpg.add_spacer(height=10)
        dpg.add_button(
            label="CLOSE",
            width=120,
            height=28,
            callback=lambda: dpg.hide_item("info_popup"),
        )

    dpg.set_primary_window("main_window", True)
    initial_total_w = default_w + panel_w + (window_padding * 2) + item_spacing
    initial_total_h = default_h + (window_padding * 2)
    dpg.configure_item("main_window", width=initial_total_w, height=initial_total_h)
    dpg.create_viewport(
        title=window_title,
        width=initial_total_w + 80,
        height=initial_total_h + 80,
        resizable=False,
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_viewport_vsync(False)

    def _open_info() -> None:
        dpg.show_item("info_popup")
        total_w = dpg.get_item_width("main_window")
        total_h = dpg.get_item_height("main_window")
        dpg.set_item_pos(
            "info_popup",
            [int((total_w - 380) / 2), int((total_h - 210) / 2)],
        )

    dpg.configure_item("info_button", callback=lambda: _open_info())

    def _on_exit() -> None:
        shared.stop_event.set()

    dpg.set_exit_callback(_on_exit)

    last_fps_ts = time.time()
    frames = 0
    fps = 0.0
    last_topmost = None
    last_size = (default_w, default_h)
    last_layout = None

    def _redraw_layers() -> None:
        panel_pos = dpg.get_item_pos("side_panel")
        panel_w_curr = dpg.get_item_width("side_panel")
        panel_h_curr = dpg.get_item_height("side_panel")
        total_w = dpg.get_item_width("main_window")
        total_h = dpg.get_item_height("main_window")

        layout_sig = (panel_pos, panel_w_curr, panel_h_curr, total_w, total_h)
        nonlocal last_layout
        if layout_sig == last_layout:
            return
        last_layout = layout_sig

        dpg.delete_item("bg_layer", children_only=True)
        dpg.delete_item("panel_layer", children_only=True)

        dpg.draw_image(
            bg_texture_tag,
            pmin=(0, 0),
            pmax=(total_w, total_h),
            parent="bg_layer",
        )
        x, y = panel_pos
        dpg.draw_rectangle(
            pmin=(x + 3, y + 6),
            pmax=(x + panel_w_curr + 3, y + panel_h_curr + 6),
            color=(0, 0, 0, 0),
            fill=shadow,
            rounding=10,
            parent="panel_layer",
        )
        dpg.draw_image(
            panel_texture_tag,
            pmin=(x, y),
            pmax=(x + panel_w_curr, y + panel_h_curr),
            parent="panel_layer",
        )
        dpg.draw_rectangle(
            pmin=(x, y),
            pmax=(x + panel_w_curr, y + panel_h_curr),
            color=(60, 66, 84, 180),
            rounding=10,
            parent="panel_layer",
        )

    try:
        while dpg.is_dearpygui_running() and not shared.stop_event.is_set():
            with shared.latest_lock:
                current_mode = getattr(shared, "current_mode", "normal")
                selected_mode = getattr(shared, "selected_mode", current_mode)
                topmost_enabled = getattr(shared, "topmost_enabled", True)
                proc_fps = getattr(shared, "processing_fps", 0.0)
                if not topmost_enabled:
                    frame = None
                    detection = None
                else:
                    frame = (
                        None
                        if shared.latest_frame is None
                        else shared.latest_frame.copy()
                    )
                    detection = shared.latest_detection

            if topmost_enabled != last_topmost:
                _set_topmost(topmost_enabled)
                last_topmost = topmost_enabled

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
                    fps = frames / (now - last_fps_ts)
                    last_fps_ts = now
                    frames = 0

                h, w = frame.shape[:2]
                if (w, h) != last_size:
                    last_size = (w, h)
                    dpg.delete_item(texture_tag)
                    with dpg.texture_registry(show=False):
                        dpg.add_raw_texture(
                            w,
                            h,
                            np.zeros((h, w, 4), dtype=np.float32 if use_float else np.uint8),
                            format=texture_format,
                            tag=texture_tag,
                        )
                    dpg.configure_item(image_tag, texture_tag=texture_tag)
                    dpg.configure_item("view_panel", width=w, height=h)
                    dpg.configure_item("side_panel", width=panel_w, height=h)
                    total_w = w + panel_w + (window_padding * 2) + item_spacing
                    total_h = h + (window_padding * 2)
                    dpg.configure_item("main_window", width=total_w, height=total_h)
                    dpg.set_viewport_width(total_w + 80)
                    dpg.set_viewport_height(total_h + 80)
                    _redraw_layers()

                rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                rgba = np.ascontiguousarray(rgba)
                if use_float:
                    rgba = rgba.astype(np.float32) / 255.0
                dpg.set_value(texture_tag, rgba)
            elif not topmost_enabled:
                frames = 0
                fps = 0.0

            _redraw_layers()

            status_color = warn if current_mode == "mode select" else active
            dpg.set_value("status_value", current_mode.upper())
            dpg.configure_item("status_value", color=status_color)
            dpg.set_value("topmost_value", "ON" if topmost_enabled else "OFF")
            dpg.configure_item(
                "topmost_value", color=active if topmost_enabled else muted
            )
            dpg.set_value("fps_value", f"{fps:.1f}")
            dpg.set_value("proc_fps_value", f"{proc_fps:.1f}")

            for name, tag in (
                ("normal", "mode_normal"),
                ("draw", "mode_draw"),
                ("zoom", "mode_zoom"),
                ("scroll", "mode_scroll"),
                ("pause", "mode_pause"),
            ):
                is_active = selected_mode == name
                dpg.configure_item(tag, color=active if is_active else muted)

            dpg.render_dearpygui_frame()
    finally:
        shared.stop_event.set()
        dpg.destroy_context()
