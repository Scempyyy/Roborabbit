import os
import sys
import time
import json

from task_agent import TaskStep
from decision_engine import DecisionEngine
from verified_executor import VerifiedExecutor


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.expanduser("~/roborabbit")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# GEMINI ADAPTIVE AGENT
# ============================================================

class GeminiAgent:

    def __init__(self):

        print("🐇 Initializing Gemini Adaptive Agent...")

        self.engine = DecisionEngine()
        self.executor = VerifiedExecutor()

        self.max_steps = 8
        self.completed_steps = []

        print("🧠 Gemini Decision Engine: READY")
        print("⚙️ Verified Executor: READY")
        print("👀 Adaptive Loop: READY")

    # ========================================================
    # OBSERVE
    # ========================================================

    def observe(self):

        state = {
            "browser_available": False,
            "url": "",
            "title": "",
            "page_text": ""
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
                    browser.get_visible_text()[:5000]
                )
            except Exception:
                pass

        except Exception as e:

            print(
                f"⚠️ Observation failed: {e}"
            )

        return state

    # ========================================================
    # NORMALIZE GEMINI DECISION
    # ========================================================

    def normalize_decision(self, decision):

        action = decision.get(
            "action",
            "stop"
        )

        target = decision.get(
            "target",
            ""
        )

        value = decision.get(
            "value",
            ""
        )

        # Gemini sometimes puts search text
        # in value instead of target.
        if not target and value:

            if action in (
                "browser_google_search",
                "browser_youtube_search",
                "browser_open",
                "browser_click"
            ):

                target = value
                value = ""

        return {
            "action": action,
            "target": target,
            "value": value,
            "reason": decision.get(
                "reason",
                ""
            )
        }

    # ========================================================
    # CONVERT TO TASK STEP
    # ========================================================

    def decision_to_step(self, decision):

        return TaskStep(
            action=decision["action"],
            target=decision.get(
                "target",
                ""
            ),
            value=decision.get(
                "value",
                ""
            ),
            description=(
                decision.get(
                    "reason",
                    ""
                )
                or decision["action"]
            ),
            optional=False
        )

    # ========================================================
    # EXECUTE DECISION
    # ========================================================

    def execute_decision(self, decision):

        step = self.decision_to_step(
            decision
        )

        print("\n⚙️ EXECUTING GEMINI DECISION")
        print("-" * 55)

        print(
            f"Action: {step.action}"
        )

        print(
            f"Target: {step.target}"
        )

        print(
            f"Value: {step.value}"
        )

        result = (
            self.executor.execute_verified_step(
                step
            )
        )

        return result

    # ========================================================
    # RUN
    # ========================================================

    def run(self, goal):

        print("\n" + "=" * 70)
        print("🐇 ROBORABBIT — GEMINI ADAPTIVE MODE")
        print("=" * 70)

        print(
            f"🎯 Goal: {goal}"
        )

        self.completed_steps = []

        for cycle in range(
            1,
            self.max_steps + 1
        ):

            print("\n")
            print("=" * 70)

            print(
                f"🔄 ADAPTIVE CYCLE "
                f"{cycle}/{self.max_steps}"
            )

            print("=" * 70)

            # ------------------------------------------------
            # OBSERVE
            # ------------------------------------------------

            print("\n👀 OBSERVING...")

            state = self.observe()

            print(
                f"🌐 URL: {state['url']}"
            )

            print(
                f"📄 Title: {state['title']}"
            )

            # ------------------------------------------------
            # ASK GEMINI
            # ------------------------------------------------

            decision = self.engine.decide(
                goal=goal,
                state=state,
                completed_steps=self.completed_steps
            )

            decision = self.normalize_decision(
                decision
            )

            print("\n🤖 DECISION")

            print(
                json.dumps(
                    decision,
                    indent=2,
                    ensure_ascii=False
                )
            )

            action = decision["action"]

            # ------------------------------------------------
            # DONE
            # ------------------------------------------------

            if action == "done":

                print("\n🎉 GEMINI SAYS TASK IS COMPLETE!")

                return {
                    "success": True,
                    "goal": goal,
                    "cycles": cycle,
                    "completed_steps": (
                        self.completed_steps
                    )
                }

            # ------------------------------------------------
            # STOP
            # ------------------------------------------------

            if action == "stop":

                print(
                    "\n🛑 Gemini decided the task "
                    "cannot safely continue."
                )

                return {
                    "success": False,
                    "goal": goal,
                    "cycles": cycle,
                    "completed_steps": (
                        self.completed_steps
                    ),
                    "reason": decision.get(
                        "reason",
                        ""
                    )
                }

            # ------------------------------------------------
            # EXECUTE
            # ------------------------------------------------

            result = self.execute_decision(
                decision
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if result.get("success"):

                completed = {
                    "cycle": cycle,
                    "action": action,
                    "target": decision.get(
                        "target",
                        ""
                    ),
                    "result": result.get(
                        "result",
                        ""
                    )
                }

                self.completed_steps.append(
                    completed
                )

                print(
                    "\n✅ GEMINI ACTION VERIFIED"
                )

            else:

                print(
                    "\n❌ GEMINI ACTION FAILED"
                )

                # Tell Gemini what failed.
                self.completed_steps.append({
                    "cycle": cycle,
                    "action": action,
                    "target": decision.get(
                        "target",
                        ""
                    ),
                    "result": "FAILED"
                })

            # ------------------------------------------------
            # Small pause
            # ------------------------------------------------

            time.sleep(1)

        # ====================================================
        # MAX CYCLES
        # ====================================================

        print("\n🛑 Maximum adaptive cycles reached.")

        return {
            "success": False,
            "goal": goal,
            "cycles": self.max_steps,
            "completed_steps": (
                self.completed_steps
            ),
            "reason": "Maximum cycles reached"
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

    agent = GeminiAgent()

    goal = (
        "Search Minecraft tutorials on YouTube "
        "and open the first video"
    )

    try:

        result = agent.run(
            goal
        )

        print("\n" + "=" * 70)
        print("🐇 FINAL RESULT")
        print("=" * 70)

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        agent.keep_browser_open()

    except KeyboardInterrupt:

        print(
            "\n🐇 Gemini Agent stopped."
        )

    except Exception as e:

        print(
            f"\n❌ Fatal error: {e}"
        )

    finally:

        agent.close()
