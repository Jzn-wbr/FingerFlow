"""Mouse control based on hand landmarks."""

from __future__ import annotations

import ctypes
import subprocess
from ctypes import wintypes
import math
import time
from typing import Iterable, Sequence, Tuple

from . import shared
import win32api
import win32con
try:
    import keyboard as _keyboard_lib
except Exception:
    _keyboard_lib = None

# Cache screen size once; no need to query Win32 on every cursor move.
screen_w = ctypes.windll.user32.GetSystemMetrics(0)
screen_h = ctypes.windll.user32.GetSystemMetrics(1)

# Landmark indices used to approximate the palm center.
_PALM_IDXS: Tuple[int, ...] = (0, 1, 5, 9, 13, 17)

# Hysteresis thresholds (normalized coordinates) to avoid noisy toggles.
TOUCH_THRESHOLD = 0.055
RELEASE_THRESHOLD = 0.065

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

_ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

_HOOK_HANDLE = None
_HOOK_PROC = None
_BLOCK_KEYS: set[int] = set()
_MODE_SELECT_ACTIVE = False


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


def _keyboard_proc(n_code, w_param, l_param):
    if n_code == 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
        kb = ctypes.cast(l_param, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
        if _MODE_SELECT_ACTIVE and kb.vkCode in _BLOCK_KEYS:
            return 1
    return ctypes.windll.user32.CallNextHookEx(_HOOK_HANDLE, n_code, w_param, l_param)


def _install_keyboard_hook() -> None:
    global _HOOK_HANDLE, _HOOK_PROC
    if _HOOK_HANDLE:
        return
    _HOOK_PROC = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
    )(_keyboard_proc)
    h_mod = ctypes.windll.kernel32.GetModuleHandleW(None)
    _HOOK_HANDLE = ctypes.windll.user32.SetWindowsHookExW(
        WH_KEYBOARD_LL, _HOOK_PROC, h_mod, 0
    )


def _remove_keyboard_hook() -> None:
    global _HOOK_HANDLE, _HOOK_PROC
    if _HOOK_HANDLE:
        ctypes.windll.user32.UnhookWindowsHookEx(_HOOK_HANDLE)
        _HOOK_HANDLE = None
        _HOOK_PROC = None


def _pump_messages() -> None:
    msg = _MSG()
    while ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
        ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
        ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))


def _mouse_event(flag: int) -> None:
    """Send a Win32 mouse event and ignore failures."""
    try:
        win32api.mouse_event(flag, 0, 0, 0, 0)
    except Exception:
        pass


def _mouse_left_down() -> None:
    _mouse_event(win32con.MOUSEEVENTF_LEFTDOWN)


def _mouse_left_up() -> None:
    _mouse_event(win32con.MOUSEEVENTF_LEFTUP)


def _mouse_right_down() -> None:
    _mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN)


def _mouse_right_up() -> None:
    _mouse_event(win32con.MOUSEEVENTF_RIGHTUP)


def _mouse_wheel(delta: int) -> None:
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
    except Exception:
        pass


def _landmark_distance(
    landmarks: Sequence[Tuple[float, float, float | None]],
    idx_a: int,
    idx_b: int,
) -> float | None:
    """Return Euclidean distance between two landmarks or None if missing."""
    if len(landmarks) <= max(idx_a, idx_b):
        return None

    ax, ay, _ = landmarks[idx_a]
    bx, by, _ = landmarks[idx_b]
    return math.hypot(ax - bx, ay - by)


def _is_fist(
    landmarks: Sequence[Tuple[float, float, float | None]],
    threshold: float,
) -> bool:
    """Return True when fingers are folded close to the palm."""
    pairs = ((8, 5), (12, 9), (16, 13), (20, 17))
    dists = []
    for tip, base in pairs:
        dist = _landmark_distance(landmarks, tip, base)
        if dist is None:
            return False
        dists.append(dist)
    return (sum(dists) / len(dists)) < threshold


