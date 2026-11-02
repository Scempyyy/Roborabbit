import os
import shutil
import subprocess
import time


class ComputerAgent:
    """
    RoboRabbit Computer Control

    Provides basic keyboard/mouse control.
    Designed to work with ydotool on Linux/Wayland.

    Supported:
        - type text
        - press keys
        - mouse move
        - left/right click
        - double click
        - scroll
    """

    def __init__(self):
        self.wayland = os.environ.get("XDG_SESSION_TYPE") == "wayland"
        self.ydotool = shutil.which("ydotool")

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def status(self):
        return {
            "wayland": self.wayland,
            "ydotool": self.ydotool is not None,
            "ready": self.ydotool is not None,
        }

    def _check(self):
        if not self.ydotool:
            return (
                False,
                "ydotool is not installed. Install it with: "
                "sudo pacman -S ydotool"
            )

        return True, ""

    # ---------------------------------------------------------
    # KEYBOARD
    # ---------------------------------------------------------

    def type_text(self, text):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        try:
            # ydotool type handles ordinary text
            subprocess.run(
                [
                    self.ydotool,
                    "type",
                    "--",
                    text
                ],
                check=True,
                timeout=15
            )

            return {
                "success": True,
                "action": "type",
                "text": text
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def press_key(self, key):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        keymap = {
            "enter": "28",
            "return": "28",
            "esc": "1",
            "escape": "1",
            "tab": "15",
            "space": "57",
            "backspace": "14",
            "delete": "111",

            "up": "103",
            "down": "108",
            "left": "105",
            "right": "106",

            "home": "102",
            "end": "107",
            "pageup": "104",
            "pagedown": "109",

            "ctrl": "29",
            "shift": "42",
            "alt": "56",
            "super": "125",

            "f1": "59",
            "f2": "60",
            "f3": "61",
            "f4": "62",
            "f5": "63",
            "f6": "64",
            "f7": "65",
            "f8": "66",
            "f9": "67",
            "f10": "68",
            "f11": "87",
            "f12": "88",
        }

        normalized = key.lower().strip()

        try:
            if normalized in keymap:
                code = keymap[normalized]

                subprocess.run(
                    [
                        self.ydotool,
                        "key",
                        f"{code}:1",
                        f"{code}:0"
                    ],
                    check=True,
                    timeout=5
                )

            elif len(normalized) == 1:
                # Linux input keycodes for common letters/numbers
                char_codes = {
                    "a": 30,
                    "b": 48,
                    "c": 46,
                    "d": 32,
                    "e": 18,
                    "f": 33,
                    "g": 34,
                    "h": 35,
                    "i": 23,
                    "j": 36,
                    "k": 37,
                    "l": 38,
                    "m": 50,
                    "n": 49,
                    "o": 24,
                    "p": 25,
                    "q": 16,
                    "r": 19,
                    "s": 31,
                    "t": 20,
                    "u": 22,
                    "v": 47,
                    "w": 17,
                    "x": 45,
                    "y": 21,
                    "z": 44,

                    "0": 11,
                    "1": 2,
                    "2": 3,
                    "3": 4,
                    "4": 5,
                    "5": 6,
                    "6": 7,
                    "7": 8,
                    "8": 9,
                    "9": 10,
                }

                if normalized not in char_codes:
                    return {
                        "success": False,
                        "error": f"Unsupported key: {key}"
                    }

                code = char_codes[normalized]

                subprocess.run(
                    [
                        self.ydotool,
                        "key",
                        f"{code}:1",
                        f"{code}:0"
                    ],
                    check=True,
                    timeout=5
                )

            else:
                return {
                    "success": False,
                    "error": f"Unsupported key: {key}"
                }

            return {
                "success": True,
                "action": "press_key",
                "key": key
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------
    # KEY COMBINATIONS
    # ---------------------------------------------------------

    def hotkey(self, *keys):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        keymap = {
            "ctrl": 29,
            "shift": 42,
            "alt": 56,
            "super": 125,

            "a": 30,
            "c": 46,
            "v": 47,
            "x": 45,
            "z": 44,
            "s": 31,
            "w": 17,
            "t": 20,
            "l": 38,
            "r": 19,
            "f": 33,
            "q": 16,
        }

        codes = []

        for key in keys:
            key = key.lower().strip()

            if key not in keymap:
                return {
                    "success": False,
                    "error": f"Unsupported hotkey key: {key}"
                }

            codes.append(keymap[key])

        try:
            args = [self.ydotool, "key"]

            # press
            for code in codes:
                args.append(f"{code}:1")

            # release reverse order
            for code in reversed(codes):
                args.append(f"{code}:0")

            subprocess.run(
                args,
                check=True,
                timeout=5
            )

            return {
                "success": True,
                "action": "hotkey",
                "keys": list(keys)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ---------------------------------------------------------
    # MOUSE
    # ---------------------------------------------------------

    def move_mouse(self, x, y):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        try:
            # ydotool mousemove uses relative movement.
            # Get current position isn't universally available,
            # so this method uses absolute positioning when
            # supported by the installed version.

            result = subprocess.run(
                [
                    self.ydotool,
                    "mousemove",
                    "--absolute",
                    "-x",
                    str(int(x)),
                    "-y",
                    str(int(y))
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Mouse move failed"
                }

            return {
                "success": True,
                "action": "move_mouse",
                "x": int(x),
                "y": int(y)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def click(self, button="left"):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        buttons = {
            "left": "0xC0",
            "right": "0xC1",
            "middle": "0xC2",
        }

        button = button.lower()

        if button not in buttons:
            return {
                "success": False,
                "error": f"Unsupported mouse button: {button}"
            }

        try:
            subprocess.run(
                [
                    self.ydotool,
                    "click",
                    buttons[button]
                ],
                check=True,
                timeout=5
            )

            return {
                "success": True,
                "action": "click",
                "button": button
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def double_click(self):
        first = self.click("left")

        if not first["success"]:
            return first

        time.sleep(0.08)

        second = self.click("left")

        if not second["success"]:
            return second

        return {
            "success": True,
            "action": "double_click"
        }

    # ---------------------------------------------------------
    # SCROLL
    # ---------------------------------------------------------

    def scroll(self, amount):
        ok, error = self._check()

        if not ok:
            return {
                "success": False,
                "error": error
            }

        try:
            # Positive = up
            # Negative = down

            clicks = int(amount)

            subprocess.run(
                [
                    self.ydotool,
                    "click",
                    "0x00000000"
                ],
                check=False,
                timeout=5
            )

            # ydotool supports wheel events using click codes
            wheel_code = "0x00B0" if clicks > 0 else "0x00BF"

            for _ in range(abs(clicks)):
                subprocess.run(
                    [
                        self.ydotool,
                        "click",
                        wheel_code
                    ],
                    check=True,
                    timeout=5
                )

            return {
                "success": True,
                "action": "scroll",
                "amount": clicks
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# ---------------------------------------------------------
# STANDALONE TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    agent = ComputerAgent()

    print("===================================")
    print(" RoboRabbit Computer Agent")
    print("===================================")

    print("\nStatus:")
    print(agent.status())

    if not agent.status()["ready"]:
        print("\nComputer control is not ready.")
        print("Install ydotool first:")
        print("sudo pacman -S ydotool")
        raise SystemExit(1)

    print("\nTesting keyboard...")

    result = agent.type_text("RoboRabbit computer control test")

    print(result)

    print("\nPressing Enter in 2 seconds...")
    time.sleep(2)

    print(agent.press_key("enter"))

    print("\nComputer agent test complete.")
