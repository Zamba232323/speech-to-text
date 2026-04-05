import ctypes
import ctypes.wintypes
import tempfile
import os
from PIL import Image, ImageDraw

user32 = ctypes.windll.user32

# Windows cursor IDs
OCR_NORMAL = 32512
OCR_APPSTARTING = 32650

# SetSystemCursor replaces a system cursor until SPI_SETCURSORS restores all
SPI_SETCURSORS = 0x0057


def _create_cursor_file(color, size=32):
    """Create a .cur file with a colored circle next to the normal arrow."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw arrow pointer (simplified)
    arrow_points = [
        (0, 0), (0, 20), (5, 16), (9, 24), (12, 23), (8, 15), (14, 14)
    ]
    draw.polygon(arrow_points, fill="white", outline="black")

    # Draw colored circle indicator (bottom-right of cursor)
    circle_x, circle_y = 16, 16
    circle_r = 7
    draw.ellipse(
        [circle_x - circle_r, circle_y - circle_r,
         circle_x + circle_r, circle_y + circle_r],
        fill=color, outline="black", width=1,
    )

    # Save as .cur (Windows .ico format works as .cur with hotspot 0,0)
    tmp = tempfile.NamedTemporaryFile(suffix=".cur", delete=False, dir=tempfile.gettempdir())
    # Save as ICO which Windows can load as cursor
    img.save(tmp.name, format="ICO", sizes=[(size, size)])
    tmp.close()
    return tmp.name


def _load_cursor_from_file(path):
    """Load a cursor from a .cur/.ico file."""
    IMAGE_CURSOR = 2
    LR_LOADFROMFILE = 0x0010
    LR_DEFAULTSIZE = 0x0040
    handle = user32.LoadImageW(
        None, path, IMAGE_CURSOR, 0, 0,
        LR_LOADFROMFILE | LR_DEFAULTSIZE,
    )
    return handle


def _force_cursor_refresh():
    """Nudge the cursor position to force Windows to redraw it immediately."""
    pos = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pos))
    user32.SetCursorPos(pos.x, pos.y)


class CursorIndicator:
    def __init__(self):
        self._active = False
        self._cursor_files = []

    def set_recording(self):
        """Change cursor to show red circle (recording)."""
        self._set_custom_cursor("#FF0000")

    def set_transcribing(self):
        """Change cursor to show yellow circle (transcribing)."""
        self._set_custom_cursor("#FFD700")

    def set_idle(self):
        """Restore normal cursor."""
        if self._active:
            # Restore all system cursors to defaults
            user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)
            self._active = False
            _force_cursor_refresh()
            self._cleanup_files()

    def _set_custom_cursor(self, color):
        cur_path = _create_cursor_file(color)
        self._cursor_files.append(cur_path)
        handle = _load_cursor_from_file(cur_path)
        if handle:
            # CopyIcon so the handle survives SetSystemCursor (which destroys the input)
            copy = user32.CopyIcon(handle)
            user32.SetSystemCursor(copy, OCR_NORMAL)
            self._active = True
            _force_cursor_refresh()

    def _cleanup_files(self):
        for f in self._cursor_files:
            try:
                os.remove(f)
            except OSError:
                pass
        self._cursor_files = []
