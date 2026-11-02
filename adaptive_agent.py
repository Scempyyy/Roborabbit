import os
import sys
import time


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
from smart_recovery import SmartRecovery


# ============================================================
# ADAPTIVE AGENT
# ============================================================

class AdaptiveAgent:

    def __init__(self):

        print("🐇 Initializing Adaptive Agent...")

        self.planner = TaskAgent()
        self.executor = VerifiedExecutor()
        self.recovery = SmartRecovery()

        self.max_retries = 2

        print("🧠 Planner: READY")
        print("👀 Observation: READY")
        print("⚙️ Execution: READY")
        print("✅ Verification: READY")
        print("🔄 Recovery: READY")

    # ========================================================
    # OBSERVE
    # ========================================================

    def observe(self):

        state = {
            "browser_available": False,
            "url": "",
            "title": "",
            "page_text": "",
        }

        try:

            browser = self.executor.get_browser()

            if browser is None:
                return state

            state["browser_available"] = True

            try:
                state["url"] = browser.get_url()
            except Exception:
                pass

            try:
                state["title"] = browser.get_title()
            except Exception:
                pass

            try:
                state["page_text"] = (
                    browser.get_visible_text()[:3000]
                )
            except Exception:
                pass

        except Exception as e:

            print(
                f"⚠️ Observation error: {e}"
            )

        return state

    # ========================================================
    # DISPLAY STATE
    # ========================================================

    def show_state(self, state):

        print("\n👀 CURRENT STATE")
        print("-" * 55)

        print(
            f"Browser: "
            f"{'READY' if state['browser_available'] else 'OFF'}"
        )

        if state["url"]:
            print(
                f"🌐 URL: {state['url']}"
            )

        if state["title"]:
            print(
                f"📄 Title: {state['title']}"
            )

        if state["page_text"]:

            text = (
                state["page_text"]
                .replace("\n", " ")
                .strip()
            )

            if len(text) > 300:
                text = text[:300] + "..."

            print(
                f"📝 Page: {text}"
            )

        print("-" * 55)

    # ========================================================
    # CHECK WHETHER STEP ALREADY HAPPENED
    # ========================================================

    def step_already_completed(self, step, state):

        action = step.action

        url = state["url"].lower()

        # YouTube video already open
        if action == "browser_click_first_youtube":

            if "youtube.com/watch" in url:
                return True

            if "youtube.com/shorts/" in url:
                return True

        # Google result already opened
        if action == "browser_click_first_google":

            if "google." not in url:
                return True

        # Website already open
        if action == "browser_open":

            target = step.target.lower()

            target = (
                target
                .replace("https://", "")
                .replace("http://", "")
                .rstrip("/")
            )

            if target in url:
                return True

        return False

    # ========================================================
    # EXECUTE STEP
    # ========================================================

    def execute_step(self, step):

        print("\n⚙️ ACTION")
        print("-" * 55)

        print(
            f"🎯 {step.description}"
        )

        for attempt in range(
            1,
            self.max_retries + 2
        ):

            print(
                f"\n🔧 Attempt {attempt}"
            )

            result = (
                self.executor.execute_verified_step(
                    step
                )
            )

            if result.get("success"):

                print(
                    "✅ ACTION SUCCESSFUL"
                )

                return result

            print(
                "❌ Action failed."
            )

            if attempt <= self.max_retries:

                print(
                    "🔄 Preparing recovery..."
                )

                time.sleep(1)

        return {
            "success": False,
            "verified": False,
            "result": "Action failed after retries"
        }

    # ========================================================
    # RECOVER
    # ========================================================

    def recover(self, step):

        print("\n🔄 RECOVERY")
        print("-" * 55)

        try:

            result = self.recovery.recover(
                step
            )

            if isinstance(result, dict):

                if result.get("success"):

                    print(
                        "✅ Recovery successful"
                    )

                else:

                    print(
                        "❌ Recovery failed"
                    )

            return result

        except Exception as e:

            print(
                f"❌ Recovery error: {e}"
            )

            return {
                "success": False,
                "result": str(e)
            }

    # ========================================================
    # RUN ADAPTIVE TASK
    # ========================================================

    def run(self, command):

        print("\n" + "=" * 65)
        print("🐇 ROBORABBIT ADAPTIVE AGENT")
        print("=" * 65)

        print(
            f"💬 Goal: {command}"
        )

        # ----------------------------------------------------
        # PLAN
        # ----------------------------------------------------

        print("\n🧠 PLANNING...")

        plan = self.planner.plan(
            command
        )

        print(
            f"🎯 {plan.goal}"
        )

        print(
            f"📋 {len(plan.steps)} planned step(s)"
        )

        for index, step in enumerate(
            plan.steps,
            1
        ):

            print(
                f"   {index}. "
                f"{step.description}"
            )

        # ----------------------------------------------------
        # EXECUTION LOOP
        # ----------------------------------------------------

        results = []

        for index, step in enumerate(
            plan.steps,
            1
        ):

            print("\n")
            print("=" * 65)
            print(
                f"📍 STEP {index}/{len(plan.steps)}"
            )
            print("=" * 65)

            # ----------------------------------------------
            # OBSERVE BEFORE ACTION
            # ----------------------------------------------

            state_before = self.observe()

            self.show_state(
                state_before
            )

            # ----------------------------------------------
            # Avoid duplicate actions
            # ----------------------------------------------

            if self.step_already_completed(
                step,
                state_before
            ):

                print(
                    "⏭️ Step already completed."
                )

                result = {
                    "success": True,
                    "verified": True,
                    "skipped": True,
                    "result": (
                        "Step already completed"
                    )
                }

                results.append({
                    "step": index,
                    "action": step.action,
                    "success": True,
                    "result": result
                })

                continue

            # ----------------------------------------------
            # EXECUTE
            # ----------------------------------------------

            result = self.execute_step(
                step
            )

            # ----------------------------------------------
            # RECOVER
            # ----------------------------------------------

            if not result.get("success"):

                print(
                    "\n⚠️ Normal execution failed."
                )

                recovery_result = self.recover(
                    step
                )

                if recovery_result.get(
                    "success",
                    False
                ):

                    result = recovery_result

                else:

                    print(
                        "\n🛑 Could not complete step."
                    )

                    results.append({
                        "step": index,
                        "action": step.action,
                        "success": False,
                        "result": result
                    })

                    if getattr(
                        step,
                        "optional",
                        False
                    ):

                        print(
                            "⚠️ Optional step. "
                            "Continuing..."
                        )

                        continue

                    break

            # ----------------------------------------------
            # OBSERVE AFTER ACTION
            # ----------------------------------------------

            time.sleep(1)

            state_after = self.observe()

            self.show_state(
                state_after
            )

            results.append({
                "step": index,
                "action": step.action,
                "success": True,
                "result": result,
                "state_before": state_before,
                "state_after": state_after
            })

            print(
                f"✅ STEP {index} COMPLETE"
            )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        completed = sum(
            1
            for result in results
            if result["success"]
        )

        total = len(plan.steps)

        print("\n" + "=" * 65)
        print("📋 ADAPTIVE TASK SUMMARY")
        print("=" * 65)

        print(
            f"Completed: {completed}/{total}"
        )

        if completed == total:

            print(
                "🎉 ADAPTIVE TASK COMPLETE!"
            )

        else:

            print(
                "⚠️ Task partially completed."
            )

        print("=" * 65)

        return {
            "success": completed == total,
            "goal": plan.goal,
            "completed_steps": completed,
            "total_steps": total,
            "results": results
        }

    # ========================================================
    # KEEP FIREFOX OPEN
    # ========================================================

    def keep_browser_open(self):

        try:

            browser = self.executor.get_browser()

            if browser is None:
                return

            print(
                "\n🦊 Firefox is staying open."
            )

            input(
                "🐇 Press Enter to close Firefox..."
            )

            try:
                browser.close()
            except Exception:
                pass

        except Exception as e:

            print(
                f"⚠️ Browser close error: {e}"
            )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        try:

            self.executor.executor.close()

        except Exception:
            pass


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    agent = AdaptiveAgent()

    command = (
        "search Minecraft tutorials on YouTube "
        "and open the first video"
    )

    try:

        result = agent.run(
            command
        )

        print("\n🐇 FINAL RESULT:")
        print(result)

        agent.keep_browser_open()

    except KeyboardInterrupt:

        print(
            "\n🐇 Adaptive Agent stopped."
        )

    except Exception as e:

        print(
            f"\n❌ Fatal error: {e}"
        )

    finally:

        agent.close()
