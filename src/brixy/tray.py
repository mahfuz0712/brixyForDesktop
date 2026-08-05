from __future__ import annotations
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

if TYPE_CHECKING:
    # pystray.Icon is dynamically assigned from a platform backend at runtime
    # (Icon = backend().Icon), so Pylance sees it as a variable, not a class,
    # and rejects it in type annotations. pystray._base.Icon is the real
    # static base class every backend's Icon subclasses from — safe to use
    # for typing only. At runtime we still use the actual pystray.Icon above.
    from pystray._base import Icon as IconType
else:
    IconType = Icon

from brixy.logging_utils import get_logger

log = get_logger()


def _make_icon_image(color: str = "#4F8EF7") -> Image.Image:
    """Simple generated 'B' badge icon — parer step e real .ico file
    diye replace kora jabe, ekhon kono external asset lage na."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, size - 2, size - 2), fill=color)
    draw.text((size / 2 - 8, size / 2 - 12), "B", fill="white")
    return img


class TrayApp:
    def __init__(self, on_exit: Callable[[], None]):
        self._on_exit = on_exit
        self._status_text = "Brixy — listening"
        self._icon: IconType | None = None

    def _build_menu(self) -> Menu:
        return Menu(
            MenuItem(lambda item: self._status_text, None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Exit", self._handle_exit),
        )

    def _handle_exit(self, icon: IconType, item: MenuItem) -> None:  # noqa: ARG002
        log.info("Exit requested from tray menu")
        self._on_exit()
        icon.stop()

    def set_status(self, text: str) -> None:
        self._status_text = text
        if self._icon is not None:
            self._icon.update_menu()

    def run_blocking(self) -> None:
        """Ei call blocking — tai eta always main thread e call korte hobe.
        (Windows tray/GUI toolkit gulor eita common requirement.)"""
        self._icon = Icon("Brixy", _make_icon_image(), "Brixy", self._build_menu())
        self._icon.run()

    def run_in_thread(self) -> threading.Thread:
        t = threading.Thread(target=self.run_blocking, daemon=True, name="brixy-tray")
        t.start()
        return t