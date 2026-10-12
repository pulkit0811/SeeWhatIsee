import ctypes
import os
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, Signal, QObject


class GlobalHotkey(QObject, QAbstractNativeEventFilter):
    """Register a Windows-wide hotkey without adding a third-party dependency."""

    pressed = Signal()

    _hotkey_id = 0x5349
    _fallback_hotkey_id = 0x534A
    _wm_hotkey = 0x0312
    _mod_control = 0x0002
    _mod_windows = 0x0008
    _mod_alt = 0x0001
    _mod_norepeat = 0x4000
    _vk_space = 0x20

    def __init__(self) -> None:
        QObject.__init__(self)
        QAbstractNativeEventFilter.__init__(self)
        self._registered = False
        self._active_id = None
        self.shortcut_text = "Ctrl+Win+Space"

    def register(self) -> bool:
        if os.name != "nt":
            return False
        self._registered = bool(ctypes.windll.user32.RegisterHotKey(
            None,
            self._hotkey_id,
            self._mod_control | self._mod_windows | self._mod_norepeat,
            self._vk_space,
        ))
        if self._registered:
            self._active_id = self._hotkey_id
            return True

        self._registered = bool(ctypes.windll.user32.RegisterHotKey(
            None,
            self._fallback_hotkey_id,
            self._mod_control | self._mod_alt | self._mod_norepeat,
            self._vk_space,
        ))
        if self._registered:
            self._active_id = self._fallback_hotkey_id
            self.shortcut_text = "Ctrl+Alt+Space"
        return self._registered

    def unregister(self) -> None:
        if self._registered and os.name == "nt":
            ctypes.windll.user32.UnregisterHotKey(None, self._active_id)
            self._registered = False
            self._active_id = None

    def nativeEventFilter(self, event_type, message):
        if event_type not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
            return False, 0

        msg = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
        if msg.message == self._wm_hotkey and msg.wParam == self._active_id:
            self.pressed.emit()
            return True, 0
        return False, 0


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", _POINT),
    ]
