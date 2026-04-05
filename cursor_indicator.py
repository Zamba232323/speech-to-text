import ctypes
import ctypes.wintypes
import threading
import tkinter as tk

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080

user32 = ctypes.windll.user32


class CursorIndicator:
    """Small colored circle overlay that follows the mouse cursor."""

    def __init__(self):
        self._root = None
        self._canvas = None
        self._thread = None
        self._color = None
        self._visible = False
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._start_ui_thread()

    def _start_ui_thread(self):
        self._thread = threading.Thread(target=self._ui_loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _ui_loop(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-transparentcolor", "#010101")

        size = 22
        self._canvas = tk.Canvas(
            self._root, width=size, height=size,
            bg="#010101", highlightthickness=0,
        )
        self._canvas.pack()
        self._circle_id = self._canvas.create_oval(
            3, 3, size - 3, size - 3, fill="red", outline="black", width=1,
        )

        # Make window click-through
        self._root.update_idletasks()
        hwnd = user32.GetParent(self._root.winfo_id())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW,
        )

        self._ready.set()
        self._follow_mouse()
        self._root.mainloop()

    def _follow_mouse(self):
        if self._visible:
            pos = ctypes.wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pos))
            self._root.geometry(f"+{pos.x + 18}+{pos.y + 18}")
            self._root.deiconify()
        else:
            self._root.withdraw()
        self._root.after(30, self._follow_mouse)

    def set_recording(self):
        self._ready.wait()
        self._canvas.itemconfig(self._circle_id, fill="#FF0000")
        self._visible = True

    def set_transcribing(self):
        self._ready.wait()
        self._canvas.itemconfig(self._circle_id, fill="#FFD700")
        self._visible = True

    def set_idle(self):
        self._visible = False
