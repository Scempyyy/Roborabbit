import subprocess


ALLOWED_APPS = {
    "firefox": ["firefox"],
    "spotify": ["spotify"],
    "terminal": ["kgx"],
    "files": ["nautilus"],
}


def open_app(app_name: str):
    app_name = app_name.lower().strip()

    if app_name not in ALLOWED_APPS:
        return f"I can't open '{app_name}'. It isn't an approved application."

    try:
        subprocess.Popen(
            ALLOWED_APPS[app_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return f"Opened {app_name}."

    except FileNotFoundError:
        return f"{app_name} is not installed or could not be found."
