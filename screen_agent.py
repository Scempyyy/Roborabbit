import os
import uuid
import shutil
import pytesseract
from PIL import Image
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


class ScreenAgent:
    def __init__(self):
        self.screenshot_dir = os.path.expanduser(
            "~/roborabbit/screenshots"
        )

        os.makedirs(
            self.screenshot_dir,
            exist_ok=True
        )

        self.last_screenshot = os.path.join(
            self.screenshot_dir,
            "screen.png"
        )

    def capture(self):
        """
        Capture the GNOME Wayland screen using
        the XDG Desktop Portal Screenshot API.
        """

        bus = Gio.bus_get_sync(
            Gio.BusType.SESSION,
            None
        )

        token = (
            "roborabbit_"
            + uuid.uuid4().hex[:12]
        )

        options = {
            "handle_token": GLib.Variant(
                "s",
                token
            ),
            "interactive": GLib.Variant(
                "b",
                True
            ),
            "modal": GLib.Variant(
                "b",
                True
            ),
        }

        result = bus.call_sync(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            "Screenshot",
            GLib.Variant(
                "(sa{sv})",
                (
                    "wayland:",
                    options
                )
            ),
            GLib.VariantType("(o)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

        request_path = result.unpack()[0]

        loop = GLib.MainLoop()

        response_data = {}

        def on_response(
            connection,
            sender_name,
            object_path,
            interface_name,
            signal_name,
            parameters,
        ):
            if object_path != request_path:
                return

            response, results = parameters.unpack()

            response_data["response"] = response
            response_data["results"] = results

            loop.quit()

        subscription = bus.signal_subscribe(
            "org.freedesktop.portal.Desktop",
            "org.freedesktop.portal.Request",
            "Response",
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response,
        )

        try:
            loop.run()
        finally:
            bus.signal_unsubscribe(
                subscription
            )

        if response_data.get("response") != 0:
            raise RuntimeError(
                "Screenshot request failed: "
                f"{response_data.get('response')}"
            )

        results = response_data["results"]

        uri = results.get("uri")

        if uri is None:
            raise RuntimeError(
                "Screenshot succeeded but "
                f"no URI was returned: {results}"
            )

        source = Gio.File.new_for_uri(uri)

        destination = Gio.File.new_for_path(
            self.last_screenshot
        )

        source.copy(
            destination,
            Gio.FileCopyFlags.OVERWRITE,
            None,
            None,
        )

        return self.last_screenshot

    def read_screen(self):
        """
        Capture the screen and run OCR.
        """

        screenshot = self.capture()

        try:
            image = Image.open(
                screenshot
            )

            text = pytesseract.image_to_string(
                image
            )

            text = text.strip()

            if not text:
                return (
                    "I captured the screen, "
                    "but couldn't detect readable text."
                )

            return text

        except Exception as e:
            return (
                f"Screen OCR failed: {e}"
            )

    def screenshot(self):
        """
        Capture the screen and return the
        screenshot path.
        """

        return self.capture()

    def info(self):
        """
        Return basic information about the
        latest screenshot.
        """

        if not os.path.exists(
            self.last_screenshot
        ):
            return {
                "exists": False,
                "path": self.last_screenshot,
            }

        image = Image.open(
            self.last_screenshot
        )

        return {
            "exists": True,
            "path": self.last_screenshot,
            "width": image.width,
            "height": image.height,
        }


if __name__ == "__main__":

    print("\n🐇 RoboRabbit Screen Agent Test\n")

    agent = ScreenAgent()

    print("📸 Capturing screen...")

    try:
        path = agent.capture()

        print("\n🎉 Capture successful!")
        print(f"📁 {path}")

        print("\n👁️ Running OCR...")

        text = agent.read_screen()

        print("\n========== SCREEN TEXT ==========\n")
        print(text)
        print("\n=================================\n")

        info = agent.info()

        print("📐 Screen information:")
        print(info)

    except Exception as e:
        print("\n❌ Screen Agent failed:")
        print(repr(e))
