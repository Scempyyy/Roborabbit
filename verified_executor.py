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
from action_executor import ActionExecutor


# ============================================================
# VERIFIED EXECUTOR
# ============================================================

class VerifiedExecutor:

    def __init__(self):

        self.task_agent = TaskAgent()
        self.executor = ActionExecutor()

        self.max_retries = 2

        print("🔍 Verified Executor initialized")

    # ========================================================
    # GET BROWSER
    # ========================================================

    def get_browser(self):

        return self.executor.get_browser()

    # ========================================================
    # VERIFY GOOGLE SEARCH
    # ========================================================

    def verify_google_search(self, query):

        browser = self.get_browser()

        try:

            url = browser.get_url()
            title = browser.get_title()

            print(f"🔎 URL: {url}")
            print(f"📄 Title: {title}")

            query_words = query.lower().split()
            url_lower = url.lower()

            matched = sum(
                1
                for word in query_words
                if word in url_lower
            )

            if "google." in url_lower and matched >= 1:
                return True

            try:

                text = browser.get_visible_text()
                text_lower = text.lower()

                matched = sum(
                    1
                    for word in query_words
                    if word in text_lower
                )

                if matched >= max(
                    1,
                    len(query_words) // 2
                ):
                    return True

            except Exception:
                pass

        except Exception as e:

            print(
                f"⚠️ Google verification error: {e}"
            )

        return False

    # ========================================================
    # VERIFY YOUTUBE SEARCH
    # ========================================================

    def verify_youtube_search(self, query):

        browser = self.get_browser()

        try:

            url = browser.get_url()
            title = browser.get_title()

            print(f"🔎 URL: {url}")
            print(f"📄 Title: {title}")

            url_lower = url.lower()

            if "youtube.com" not in url_lower:
                return False

            if "search_query=" in url_lower:
                return True

            try:

                text = browser.get_visible_text()
                query_words = query.lower().split()

                matched = sum(
                    1
                    for word in query_words
                    if word in text.lower()
                )

                if matched >= max(
                    1,
                    len(query_words) // 2
                ):
                    return True

            except Exception:
                pass

        except Exception as e:

            print(
                f"⚠️ YouTube verification error: {e}"
            )

        return False

    # ========================================================
    # VERIFY OPEN WEBSITE
    # ========================================================

    def verify_open(self, target):

        browser = self.get_browser()

        try:

            current_url = browser.get_url()

            print(
                f"🔎 Current URL: {current_url}"
            )

            target_clean = target.lower()
            current_clean = current_url.lower()

            target_clean = (
                target_clean
                .replace("https://", "")
                .replace("http://", "")
            )

            if target_clean.rstrip("/") in current_clean:
                return True

            target_domain = target_clean.split("/")[0]

            if target_domain in current_clean:
                return True

        except Exception as e:

            print(
                f"⚠️ Open verification error: {e}"
            )

        return False

    # ========================================================
    # VERIFY YOUTUBE VIDEO
    # ========================================================

    def verify_youtube_video(self):

        browser = self.get_browser()

        try:

            url = browser.get_url()

            print(
                f"🔎 Video URL: {url}"
            )

            url_lower = url.lower()

            # Normal YouTube video URL
            if "youtube.com/watch" in url_lower:
                return True

            # YouTube Shorts
            if "youtube.com/shorts/" in url_lower:
                return True

            return False

        except Exception as e:

            print(
                f"⚠️ YouTube video verification error: {e}"
            )

            return False

    # ========================================================
    # VERIFY GOOGLE RESULT
    # ========================================================

    def verify_google_result(self):

        browser = self.get_browser()

        try:

            url = browser.get_url()

            print(
                f"🔎 Google result URL: {url}"
            )

            url_lower = url.lower()

            # If we are no longer on Google search,
            # the result was probably opened.
            if "google." not in url_lower:
                return True

            # Some Google result redirects can still contain
            # Google in the URL, so inspect the page title too.
            title = browser.get_title()

            if title and "search" not in title.lower():
                return True

        except Exception as e:

            print(
                f"⚠️ Google result verification error: {e}"
            )

        return False

    # ========================================================
    # VERIFY BROWSER ACTION
    # ========================================================

    def verify_browser_action(self, step):

        action = step.action

        print("")
        print(
            f"🔍 Verifying {action}..."
        )

        # Firefox launch
        if action == "get_time":
            try:
                result = self.executor.execute_step(step)
                return bool(
                    result
                    and result.get("success") is True
                    and result.get("result")
                )
            except Exception:
                return False

        if action == "browser_launch":

            try:
                browser = self.get_browser()
                url = browser.get_url()

                return bool(url)

            except Exception:
                return False

        # Firefox close
        if action == "browser_close":

            # ActionExecutor clears self.browser after closing.
            # A missing browser object therefore confirms closure.
            return self.executor.browser is None

        # Google search
        if action == "browser_google_search":

            return self.verify_google_search(
                step.target
            )

        # YouTube search
        if action == "browser_youtube_search":

            return self.verify_youtube_search(
                step.target
            )

        # Open website
        if action == "browser_open":

            return self.verify_open(
                step.target
            )

        # First YouTube video
        if action == "browser_click_first_youtube":

            return self.verify_youtube_video()

        # First Google result
        if action == "browser_click_first_google":

            return self.verify_google_result()

        # Navigation actions
        if action in (
            "browser_back",
            "browser_forward",
            "browser_refresh"
        ):

            try:

                browser = self.get_browser()
                url = browser.get_url()

                return bool(url)

            except Exception:

                return False

        # Browser typing/clicking
        if action in (
            "browser_type",
            "browser_press",
            "browser_click",
            "browser_scroll_down",
            "browser_scroll_up"
        ):

            return True

        # Computer actions
        if action in (
            "type",
            "press",
            "click",
            "double_click",
            "scroll"
        ):

            return True

        return False

    # ========================================================
    # EXECUTE + VERIFY ONE STEP
    # ========================================================

    def execute_verified_step(self, step):

        for attempt in range(
            1,
            self.max_retries + 2
        ):

            print("")

            print(
                f"⚡ Attempt {attempt}: "
                f"{step.description or step.action}"
            )

            try:

                # IMPORTANT:
                # ActionExecutor uses execute_step(),
                # not execute_action().
                result = self.executor.execute_step(
                    step
                )

                # Give browser time to update.
                time.sleep(1)

                # Verify result.
                verified = self.verify_browser_action(
                    step
                )

                if verified:

                    print(
                        "✅ VERIFIED"
                    )

                    return {
                        "success": True,
                        "verified": True,
                        "attempts": attempt,
                        "result": result
                    }

                print(
                    "❌ Verification failed"
                )

            except Exception as e:

                print(
                    f"❌ Execution failed: {e}"
                )

                if attempt >= self.max_retries + 1:

                    return {
                        "success": False,
                        "verified": False,
                        "attempts": attempt,
                        "result": str(e)
                    }

            # =================================================
            # RETRY
            # =================================================

            if attempt <= self.max_retries:

                print(
                    f"🔄 Retrying "
                    f"({attempt}/{self.max_retries})..."
                )

                time.sleep(1)

        return {
            "success": False,
            "verified": False,
            "attempts": self.max_retries + 1,
            "result": "Verification failed"
        }

    # ========================================================
    # EXECUTE VERIFIED PLAN
    # ========================================================

    def execute_plan(self, plan):

        results = []

        print("")
        print(
            "🤖 RoboRabbit Verified Executor"
        )
        print("=" * 55)

        print(
            f"🎯 Goal: {plan.goal}"
        )

        for index, step in enumerate(
            plan.steps,
            start=1
        ):

            print("")
            print(
                f"▶ STEP {index}/{len(plan.steps)}"
            )

            result = self.execute_verified_step(
                step
            )

            result["step"] = index
            result["action"] = step.action

            results.append(result)

            if not result["success"]:

                print("")
                print(
                    "🛑 Task stopped because "
                    "the step could not be verified."
                )

                break

            print(
                "✅ Step completed"
            )

        print("")
        print("=" * 55)

        completed = sum(
            1
            for result in results
            if result["success"]
        )

        total = len(plan.steps)

        if completed == total:

            print(
                f"🎉 TASK VERIFIED: "
                f"{completed}/{total}"
            )

        else:

            print(
                f"⚠️ TASK PARTIAL: "
                f"{completed}/{total}"
            )

        return results

    # ========================================================
    # NATURAL COMMAND
    # ========================================================

    def execute_command(self, command):

        print("")
        print(
            "🧠 Understanding command..."
        )

        plan = self.task_agent.plan(
            command
        )

        print(
            f"📋 Planned {len(plan.steps)} step(s)"
        )

        return self.execute_plan(
            plan
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    agent = VerifiedExecutor()

    command = (
        "search Minecraft tutorials on YouTube "
        "and open the first video"
    )

    try:

        results = agent.execute_command(
            command
        )

        print("")
        print("RESULT:")

        for result in results:
            print(result)

        print("")
        print(
            "🦊 Firefox will remain open."
        )

        input(
            "🐇 Press Enter to close Firefox..."
        )

    except KeyboardInterrupt:

        print(
            "\n🐇 RoboRabbit stopped."
        )

    except Exception as e:

        print(
            f"\n❌ Fatal error: {e}"
        )

        traceback.print_exc()

    finally:

        try:
            agent.executor.close()
        except Exception:
            pass
