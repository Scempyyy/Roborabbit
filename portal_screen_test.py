import os
import uuid

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


DEST = os.path.expanduser(
    "~/jarvis/screenshots/portal_screen.png"
)


def main():
    print("\n🐇 RoboRabbit Wayland Screen Test\n")
    print("📸 Requesting GNOME screenshot...")
    print("🪟 Parent window: wayland:")

    os.makedirs(
        os.path.dirname(DEST),
        exist_ok=True
    )

    # Connect to the user's D-Bus session
    bus = Gio.bus_get_sync(
        Gio.BusType.SESSION,
        None
    )

    token = (
        "roborabbit_"
        + uuid.uuid4().hex[:12]
    )

    # Do NOT use target=1.
    # Your GNOME portal reported:
    # "Unavailable screenshot target 1"
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

    # Ask xdg-desktop-portal for a screenshot
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

    print(f"🔗 Request: {request_path}")
    print(
        "⏳ Waiting for GNOME screenshot "
        "permission/selection..."
    )

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
        # Ignore unrelated Request objects
        if object_path != request_path:
            return

        response, results = parameters.unpack()

        response_data["response"] = response
        response_data["results"] = results

        loop.quit()

    # Listen for the portal response
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

    # Portal response code:
    # 0 = success
    if response_data.get("response") != 0:
        raise RuntimeError(
            "Screenshot request failed: "
            f"{response_data.get('response')}"
        )

    results = response_data["results"]

    # IMPORTANT:
    # Gio already converted the URI into a Python string.
    uri = results.get("uri")

    if uri is None:
        raise RuntimeError(
            "Screenshot succeeded but no URI "
            f"was returned: {results}"
        )

    print(f"📍 Portal URI: {uri}")

    # Copy the portal screenshot to our normal path
    source = Gio.File.new_for_uri(uri)

    destination = Gio.File.new_for_path(
        DEST
    )

    source.copy(
        destination,
        Gio.FileCopyFlags.OVERWRITE,
        None,
        None,
    )

    print("\n🎉 SCREEN CAPTURE SUCCESS!")
    print(f"📸 Saved to: {DEST}")

    print("\nOpening screenshot...")

    os.system(
        f'xdg-open "{DEST}"'
    )


if __name__ == "__main__":
    main()
