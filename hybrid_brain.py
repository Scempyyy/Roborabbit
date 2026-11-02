import os
import sys
import re


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
from decision_engine import DecisionEngine


# ============================================================
# HYBRID BRAIN
# ============================================================

class HybridBrain:

    def __init__(self):

        print("🐇 Initializing Hybrid Brain...")

        self.local_planner = TaskAgent()
        self.gemini = None

        try:
            self.gemini = DecisionEngine()
            print("🧠 Gemini fallback: READY")

        except Exception as e:

            print(
                f"⚠️ Gemini unavailable: {e}"
            )

        print("⚡ Local brain: READY")
        print("🐇 Hybrid Brain: READY")

    # ========================================================
    # NORMALIZE
    # ========================================================

    def normalize(self, text):

        text = text.lower().strip()

        text = re.sub(
            r"^roborabbit[\s,:-]*",
            "",
            text
        )

        text = text.replace("wi-fi", "wifi")
        text = text.replace("wi fi", "wifi")

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # ========================================================
    # CONVERSATION
    # ========================================================

    def is_conversation(self, text):

        text = self.normalize(text)

        conversation_patterns = [

            r"^hi$",
            r"^hello$",
            r"^hey$",
            r"^hello[.!]$",
            r"^hi[.!]$",
            r"^hey[.!]$",

            r"^good morning$",
            r"^good afternoon$",
            r"^good evening$",

            r"^thanks$",
            r"^thank you$",
            r"^thanks[.!]$",
            r"^thank you[.!]$",

            r"^who are you$",
            r"^what are you$",
        ]

        return any(
            re.search(
                pattern,
                text
            )
            for pattern in conversation_patterns
        )

    # ========================================================
    # LOCAL TASK DETECTION
    # ========================================================

    def is_local_task(self, text):

        text = self.normalize(text)

        if self.is_conversation(text):

            return True

        local_patterns = [

            # Browser
            r"open firefox",
            r"open youtube",
            r"open google",
            r"open github",
            r"open .*\.com",

            r"search .* on youtube",
            r"search youtube for",
            r"search google for",
            r"search .+",
r"open first result",
r"open second result",
            r"google .*",
            r"youtube .*",

            # Navigation
            r"go back",
            r"go forward",
            r"refresh",
            r"scroll down",
            r"scroll up",

            # Desktop apps
            r"(open|launch|start|close|exit|quit) terminal",
            r"(open|launch|start|close|exit|quit) spotify",
            r"(open|launch|start|close|exit|quit) files",
            r"(open|launch|start|close|exit|quit) file manager",

            # System
            r"what time is it",
            r"what's the time",
            r"current time",
            r"^time$",
            r"check battery",
            r"battery",
            r"check wifi",
            r"wifi",
            r"check cpu",
            r"check ram",
            r"check memory",
            r"system status",
        ]

        for pattern in local_patterns:

            if re.search(
                pattern,
                text
            ):

                return True

        return False

    # ========================================================
    # LOCAL PLAN
    # ========================================================

    def local_plan(self, command):

        # Conversation doesn't need TaskAgent.
        if self.is_conversation(command):

            return {
                "type": "conversation",
                "command": self.normalize(command)
            }

        try:

            plan = self.local_planner.plan(
                command
            )

            if plan and plan.steps:

                print(
                    "⚡ Local planner generated "
                    f"{len(plan.steps)} step(s)"
                )

                return plan

        except Exception as e:

            print(
                f"⚠️ Local planning failed: {e}"
            )

        return None

    # ========================================================
    # GEMINI DECISION
    # ========================================================

    def gemini_decision(
        self,
        goal,
        state,
        completed_steps=None
    ):

        if self.gemini is None:

            return {
                "action": "stop",
                "target": "",
                "value": "",
                "reason": "Gemini unavailable"
            }

        try:

            return self.gemini.decide(
                goal=goal,
                state=state,
                completed_steps=completed_steps
            )

        except Exception as e:

            print(
                f"⚠️ Gemini unavailable: {e}"
            )

            return {
                "action": "stop",
                "target": "",
                "value": "",
                "reason": str(e)
            }

    # ========================================================
    # ROUTE
    # ========================================================

    def route(
        self,
        command,
        state=None,
        completed_steps=None
    ):

        normalized = self.normalize(
            command
        )

        print("\n" + "=" * 60)
        print("🧠 HYBRID BRAIN")
        print("=" * 60)

        print(
            f"💬 Command: {command}"
        )

        # ----------------------------------------------------
        # CONVERSATION
        # ----------------------------------------------------

        if self.is_conversation(
            normalized
        ):

            print(
                "💬 ROUTE: LOCAL CONVERSATION"
            )

            return {
                "source": "local",
                "type": "conversation",
                "command": normalized
            }

        # ----------------------------------------------------
        # LOCAL TASK
        # ----------------------------------------------------

        if self.is_local_task(
            normalized
        ):

            print(
                "⚡ ROUTE: LOCAL"
            )

            plan = self.local_plan(
                command
            )

            if plan:

                return {
                    "source": "local",
                    "type": "plan",
                    "plan": plan
                }

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        print(
            "🧠 ROUTE: GEMINI FALLBACK"
        )

        if state is None:

            state = {
                "browser_available": False,
                "url": "",
                "title": "",
                "page_text": ""
            }

        decision = self.gemini_decision(
            goal=command,
            state=state,
            completed_steps=completed_steps
        )

        return {
            "source": "gemini",
            "type": "decision",
            "decision": decision
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    brain = HybridBrain()

    tests = [

        "hello",

        "thanks",

        "search Minecraft tutorials on YouTube",

        "open github.com",

        "do something complicated with this webpage",
    ]

    for command in tests:

        result = brain.route(
            command
        )

        print(
            f"\n🐇 RESULT SOURCE: "
            f"{result['source']}"
        )

        print(
            f"📦 RESULT TYPE: "
            f"{result['type']}"
        )

        if result["type"] == "conversation":

            print(
                f"💬 Conversation: "
                f"{result['command']}"
            )

        elif result["type"] == "plan":

            plan = result["plan"]

            print(
                f"📋 Local plan: "
                f"{len(plan.steps)} step(s)"
            )

            for i, step in enumerate(
                plan.steps,
                1
            ):

                print(
                    f"   {i}. "
                    f"{step.description}"
                )

        else:

            print(
                "🤖 Gemini decision:"
            )

            print(
                result["decision"]
            )

        print(
            "\n" + "-" * 60
        )