def _map_to_screen(
    x_norm: float,
    y_norm: float,
    scale_x: float,
    scale_y: float,
    offset_x: float,
    offset_y: float,
) -> tuple[int, int]:
    """Convert normalized coords (0..1) into pixel coordinates with scaling."""
    if scale_x <= 0:
        scale_x = 1.0
    if scale_y <= 0:
        scale_y = 1.0

    x_mapped = 0.5 + (x_norm - 0.5) * scale_x + offset_x
    y_mapped = 0.5 + (y_norm - 0.5) * scale_y + offset_y
    x_mapped = max(0.0, min(1.0, float(x_mapped)))
    y_mapped = max(0.0, min(1.0, float(y_mapped)))

    return int(x_mapped * screen_w), int(y_mapped * screen_h)


def _palm_center(
    landmarks: Sequence[Tuple[float, float, float | None]],
) -> tuple[float, float] | None:
    """Compute normalized palm center from selected landmarks."""
    points = [landmarks[i] for i in _PALM_IDXS if i < len(landmarks)]
    if not points:
        return None

    avg_x = sum(p[0] for p in points) / len(points)
    avg_y = sum(p[1] for p in points) / len(points)
    # Flip horizontally to match mirrored preview.
    return 1.0 - avg_x, avg_y


def _update_click_state(
    distance: float | None,
    pressed: bool,
    press_fn,
    release_fn,
) -> bool:
    """Apply hysteresis to update click state and trigger mouse events."""
    if distance is None:
        if pressed:
            release_fn()
        return False

    if not pressed and distance <= TOUCH_THRESHOLD:
        press_fn()
        return True

    if pressed and distance > RELEASE_THRESHOLD:
        release_fn()
        return False

    return pressed


def _safe_set_cursor(pos: Iterable[int]) -> None:
    try:
        win32api.SetCursorPos(tuple(pos))
    except Exception:
        pass


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


def _send_mouse_move_abs(pos: Iterable[int]) -> None:
    """Send absolute mouse move via SendInput to emit real move events."""
    try:
        x, y = tuple(pos)
        x = max(0, min(screen_w - 1, int(x)))
        y = max(0, min(screen_h - 1, int(y)))
        abs_x = int(x * 65535 / max(1, screen_w - 1))
        abs_y = int(y * 65535 / max(1, screen_h - 1))
        flags = win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE
        mi = _MOUSEINPUT(abs_x, abs_y, 0, flags, 0, None)
        inp = _INPUT(0, _INPUT_UNION(mi=mi))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    except Exception:
        _safe_set_cursor(pos)


def _move_cursor_smooth(
    target: tuple[int, int],
    last_pos: tuple[int, int] | None,
    step_px: int = 6,
) -> tuple[int, int]:
    """Interpolate cursor moves to avoid teleporting during drawing."""
    if last_pos is None:
        _send_mouse_move_abs(target)
        return target

    lx, ly = last_pos
    tx, ty = target
    dx = tx - lx
    dy = ty - ly
    dist = math.hypot(dx, dy)
    if dist <= step_px:
        _send_mouse_move_abs(target)
        return target

    steps = max(1, int(dist / step_px))
    for i in range(1, steps + 1):
        nx = int(lx + dx * (i / steps))
        ny = int(ly + dy * (i / steps))
        _send_mouse_move_abs((nx, ny))
    return target


def _ema_filter(
    target: tuple[int, int],
    last_filtered: tuple[float, float] | None,
    alpha: float,
) -> tuple[float, float]:
    """Low-pass filter to smooth jitter before sending mouse moves."""
    if last_filtered is None:
        return float(target[0]), float(target[1])
    lx, ly = last_filtered
    tx, ty = target
    fx = lx + (tx - lx) * alpha
    fy = ly + (ty - ly) * alpha
    return fx, fy


def _vk_for_key(key: str) -> int:
    key = key.strip().upper()
    if key.startswith("F") and key[1:].isdigit():
        num = int(key[1:])
        if 1 <= num <= 24:
            return getattr(win32con, f"VK_F{num}")
    if len(key) == 1:
        return ord(key)
    return ord(key[0])


