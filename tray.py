import threading
from PIL import Image, ImageDraw
import pystray


# Icon colors for each state
COLORS = {
    "idle": "#888888",       # grey
    "recording": "#FF0000",  # red
    "transcribing": "#FFD700",  # yellow
}


def _create_icon_image(color):
    """Generate a 64x64 microphone icon with the given color."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Microphone body (rounded rectangle approximation)
    draw.rounded_rectangle([20, 8, 44, 36], radius=8, fill=color)

    # Microphone stand arc
    draw.arc([16, 20, 48, 48], start=0, end=180, fill=color, width=3)

    # Stand line
    draw.line([32, 48, 32, 56], fill=color, width=3)

    # Base
    draw.line([24, 56, 40, 56], fill=color, width=3)

    return img


class TrayApp:
    def __init__(self, on_setup_check, on_quit):
        self._state = "idle"
        self._on_setup_check = on_setup_check
        self._on_quit = on_quit
        self._icon = None

    def set_state(self, state):
        """Update tray icon state: 'idle', 'recording', or 'transcribing'."""
        self._state = state
        if self._icon:
            self._icon.icon = _create_icon_image(COLORS[state])
            tooltips = {
                "idle": "Speech-to-Text — Ready (Ctrl+Space)",
                "recording": "Speech-to-Text — Recording...",
                "transcribing": "Speech-to-Text — Transcribing...",
            }
            self._icon.title = tooltips[state]

    def run(self):
        """Start the tray icon. Blocks the calling thread."""
        menu = pystray.Menu(
            pystray.MenuItem("Setup Check", lambda: self._on_setup_check()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self._on_quit()),
        )

        self._icon = pystray.Icon(
            name="speech-to-text",
            icon=_create_icon_image(COLORS["idle"]),
            title="Speech-to-Text — Ready (Ctrl+Space)",
            menu=menu,
        )
        self._icon.run()

    def stop(self):
        if self._icon:
            self._icon.stop()
