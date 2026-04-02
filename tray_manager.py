from __future__ import annotations

from typing import Callable

from PIL import Image, ImageDraw

try:
    import pystray
except ImportError:
    pystray = None


class TrayManager:
    """System tray controller with graceful fallback when pystray is unavailable."""

    def __init__(
        self,
        title: str,
        on_show: Callable[[], None],
        on_toggle_session: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self._title = title
        self._on_show = on_show
        self._on_toggle_session = on_toggle_session
        self._on_exit = on_exit
        self._icon = None
        self._is_running = False

    @property
    def available(self) -> bool:
        return pystray is not None

    def start(self) -> None:
        if not self.available or self._icon is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Відкрити", self._handle_show),
            pystray.MenuItem(lambda _: "Зупинити моніторинг" if self._is_running else "Почати моніторинг", self._handle_toggle),
            pystray.MenuItem("Вийти", self._handle_exit),
        )

        self._icon = pystray.Icon(
            name="kpi_focus_assistant",
            title=self._title,
            icon=self._create_icon(),
            menu=menu,
        )
        self._icon.run_detached()

    def stop(self) -> None:
        if self._icon is None:
            return
        self._icon.stop()
        self._icon = None

    def update_session_state(self, is_running: bool) -> None:
        self._is_running = is_running
        if self._icon is not None:
            self._icon.update_menu()

    def notify(self, title: str, message: str) -> None:
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass

    @staticmethod
    def _create_icon() -> Image.Image:
        image = Image.new("RGB", (64, 64), color=(24, 24, 24))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(40, 167, 69), outline=(220, 220, 220), width=2)
        draw.rectangle((30, 18, 34, 46), fill=(255, 255, 255))
        draw.rectangle((22, 30, 42, 34), fill=(255, 255, 255))
        return image

    def _handle_show(self, _icon, _item) -> None:
        self._on_show()

    def _handle_toggle(self, _icon, _item) -> None:
        self._on_toggle_session()

    def _handle_exit(self, _icon, _item) -> None:
        self._on_exit()
