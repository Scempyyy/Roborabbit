import os
import sys
import time
import traceback


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.expanduser("~/roborabbit")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# IMPORTS
# ============================================================

from task_agent import TaskAgent
from verified_executor import VerifiedExecutor


# ============================================================
# SMART RECOVERY
# ============================================================

class SmartRecovery:

    def __init__(self):

        self.task_agent = TaskAgent()
        self.executor = VerifiedExecutor()

        print("🧠 Smart Recovery initialized")

    # ========================================================
    # RECOVERY STRATEGIES
    # ========================================================

    def get_strategies(self, step):

        action = step.action

        strategies = []

        # ----------------------------------------------------
        # GOOGLE SEARCH
        # ----------------------------------------------------

        if action == "browser_google_search":

            strategies = [
                "retry",
                "direct_url"
            ]

        # ----------------------------------------------------
        # YOUTUBE SEARCH
        # ----------------------------------------------------

        elif action == "browser_youtube_search":

            strategies = [
                "direct_url",
                "retry"
            ]

        # ----------------------------------------------------
        # OPEN WEBSITE
        # ----------------------------------------------------

        elif action == "browser_open":

            strategies = [
                "retry"
            ]

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------

        elif action in (
            "browser_back",
            "browser_forward",
            "browser_refresh"
        ):

            strategies = [
                "retry",
                "reconnect"
            ]

        # ----------------------------------------------------
        # COMPUTER CONTROL
        # ----------------------------------------------------

        elif action in (
            "type",
            "press",
            "click",
            "double_click",
            "scroll"
        ):

            strategies = [
                "retry"
            ]

        else:

            strategies = [
                "retry"
            ]

        return strategies

    # ========================================================
    # DIRECT URL RECOVERY
    # ========================================================

    def direct_url_recovery(self, step):

        browser = self.executor.get_browser()

        action = step.action

        # ----------------------------------------------------
        # YOUTUBE
        # ----------------------------------------------------

        if action == "browser_youtube_search":

            from urllib.parse import quote_plus

            query = quote_plus(
                step.target
            )

            url = (
                "https://www.youtube.com/results"
                "?search_query="
                + query
            )

            print(
                f"🔗 Recovery URL: {url}"
            )

            browser.open(url)

            time.sleep(2)

            current_url = browser.get_url()

            if "search_query=" in current_url:

                return True

            return False

        # ----------------------------------------------------
        # GOOGLE
        # ----------------------------------------------------

        if action == "browser_google_search":

            from urllib.parse import quote_plus

            query = quote_plus(
                step.target
            )

            url = (
                "https://www.google.com/search"
                "?q="
                + query
            )

            print(
                f"🔗 Recovery URL: {url}"
            )

            browser.open(url)

            time.sleep(2)

            current_url = browser.get_url()

            if "google." in current_url:

                return True

            return False

        return False

    # ========================================================
    # RECONNECT
    # ========================================================

    def reconnect(self):

        print(
            "🔄 Reconnecting browser..."
        )

        try:

            browser = self.executor.get_browser()

            browser.ensure_connection()

            return True

        except Exception as e:

            print(
                f"❌ Reconnect failed: {e}"
            )

            return False

    # ========================================================
    # EXECUTE RECOVERY
    # ========================================================

    def recover(self, step):

        strategies = self.get_strategies(
            step
        )

        print("")
        print(
            f"🛠️ Recovery strategies: "
            f"{strategies}"
        )

        for strategy in strategies:

            print("")
            print(
                f"🔧 Trying recovery: "
                f"{strategy}"
            )

            try:

                # ------------------------------------------------
                # RETRY
                # ------------------------------------------------

                if strategy == "retry":

                    result = (
                        self.executor.execute_verified_step(
                            step
                        )
                    )

                    if result["success"]:

                        print(
                            "✅ Retry recovery succeeded"
                        )

                        return result

                # ------------------------------------------------
                # DIRECT URL
                # ------------------------------------------------

                elif strategy == "direct_url":

                    success = (
                        self.direct_url_recovery(
                            step
                        )
                    )

                    if success:

                        print(
                            "✅ Direct URL recovery "
                            "succeeded"
                        )

                        return {
                            "success": True,
                            "verified": True,
                            "attempts": 1,
                            "recovery": "direct_url",
                            "result": (
                                "Recovered using "
                                "direct URL"
                            )
                        }

                # ------------------------------------------------
                # RECONNECT
                # ------------------------------------------------

                elif strategy == "reconnect":

                    success = self.reconnect()

                    if success:

                        result = (
                            self.executor
                            .execute_verified_step(
                                step
                            )
                        )

                        if result["success"]:

                            result["recovery"] = (
                                "reconnect"
                            )

                            return result

            except Exception as e:

                print(
                    f"⚠️ Recovery strategy "
                    f"failed: {e}"
                )

                traceback.print_exc()

        # ====================================================
        # TOTAL FAILURE
        # ====================================================

        print("")
        print(
            "❌ All recovery strategies failed"
        )

        return {
            "success": False,
            "verified": False,
            "attempts": 0,
            "recovery": "failed",
            "result": (
                f"Could not recover action: "
                f"{step.action}"
            )
        }

    # ========================================================
    # SMART COMMAND
    # ========================================================

    def execute_command(self, command):

        print("")
        print("=" * 60)
        print(
            f"🎯 SMART COMMAND: {command}"
        )
        print("=" * 60)

        plan = self.task_agent.plan(
            command
        )

        results = []

        for index, step in enumerate(
            plan.steps,
            start=1
        ):

            print("")
            print(
                f"▶ STEP {index}/{len(plan.steps)}"
            )

            # First normal verified execution.

            result = (
                self.executor.execute_verified_step(
                    step
                )
            )

            # If normal execution fails,
            # activate intelligent recovery.

            if not result["success"]:

                print("")
                print(
                    "🧠 Normal execution failed."
                )

                print(
                    "🚑 Activating smart recovery..."
                )

                result = self.recover(
                    step
                )

            result["step"] = index

            result["action"] = (
                step.action
            )

            results.append(
                result
            )

            # Stop if recovery also failed.

            if not result["success"]:

                print("")
                print(
                    "🛑 Task stopped."
                )

                break

            print(
                "✅ Step completed successfully"
            )

        print("")
        print("=" * 60)

        completed = sum(
            1
            for result in results
            if result["success"]
        )

        print(
            f"📊 Final result: "
            f"{completed}/{len(plan.steps)}"
        )

        return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    agent = SmartRecovery()

    tests = [

        "search Minecraft tutorials on YouTube",

        "search Python tutorials",

    ]

    for command in tests:

        try:

            results = (
                agent.execute_command(
                    command
                )
            )

            print("")
            print("RESULT:")

            for result in results:

                print(result)

        except Exception as e:

            print(
                f"❌ Fatal error: {e}"
            )

            traceback.print_exc()
