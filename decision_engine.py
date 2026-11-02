import os
import json
import time

from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.expanduser("~/roborabbit")

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

MODEL = "gemini-3.6-flash"

API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
]

API_KEYS = [
    key.strip()
    for key in API_KEYS
    if key and key.strip()
]


# ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:

    def __init__(self):

        if not API_KEYS:

            raise RuntimeError(
                "No Gemini API keys found in ~/roborabbit/.env"
            )

        self.clients = []

        for index, key in enumerate(
            API_KEYS,
            1
        ):

            try:

                client = genai.Client(
                    api_key=key
                )

                self.clients.append(
                    client
                )

                print(
                    f"🧠 Gemini Key {index}: READY"
                )

            except Exception as e:

                print(
                    f"⚠️ Gemini Key {index} failed: {e}"
                )

        if not self.clients:

            raise RuntimeError(
                "Could not initialize any Gemini clients."
            )

        self.current_key = 0

        print(
            f"🧠 Gemini Decision Engine initialized "
            f"with {len(self.clients)} key(s)"
        )

    # ========================================================
    # BUILD PROMPT
    # ========================================================

    def build_prompt(
        self,
        goal,
        state,
        completed_steps=None
    ):

        completed_steps = (
            completed_steps or []
        )

        prompt = f"""
You are the decision engine for RoboRabbit,
an autonomous desktop assistant.

USER GOAL:
{goal}

CURRENT BROWSER STATE:
URL: {state.get("url", "")}
TITLE: {state.get("title", "")}
BROWSER AVAILABLE: {state.get("browser_available", False)}

VISIBLE PAGE TEXT:
{state.get("page_text", "")[:6000]}

COMPLETED STEPS:
{completed_steps}

Choose exactly ONE next action.

AVAILABLE ACTIONS:

browser_google_search
browser_youtube_search
browser_open
browser_click
browser_type
browser_press
browser_click_first_google
browser_click_first_youtube
browser_back
browser_forward
browser_refresh
browser_scroll_down
browser_scroll_up
computer_type
computer_press
computer_click
computer_double_click
computer_scroll
done
stop

Return ONLY valid JSON:

{{
    "action": "action_name",
    "target": "target",
    "value": "value",
    "reason": "short explanation"
}}

Rules:

- Choose only one action.
- Do not invent actions.
- Prefer DOM/browser actions when possible.
- Use computer actions only when browser actions cannot accomplish the task.
- If the goal is complete, use "done".
- If the goal cannot be completed, use "stop".
"""

        return prompt

    # ========================================================
    # PARSE JSON
    # ========================================================

    def parse_json(
        self,
        text
    ):

        text = text.strip()

        # Remove markdown fences.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines:

                lines = lines[1:]

            if lines and lines[-1].strip() == "```":

                lines = lines[:-1]

            text = "\n".join(lines).strip()

        # Find JSON object if extra text exists.
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:

            text = text[start:end + 1]

        try:

            data = json.loads(
                text
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                f"Invalid Gemini JSON: {e}"
            )

        if not isinstance(
            data,
            dict
        ):

            raise ValueError(
                "Gemini response was not a JSON object."
            )

        return data

    # ========================================================
    # DECIDE
    # ========================================================

    def decide(
        self,
        goal,
        state,
        completed_steps=None
    ):

        if not self.clients:

            return {
                "action": "stop",
                "target": "",
                "value": "",
                "reason": "No Gemini clients available."
            }

        prompt = self.build_prompt(
            goal,
            state,
            completed_steps
        )

        # Try each configured key once.
        attempts = len(
            self.clients
        )

        for attempt in range(
            attempts
        ):

            key_index = (
                self.current_key %
                len(self.clients)
            )

            client = self.clients[
                key_index
            ]

            print(
                f"\n🧠 Asking Gemini "
                f"(Key {key_index + 1})..."
            )

            try:

                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

                text = getattr(
                    response,
                    "text",
                    None
                )

                if not text:

                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                decision = self.parse_json(
                    text
                )

                print(
                    f"🎯 Gemini Key "
                    f"{key_index + 1} chose: "
                    f"{decision.get('action', 'unknown')}"
                )

                print(
                    f"💡 Reason: "
                    f"{decision.get('reason', '')}"
                )

                # Keep successful key.
                self.current_key = key_index

                return decision

            except Exception as e:

                error_text = str(
                    e
                )

                print(
                    f"❌ Gemini Key "
                    f"{key_index + 1} error: "
                    f"{error_text}"
                )

                # Move to next key.
                self.current_key = (
                    key_index + 1
                ) % len(self.clients)

                # If another key exists, try it.
                if attempt + 1 < attempts:

                    print(
                        f"🔄 Switching to Gemini "
                        f"Key {self.current_key + 1}..."
                    )

                    continue

                # All keys failed.
                return {
                    "action": "stop",
                    "target": "",
                    "value": "",
                    "reason": (
                        "All Gemini API keys failed. "
                        + error_text
                    )
                }

        return {
            "action": "stop",
            "target": "",
            "value": "",
            "reason": "Gemini unavailable."
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🧠 GEMINI MULTI-KEY DECISION ENGINE")
    print("=" * 60)

    try:

        engine = DecisionEngine()

        state = {
            "browser_available": False,
            "url": "",
            "title": "",
            "page_text": ""
        }

        result = engine.decide(
            goal=(
                "Search YouTube for Minecraft tutorials"
            ),
            state=state,
            completed_steps=[]
        )

        print()
        print(
            "🎯 FINAL DECISION:"
        )

        print(
            json.dumps(
                result,
                indent=2
            )
        )

    except Exception as e:

        print(
            f"❌ Engine failed: {e}"
        )