def _key_down(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def _send_key_combo(mod_vk: int, key_vk: int) -> None:
    try:
        inputs = (_INPUT * 4)(
            _INPUT(1, _INPUT_UNION(ki=_KEYBDINPUT(mod_vk, 0, 0, 0, None))),
            _INPUT(1, _INPUT_UNION(ki=_KEYBDINPUT(key_vk, 0, 0, 0, None))),
            _INPUT(
                1,
                _INPUT_UNION(
                    ki=_KEYBDINPUT(key_vk, 0, win32con.KEYEVENTF_KEYUP, 0, None)
                ),
            ),
            _INPUT(
                1,
                _INPUT_UNION(
                    ki=_KEYBDINPUT(mod_vk, 0, win32con.KEYEVENTF_KEYUP, 0, None)
                ),
            ),
        )
        ctypes.windll.user32.SendInput(
            4, ctypes.byref(inputs), ctypes.sizeof(_INPUT)
        )
    except Exception:
        pass


def _key_name(key: str) -> str:
    key = key.strip()
    if not key:
        return ""
    return key.lower()


def _start_draw_app() -> subprocess.Popen | None:
    app = getattr(shared, "DRAW_APP", "mspaint.exe")
    try:
        return subprocess.Popen([app])
    except Exception:
        return None


def _stop_draw_app(proc: subprocess.Popen | None) -> None:
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=1)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def mouse_thread() -> None:
    """Move cursor based on palm center and implement pinch-to-click."""
    global _MODE_SELECT_ACTIVE
    left_pressed = False
    right_pressed = False
    screen_scale_x = getattr(shared, "SCREEN_SCALE_X", 1.25)
    screen_scale_y = getattr(shared, "SCREEN_SCALE_Y", 1.25)
    screen_offset_x = getattr(shared, "SCREEN_OFFSET_X", 0.0)
    screen_offset_y = getattr(shared, "SCREEN_OFFSET_Y", 0.0)
    last_pos: tuple[int, int] | None = None
    last_filtered: tuple[float, float] | None = None
    smooth_alpha = getattr(shared, "MOUSE_SMOOTH_ALPHA", 0.25)
    step_px = getattr(shared, "MOUSE_STEP_PX", 6)
    fist_threshold = getattr(shared, "FIST_THRESHOLD", 0.08)
    click_freeze_ms = getattr(shared, "CLICK_FREEZE_MS", 120)
    mode = "normal"
    with shared.latest_lock:
        shared.current_mode = mode
        shared.selected_mode = mode
    draw_proc: subprocess.Popen | None = None
    key_map = {
        "draw": _vk_for_key(getattr(shared, "MODE_KEY_DRAW", "D")),
        "normal": _vk_for_key(getattr(shared, "MODE_KEY_NORMAL", "S")),
        "zoom": _vk_for_key(getattr(shared, "MODE_KEY_ZOOM", "Z")),
        "scroll": _vk_for_key(getattr(shared, "MODE_KEY_SCROLL", "S")),
        "pause": _vk_for_key(getattr(shared, "MODE_KEY_PAUSE", "P")),
    }
    key_name_map = {
        "draw": _key_name(getattr(shared, "MODE_KEY_DRAW", "D")),
        "normal": _key_name(getattr(shared, "MODE_KEY_NORMAL", "S")),
        "zoom": _key_name(getattr(shared, "MODE_KEY_ZOOM", "Z")),
        "scroll": _key_name(getattr(shared, "MODE_KEY_SCROLL", "S")),
        "pause": _key_name(getattr(shared, "MODE_KEY_PAUSE", "P")),
    }
    top_toggle_key = _vk_for_key(getattr(shared, "MODE_KEY_TOP", "F"))
    top_toggle_name = _key_name(getattr(shared, "MODE_KEY_TOP", "F"))
    block_key_names = [
        key_name_map["draw"],
        key_name_map["normal"],
        key_name_map["zoom"],
        key_name_map["scroll"],
        key_name_map["pause"],
        top_toggle_name,
    ]
    block_key_names = [name for name in block_key_names if name]
    keyboard_blocked = False
    use_keyboard_state = False
    zoom_in_vk = getattr(win32con, "VK_OEM_PLUS", 0xBB)
    zoom_out_vk = getattr(win32con, "VK_OEM_MINUS", 0xBD)
    zoom_cooldown = 0.15
    zoom_last_in = 0.0
    zoom_last_out = 0.0
    scroll_cooldown = 0.08
    scroll_last_down = 0.0
    scroll_last_up = 0.0
    click_freeze_until = 0.0
    click_freeze_anchor: tuple[int, int] | None = None
    last_key_state = {name: False for name in key_map}
    top_toggle_state = False
    _BLOCK_KEYS.clear()
    _BLOCK_KEYS.update(key_map.values())
    _BLOCK_KEYS.add(top_toggle_key)
    _install_keyboard_hook()
    try:
        while not shared.stop_event.is_set():
            time.sleep(0.002)
            _pump_messages()

            with shared.latest_lock:
                data = shared.latest_detection

            if not data:
                # Release buttons if the hand disappears to avoid stuck presses.
                if left_pressed:
                    _mouse_left_up()
                    left_pressed = False
                if right_pressed:
                    _mouse_right_up()
                    right_pressed = False
                continue

            if isinstance(data, dict) and "landmarks" in data:
                lm = data["landmarks"]
                fist = _is_fist(lm, fist_threshold)

                if fist:
                    _MODE_SELECT_ACTIVE = True
                    if _keyboard_lib and not keyboard_blocked:
                        for name in block_key_names:
                            _keyboard_lib.block_key(name)
                        keyboard_blocked = True
                        use_keyboard_state = True
                    with shared.latest_lock:
                        shared.current_mode = "mode select"
                    for name, vk in key_map.items():
                        if _keyboard_lib and use_keyboard_state and key_name_map[name]:
                            pressed = _keyboard_lib.is_pressed(key_name_map[name])
                        else:
                            pressed = _key_down(vk)
                        if pressed and not last_key_state[name]:
                            if mode != name:
                                mode = name
                                last_pos = None
                                last_filtered = None
                                if left_pressed:
                                    _mouse_left_up()
                                    left_pressed = False
                                if right_pressed:
                                    _mouse_right_up()
                                    right_pressed = False
                                if mode == "draw":
                                    if (
                                        draw_proc is None
                                        or draw_proc.poll() is not None
                                    ):
                                        draw_proc = _start_draw_app()
                                else:
                                    _stop_draw_app(draw_proc)
                                    draw_proc = None
                                with shared.latest_lock:
                                    shared.selected_mode = mode
                        last_key_state[name] = pressed
                    if _keyboard_lib and use_keyboard_state and top_toggle_name:
                        top_pressed = _keyboard_lib.is_pressed(top_toggle_name)
                    else:
                        top_pressed = _key_down(top_toggle_key)
                    if top_pressed and not top_toggle_state:
                        with shared.latest_lock:
                            shared.topmost_enabled = not getattr(
                                shared, "topmost_enabled", True
                            )
                        top_toggle_state = True
                    elif not top_pressed:
                        top_toggle_state = False
                else:
                    _MODE_SELECT_ACTIVE = False
                    if _keyboard_lib and keyboard_blocked:
                        for name in block_key_names:
                            _keyboard_lib.unblock_key(name)
                        keyboard_blocked = False
                        use_keyboard_state = False
                    for name, vk in key_map.items():
                        last_key_state[name] = _key_down(vk)
                    top_toggle_state = False
                    with shared.latest_lock:
                        shared.current_mode = mode

                if fist:
                    continue

                if mode == "pause":
                    continue

                center = _palm_center(lm)
                desired_pos: tuple[int, int] | None = None
                if center:
                    x_norm, y_norm = center
                    target = _map_to_screen(
                        x_norm,
                        y_norm,
                        screen_scale_x,
                        screen_scale_y,
                        screen_offset_x,
                        screen_offset_y,
                    )
                    fx, fy = _ema_filter(target, last_filtered, smooth_alpha)
                    last_filtered = (fx, fy)
                    desired_pos = (int(fx), int(fy))

                # Left click (thumb-index pinch).
                dist_left = _landmark_distance(lm, 4, 8)
                if mode == "zoom":
                    now = time.monotonic()
                    if dist_left is None:
                        left_pressed = False
                    elif not left_pressed and dist_left <= TOUCH_THRESHOLD:
                        if now - zoom_last_in >= zoom_cooldown:
                            _send_key_combo(win32con.VK_CONTROL, zoom_in_vk)
                            zoom_last_in = now
                        left_pressed = True
                    elif left_pressed and dist_left > RELEASE_THRESHOLD:
                        left_pressed = False
                elif mode == "scroll":
                    now = time.monotonic()
                    if dist_left is None:
                        left_pressed = False
                    elif not left_pressed and dist_left <= TOUCH_THRESHOLD:
                        if now - scroll_last_down >= scroll_cooldown:
                            _mouse_wheel(-120)
                            scroll_last_down = now
                        left_pressed = True
                    elif left_pressed and dist_left > RELEASE_THRESHOLD:
                        left_pressed = False
                else:
                    now = time.monotonic()
                    prev_left = left_pressed
                    left_pressed = _update_click_state(
                        dist_left, left_pressed, _mouse_left_down, _mouse_left_up
                    )
                    if mode == "normal":
                        if left_pressed and not prev_left:
                            click_freeze_until = now + (click_freeze_ms / 1000.0)
                            click_freeze_anchor = desired_pos or last_pos
                        elif not left_pressed:
                            click_freeze_until = 0.0
                            click_freeze_anchor = None
                    else:
                        click_freeze_until = 0.0
                        click_freeze_anchor = None

                # Right click (thumb-middle pinch).
                dist_right = _landmark_distance(lm, 4, 12)
                if mode == "zoom":
                    now = time.monotonic()
                    if dist_right is None:
                        right_pressed = False
                    elif not right_pressed and dist_right <= TOUCH_THRESHOLD:
                        if now - zoom_last_out >= zoom_cooldown:
                            _send_key_combo(win32con.VK_CONTROL, zoom_out_vk)
                            zoom_last_out = now
                        right_pressed = True
                    elif right_pressed and dist_right > RELEASE_THRESHOLD:
                        right_pressed = False
                elif mode == "scroll":
                    now = time.monotonic()
                    if dist_right is None:
                        right_pressed = False
                    elif not right_pressed and dist_right <= TOUCH_THRESHOLD:
                        if now - scroll_last_up >= scroll_cooldown:
                            _mouse_wheel(120)
                            scroll_last_up = now
                        right_pressed = True
                    elif right_pressed and dist_right > RELEASE_THRESHOLD:
                        right_pressed = False
                else:
                    right_pressed = _update_click_state(
                        dist_right, right_pressed, _mouse_right_down, _mouse_right_up
                    )

                if desired_pos:
                    if (
                        mode == "normal"
                        and left_pressed
                        and click_freeze_until > time.monotonic()
                        and click_freeze_anchor
                    ):
                        last_pos = click_freeze_anchor
                    else:
                        last_pos = _move_cursor_smooth(
                            desired_pos, last_pos, step_px=step_px
                        )
            else:
                # Legacy tuple movement only (no pinch available).
                try:
                    x_norm, y_norm, _ = data
                except Exception:
                    continue

                x_norm = 1.0 - x_norm
                target = _map_to_screen(
                    x_norm,
                    y_norm,
                    screen_scale_x,
                    screen_scale_y,
                    screen_offset_x,
                    screen_offset_y,
                )
                fx, fy = _ema_filter(target, last_filtered, smooth_alpha)
                last_filtered = (fx, fy)
                last_pos = _move_cursor_smooth(
                    (int(fx), int(fy)), last_pos, step_px=step_px
                )
    finally:
        if _keyboard_lib and keyboard_blocked:
            for name in block_key_names:
                _keyboard_lib.unblock_key(name)
        _remove_keyboard_hook()
