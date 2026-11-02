import re
from dataclasses import dataclass


@dataclass
class TaskStep:
    action: str
    target: str = ""
    text: str = ""
    key: str = ""
    value: str = ""
    description: str = ""

    def __post_init__(self):
        if not self.value:
            if self.text:
                self.value = self.text
            elif self.key:
                self.value = self.key
            else:
                self.value = self.target

        if not self.target and self.value:
            if self.action in ("app_launch", "app_close", "browser_open", "navigate", "browser_search"):
                self.target = self.value

    @property
    def description_text(self):
        if self.description:
            return self.description
        if self.text:
            return self.text
        if self.key:
            return f"Press {self.key}"
        if self.target:
            return f"{self.action.replace('_', ' ').title()} {self.target}"
        return self.action.replace("_", " ").title()


@dataclass
class TaskPlan:
    steps: list


class TaskAgent:
    def __init__(self):
        pass

    def plan(self, goal):
        goal = goal.lower().strip()

        parts = re.split(
            r'\s+(?:and then|then|and)\s+|,\s*',
            goal
        )

        steps = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if re.search(r'\b(open|launch|start)\s+terminal\b', part):
                steps.append(TaskStep("app_launch", target="terminal"))
                continue

            if re.search(r'\b(open|launch|start)\s+spotify\b', part):
                steps.append(TaskStep("app_launch", target="spotify"))
                continue

            if re.search(r'\b(open|launch|start)\s+(files|file manager)\b', part):
                steps.append(TaskStep("app_launch", target="files"))
                continue

            if re.search(r'\b(close|exit|quit)\s+terminal\b', part):
                steps.append(TaskStep("app_close", target="terminal"))
                continue

            if re.search(r'\b(close|exit|quit)\s+spotify\b', part):
                steps.append(TaskStep("app_close", target="spotify"))
                continue

            if re.search(r'\b(close|exit|quit)\s+(files|file manager)\b', part):
                steps.append(TaskStep("app_close", target="files"))
                continue

            if re.search(r'\b(open|launch|start)\s+(firefox|browser)\b', part):
                steps.append(TaskStep("browser_open", target="firefox"))
                continue

            # Click/open first or second video/result
            if re.search(
                r'\\b(click|open)\\s+(on\\s+)?(the\\s+)?first\\s+(video|result)\\b',
                part
            ):
                steps.append(TaskStep(
                    "browser_result",
                    target="first",
                    value="first"
                ))
                continue

            if re.search(
                r'\\b(click|open)\\s+(on\\s+)?(the\\s+)?second\\s+(video|result)\\b',
                part
            ):
                steps.append(TaskStep(
                    "browser_result",
                    target="second",
                    value="second"
                ))
                continue

            # Also handle "first video" / "second video"
            if re.search(r'\\bfirst\\s+video\\b', part):
                steps.append(TaskStep(
                    "browser_result",
                    target="first",
                    value="first"
                ))
                continue

            if re.search(r'\\bsecond\\s+video\\b', part):
                steps.append(TaskStep(
                    "browser_result",
                    target="second",
                    value="second"
                ))
                continue

            if re.search(
                r'\b(click|open)\s+(on\s+)?(the\s+)?first\s+(video\s+)?result\b',
                part
            ):
                steps.append(TaskStep(
                    "browser_result",
                    target="first",
                    value="first"
                ))
                continue

            if re.search(
                r'\b(click|open)\s+(on\s+)?(the\s+)?second\s+(video\s+)?result\b',
                part
            ):
                steps.append(TaskStep(
                    "browser_result",
                    target="second",
                    value="second"
                ))
                continue

            # Open first/second result from a previous search
            match = re.search(
                r'\bopen\s+(first|second)\s+result\s+for\s+(.+)',
                part
            )
            if match:
                position = match.group(1).strip()
                query = match.group(2).strip()

                steps.append(TaskStep(
                    "browser_search",
                    target=query
                ))

                steps.append(TaskStep(
                    "browser_result",
                    target=position,
                    value=position
                ))
                continue

            # Open first/second result from a previous search
            match = re.search(
                r'\bopen\s+(first|second)\s+result\s+for\s+(.+)',
                part
            )
            if match:
                position = match.group(1).strip()
                query = match.group(2).strip()

                steps.append(TaskStep(
                    "browser_search",
                    target=query
                ))

                steps.append(TaskStep(
                    "browser_result",
                    target=position,
                    value=position
                ))
                continue

            match = re.search(r'\bsearch(?:\s+for)?\s+(.+)', part)
            if match:
                query = match.group(1).strip()

                query = re.sub(
                    r'\s+(?:on|in)\s+(?:youtube|google)$',
                    '',
                    query,
                    flags=re.IGNORECASE
                ).strip()

                steps.append(TaskStep(
                    "browser_search",
                    target=query
                ))
                continue

            match = re.search(r'\bgo\s+to\s+(.+)', part)
            if match:
                steps.append(TaskStep(
                    "navigate",
                    target=match.group(1).strip()
                ))
                continue

            match = re.search(r'\btype\s+(.+)', part)
            if match:
                steps.append(TaskStep(
                    "type",
                    text=match.group(1).strip()
                ))
                continue

            match = re.search(r'\bpress\s+(.+)', part)
            if match:
                steps.append(TaskStep(
                    "press",
                    key=match.group(1).strip()
                ))
                continue

        return TaskPlan(steps)

    def create_plan(self, goal):
        return self.plan(goal)

    def generate_plan(self, goal):
        return self.plan(goal)
