import time

from task_agent import TaskAgent
from firefox_agent import FirefoxAgent
from computer_agent import ComputerAgent


class ActionExecutor:
    def __init__(self):
        self.task_agent = TaskAgent()
        self.browser = None
        self.computer = None

    # -------------------------
    # Browser
    # -------------------------

    def get_browser(self):
        if self.browser is None:
            self.browser = FirefoxAgent()
        else:
            try:
                self.browser.ensure_connection()
            except Exception:
                self.browser = FirefoxAgent()

        return self.browser

    # -------------------------
    # Computer
    # -------------------------

    def get_computer(self):
        if self.computer is None:
            self.computer = ComputerAgent()

        return self.computer

    # -------------------------
    # Execute single action
    # -------------------------

    def execute_step(self, step):
        action = step.action
        target = step.target
        value = step.value

        try:

            # =========================
            # Local system actions
            # =========================

            if action == "get_time":
                from datetime import datetime

                current_time = datetime.now().strftime("%I:%M %p")

                return {
                    "success": True,
                    "result": current_time,
                }

            # =========================
            # Desktop application actions
            # =========================

            if action == "app_launch":
                import subprocess

                apps = {
                    "terminal": ["/usr/bin/kgx"],
                    "spotify": ["spotify"],
                    "files": ["nautilus"],
                }

                command = apps.get(target)

                if command is None:
                    return {
                        "success": False,
                        "result": f"Unknown application: {target}",
                    }

                try:
                    subprocess.Popen(
                        command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )

                    return {
                        "success": True,
                        "result": f"{target.title()} opened.",
                    }

                except FileNotFoundError:
                    return {
                        "success": False,
                        "result": f"{target.title()} is not installed or its command was not found.",
                    }

            elif action == "app_close":
                import subprocess

                processes = {
                    "terminal": ["/usr/bin/kgx"],
                    "spotify": ["spotify", "spotify-launcher"],
                    "files": ["nautilus"],
                }

                names = processes.get(target)

                if names is None:
                    return {
                        "success": False,
                        "result": f"Unknown application: {target}",
                    }

                closed = False

                for name in names:
                    result = subprocess.run(
                        ["pkill", "-TERM", "-x", name],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        closed = True

                if closed:
                    return {
                        "success": True,
                        "result": f"{target.title()} closed.",
                    }

                return {
                    "success": False,
                    "result": f"{target.title()} is not running.",
                }

            # =========================
            # Browser actions
            # =========================

            if action == "browser_launch":
                browser = self.get_browser()

                return {
                    "success": True,
                    "result": "Firefox is open.",
                }

            elif action == "browser_close":
                import subprocess

                try:
                    result = subprocess.run(
                        ["pkill", "-TERM", "-x", "firefox"],
                        capture_output=True,
                        text=True
                    )

                    self.browser = None

                    if result.returncode == 0:
                        return {
                            "success": True,
                            "result": "Firefox closed.",
                        }

                    return {
                        "success": False,
                        "result": "Firefox is not running.",
                    }

                except Exception as e:
                    return {
                        "success": False,
                        "result": f"Failed to close Firefox: {e}",
                    }

            elif action == "browser_google_search":
                browser = self.get_browser()
                result = browser.search_google(target)

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_search":
                browser = self.get_browser()

                result = browser.search_youtube(target)

                return {
                    "success": isinstance(result, str) and "failed" not in result.lower(),
                    "result": result,
                }

            elif action == "browser_youtube_search":
                browser = self.get_browser()
                result = browser.search_youtube(target)

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_click_first_google":
                browser = self.get_browser()
                result = browser.click_first_google_result()

                return {
                    "success": result is not None,
                    "result": result,
                }

            elif action == "browser_click_first_youtube":
                browser = self.get_browser()
                result = browser.click_first_youtube_result()

                return {
                    "success": result is not None,
                    "result": result,
                }

            elif action == "browser_result":
                browser = self.get_browser()

                if target == "first":
                    result = browser.click_first_youtube_result()
                elif target == "second":
                    # Fallback: second result is not currently implemented
                    return {
                        "success": False,
                        "result": "Second result selection is not implemented yet."
                    }
                else:
                    return {
                        "success": False,
                        "result": f"Unknown result position: {target}"
                    }

                return {
                    "success": result is not None,
                    "result": result,
                }

            elif action == "browser_open":
                browser = self.get_browser()
                result = browser.open(target)

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_back":
                browser = self.get_browser()
                result = browser.back()

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_forward":
                browser = self.get_browser()
                result = browser.forward()

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_refresh":
                browser = self.get_browser()
                result = browser.refresh()

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_type":
                browser = self.get_browser()
                result = browser.type_into(target, value)

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_press":
                browser = self.get_browser()
                result = browser.press_enter()

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_click":
                browser = self.get_browser()
                result = browser.click_text(target)

                return {
                    "success": result is not None,
                    "result": result,
                }

            elif action == "browser_scroll_down":
                browser = self.get_browser()
                result = browser.scroll_down()

                return {
                    "success": True,
                    "result": result,
                }

            elif action == "browser_scroll_up":
                browser = self.get_browser()
                result = browser.scroll_up()

                return {
                    "success": True,
                    "result": result,
                }

            # =========================
            # Computer actions
            # =========================

            elif action == "type":
                computer = self.get_computer()
                computer.type_text(value)

                return {
                    "success": True,
                    "result": f"Typed: {value}",
                }

            elif action == "press":
                computer = self.get_computer()
                computer.press(target)

                return {
                    "success": True,
                    "result": f"Pressed: {target}",
                }

            elif action == "click":
                computer = self.get_computer()

                if value:
                    x, y = int(value[0]), int(value[1])
                else:
                    x, y = int(target[0]), int(target[1])

                computer.click(x, y)

                return {
                    "success": True,
                    "result": f"Clicked at ({x}, {y})",
                }

            elif action == "double_click":
                computer = self.get_computer()

                if value:
                    x, y = int(value[0]), int(value[1])
                else:
                    x, y = int(target[0]), int(target[1])

                computer.double_click(x, y)

                return {
                    "success": True,
                    "result": f"Double-clicked at ({x}, {y})",
                }

            elif action == "scroll":
                computer = self.get_computer()

                amount = int(value) if value else 5
                computer.scroll(amount)

                return {
                    "success": True,
                    "result": f"Scrolled: {amount}",
                }

            else:
                return {
                    "success": False,
                    "result": f"Unknown action: {action}",
                }

        except Exception as e:
            return {
                "success": False,
                "result": str(e),
            }

    # -------------------------
    # Execute task
    # -------------------------

    def execute_plan(self, plan):
        results = []

        for index, step in enumerate(plan.steps, start=1):

            print(
                f"\n🐇 Step {index}/{len(plan.steps)}: "
                f"{step.description}"
            )

            result = self.execute_step(step)

            result["step"] = index
            result["action"] = step.action

            results.append(result)

            print(result)

            if not result["success"] and not step.optional:
                print(
                    f"❌ Required step {index} failed. "
                    f"Stopping task."
                )
                break

            time.sleep(0.5)

        return results

    # -------------------------
    # Execute natural language
    # -------------------------

    def execute_command(self, command):
        print(f"\n🧠 Command: {command}")

        plan = self.task_agent.plan(command)

        print(f"🎯 Goal: {plan.goal}")

        for index, step in enumerate(plan.steps, start=1):
            print(f"   {index}. {step.description}")

        return self.execute_plan(plan)

    # -------------------------
    # Keep browser alive
    # -------------------------

    def keep_browser_open(self):
        if self.browser is None:
            return

        print("\n🦊 Firefox is staying open.")
        print("🐇 Press Enter to close RoboRabbit Firefox.")

        try:
            input()
        except KeyboardInterrupt:
            print("\n🐇 Closing RoboRabbit...")

        try:
            self.browser.close()
        except Exception:
            pass

    # -------------------------
    # Close everything
    # -------------------------

    def close(self):
        # Keep RoboRabbit-controlled Firefox alive.
        # Browser is closed only through the explicit browser_close action.
        self.computer = None


# ==========================================
# Standalone test
# ==========================================

if __name__ == "__main__":

    executor = ActionExecutor()

    tests = [
        "search Minecraft tutorials on YouTube and open the first video",
    ]

    try:
        for command in tests:

            print("\n" + "=" * 60)
            print(f"🐇 Running: {command}")
            print("=" * 60)

            results = executor.execute_command(command)

            print("\n📋 Final results:")

            for result in results:
                print(result)

        # IMPORTANT:
        # Keep Python alive so Firefox does not disappear
        # immediately when the test finishes.
        executor.keep_browser_open()

    except KeyboardInterrupt:
        print("\n🐇 RoboRabbit stopped.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        executor.close()
