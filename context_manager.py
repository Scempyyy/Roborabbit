import json
import os
from datetime import datetime


class ContextManager:

    def __init__(self, max_history=20):
        self.max_history = max_history
        self.history_file = os.path.expanduser(
            "~/roborabbit/conversation_history.json"
        )
        self.history = []
        self.load()

    def load(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    self.history = data[-self.max_history:]
        except Exception as e:
            print(f"⚠️ Context load failed: {e}")
            self.history = []

    def save(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.history[-self.max_history:],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            print(f"⚠️ Context save failed: {e}")

    def add(self, user, assistant="", goal=None):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "assistant": assistant,
            "goal": goal or user
        })

        self.history = self.history[-self.max_history:]
        self.save()

    def recent(self, count=5):
        return self.history[-count:]

    def get_context_text(self, count=5):
        recent = self.recent(count)

        if not recent:
            return ""

        lines = []

        for item in recent:
            user = item.get("user", "")
            assistant = item.get("assistant", "")

            lines.append(f"User: {user}")

            if assistant:
                lines.append(f"RoboRabbit: {assistant}")

        return "\n".join(lines)

    def clear(self):
        self.history = []
        self.save()

    def last_goal(self):
        if not self.history:
            return None

        return self.history[-1].get("goal")
