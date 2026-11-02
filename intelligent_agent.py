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

from hybrid_brain import HybridBrain
from action_executor import ActionExecutor
from context_manager import ContextManager
from context_resolver import ContextResolver
from task_agent import TaskStep


# ============================================================
# INTELLIGENT AGENT
# ============================================================

class IntelligentAgent:

    def __init__(self):

        print(
            "🐇 Initializing RoboRabbit Intelligent Agent..."
        )

        self.brain = HybridBrain()
        self.executor = ActionExecutor()
        self.context = ContextManager()
        self.context_resolver = ContextResolver(self.context)

        print("🧠 Hybrid Brain: READY")
        print("⚡ Action Executor: READY")
        print("🤖 Intelligent Agent: READY")
        print("🔄 Adaptive Recovery: READY")

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

            browser = self.executor.browser

            if browser is not None:

                state["browser_available"] = True

                state["url"] = (
                    browser.get_url()
                )

                state["title"] = (
                    browser.get_title()
                )

                state["page_text"] = (
                    browser.get_visible_text()
                )[:6000]

        except Exception as e:

            print(
                f"⚠️ Browser observation unavailable: {e}"
            )

        return state

    # ========================================================
    # CONVERSATION RESPONSE
    # ========================================================

    def conversation_response(
        self,
        command
    ):

        command = command.lower().strip()

        if command in (
            "hi",
            "hello",
            "hey",
            "hello.",
            "hi.",
            "hey."
        ):

            return (
                "Hello! 👋 "
                "I'm RoboRabbit. "
                "What can I do for you?"
            )

        if command in (
            "good morning",
            "good afternoon",
            "good evening"
        ):

            return (
                f"{command.title()}! 🐇 "
                "How can I help?"
            )

        if command in (
            "thanks",
            "thank you",
            "thanks.",
            "thank you."
        ):

            return (
                "You're welcome! 🐇"
            )

        if command in (
            "who are you",
            "what are you"
        ):

            return (
                "I'm RoboRabbit, "
                "your desktop assistant. 🐇🤖"
            )

        return (
            "I'm ready. 🐇"
        )

    # ========================================================
    # CONVERT GEMINI DECISION → TASK STEP
    # ========================================================

    def decision_to_step(
        self,
        decision
    ):

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

        if action in (
            "browser_google_search",
            "browser_youtube_search",
            "browser_open",
            "browser_click",
            "browser_type",
            "click",
            "type"
        ):

            if not target and value:

                target = value
                value = ""

        return TaskStep(
            action=action,
            target=target,
            value=value,
            description=decision.get(
                "reason",
                f"Execute {action}"
            )
        )

    # ========================================================
    # EXECUTE ONE STEP
    # ========================================================

    def execute_step(
        self,
        step
    ):

        print(
            f"\n▶️ ACTION: {step.action}"
        )

        print(
            f"🎯 TARGET: {step.target}"
        )

        print(
            f"📝 VALUE: {step.value}"
        )

        try:

            result = (
                self.executor
                .execute_step(step)
            )

            if result:

                print(
                    "✅ ACTION VERIFIED"
                )

                return True

            print(
                "❌ ACTION FAILED VERIFICATION"
            )

            return False

        except Exception as e:

            print(
                f"❌ ACTION ERROR: {e}"
            )

            return False

    # ========================================================
    # EXECUTE LOCAL PLAN
    # ========================================================

    def execute_local_plan(
        self,
        plan,
        completed_steps
    ):

        print(
            f"\n⚡ LOCAL PLAN: "
            f"{len(plan.steps)} step(s)"
        )

        for index, step in enumerate(
            plan.steps,
            1
        ):

            print(
                f"\n▶️ LOCAL STEP "
                f"{index}/{len(plan.steps)}"
            )

            print(
                f"   {step.description}"
            )

            if self.execute_step(step):

                completed_steps.append(
                    step.description
                )

                continue

            print(
                "⚠️ Local step failed."
            )

            return False

        return True

    # ========================================================
    # GEMINI RECOVERY
    # ========================================================

    def recover_with_gemini(
        self,
        goal,
        state,
        completed_steps,
        failed_action
    ):

        if self.brain.gemini is None:

            return None

        print(
            "\n🧠 ADAPTIVE RECOVERY"
        )

        print(
            f"❌ Failed action: "
            f"{failed_action}"
        )

        try:

            decision = (
                self.brain.gemini_decision(
                    goal=goal,
                    state=state,
                    completed_steps=completed_steps
                )
            )

            return decision

        except Exception as e:

            print(
                f"❌ Recovery failed: {e}"
            )

            return None

    # ========================================================
    # EXECUTE GEMINI DECISION
    # ========================================================

    def execute_gemini_step(
        self,
        decision,
        completed_steps
    ):

        action = decision.get(
            "action",
            "stop"
        )

        # IMPORTANT:
        # "done" is a state, not an executable action.

        if action == "done":

            print(
                "🎉 Gemini says the goal is complete."
            )

            return True

        if action == "stop":

            print(
                "🛑 Gemini requested stop."
            )

            return False

        step = self.decision_to_step(
            decision
        )

        if self.execute_step(step):

            completed_steps.append(
                step.description
            )

            return True

        return False

    # ========================================================
    # MAIN RUN LOOP
    # ========================================================

    def run(
        self,
        goal,
        max_cycles=8,
        max_recoveries=3
    ):

        print("\n")
        print("=" * 70)
        print("🐇 ROBORABBIT INTELLIGENT AGENT")
        print("=" * 70)

        print(
            f"🎯 GOAL: {goal}"
        )

        print("=" * 70)

        # Resolve contextual references before planning
        original_goal = goal
        goal = self.context_resolver.resolve(goal)

        if goal != original_goal:
            print(f"🧠 CONTEXT: {original_goal} → {goal}")

        completed_steps = []

        recovery_count = 0

        for cycle in range(
            1,
            max_cycles + 1
        ):

            print(
                f"\n🔄 CYCLE "
                f"{cycle}/{max_cycles}"
            )

            # ------------------------------------------------
            # OBSERVE
            # ------------------------------------------------

            print(
                "👀 OBSERVING..."
            )

            state = self.observe()

            print(
                f"🌐 URL: "
                f"{state['url']}"
            )

            print(
                f"📄 TITLE: "
                f"{state['title']}"
            )

            # ------------------------------------------------
            # THINK
            # ------------------------------------------------

            result = self.brain.route(
                command=goal,
                state=state,
                completed_steps=completed_steps
            )

            source = result.get(
                "source"
            )

            result_type = result.get(
                "type"
            )

            print(
                f"\n🧠 BRAIN: "
                f"{source.upper()}"
            )

            # =================================================
            # LOCAL CONVERSATION
            # =================================================

            if (
                source == "local"
                and result_type == "conversation"
            ):

                response = (
                    self.conversation_response(
                        result["command"]
                    )
                )

                print()
                print(
                    f"🐇 RoboRabbit: {response}"
                )

                return True

            # =================================================
            # LOCAL PLAN
            # =================================================

            if (
                source == "local"
                and result_type == "plan"
            ):

                plan = result.get(
                    "plan"
                )

                if plan is None:

                    print(
                        "❌ No local plan."
                    )

                    failed_action = (
                        "Local planner returned no plan"
                    )

                else:

                    success = (
                        self.execute_local_plan(
                            plan,
                            completed_steps
                        )
                    )

                    if success:

                        print(
                            "\n🎉 TASK COMPLETED"
                        )

                        return True

                    failed_action = (
                        "Local plan execution failed"
                    )

            # =================================================
            # GEMINI
            # =================================================

            elif source == "gemini":

                decision = result.get(
                    "decision",
                    {}
                )

                action = decision.get(
                    "action",
                    "stop"
                )

                # "done" is immediate completion.
                if action == "done":

                    print(
                        "\n🎉 TASK COMPLETED"
                    )

                    return True

                if action == "stop":

                    reason = decision.get(
                        "reason",
                        ""
                    )

                    print(
                        f"🛑 Gemini stopped: "
                        f"{reason}"
                    )

                    failed_action = (
                        f"Gemini stopped: {reason}"
                    )

                else:

                    success = (
                        self.execute_gemini_step(
                            decision,
                            completed_steps
                        )
                    )

                    if success:

                        time.sleep(1)

                        continue

                    failed_action = (
                        f"Gemini action failed: "
                        f"{action}"
                    )

            # =================================================
            # RECOVERY
            # =================================================

            recovery_count += 1

            if recovery_count > max_recoveries:

                print(
                    "\n🛑 Maximum recovery attempts reached."
                )

                break

            print(
                f"\n🔧 RECOVERY "
                f"{recovery_count}/{max_recoveries}"
            )

            time.sleep(1)

            new_state = self.observe()

            recovery_decision = (
                self.recover_with_gemini(
                    goal=goal,
                    state=new_state,
                    completed_steps=completed_steps,
                    failed_action=failed_action
                )
            )

            if recovery_decision:

                action = recovery_decision.get(
                    "action",
                    "stop"
                )

                # Recovery itself can report completion.
                if action == "done":

                    print(
                        "🎉 Recovery reports goal complete."
                    )

                    return True

                if self.execute_gemini_step(
                    recovery_decision,
                    completed_steps
                ):

                    continue

            print(
                "⚠️ Recovery attempt failed."
            )

        print(
            "\n❌ RoboRabbit could not complete the goal."
        )

        return False

    # ========================================================
    # KEEP BROWSER OPEN
    # ========================================================

    def keep_browser_open(self):
        try:
            browser = self.executor.get_browser()

            if browser is not None:
                print("\n🦊 Firefox is staying open.")
                print("🐇 RoboRabbit will leave Firefox running.")

        except Exception as e:
            print(f"⚠️ Browser keep-alive error: {e}")


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    agent = IntelligentAgent()

    goal = (
        "search Minecraft tutorials "
        "on YouTube and open the first video"
    )

    success = agent.run(
        goal,
        max_cycles=8,
        max_recoveries=3
    )

    print()

    if success:

        print(
            "✅ RoboRabbit completed the task."
        )

    else:

        print(
            "❌ RoboRabbit could not complete the task."
        )

