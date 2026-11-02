import re


class ContextResolver:

    def __init__(self, context):
        self.context = context

    def resolve(self, command):

        command = command.strip().lower()

        if not command:
            return command

        recent = self.context.recent(5)

        if not recent:
            return command

        last = recent[-1]

        last_goal = last.get("goal", "").lower().strip()

        # -----------------------------------------
        # FIRST RESULT
        # -----------------------------------------

        if re.search(
            r"\b(open|click)\s+(the\s+)?first\s+result\b",
            command
        ):
            if last_goal.startswith("search "):

                query = last_goal[7:].strip()

                return f"open first result for {query}"

        # -----------------------------------------
        # SECOND RESULT
        # -----------------------------------------

        if re.search(
            r"\b(open|click)\s+(the\s+)?second\s+result\b",
            command
        ):
            if last_goal.startswith("search "):

                query = last_goal[7:].strip()

                return f"open second result for {query}"

        # -----------------------------------------
        # SEARCH THAT / SEARCH IT
        # -----------------------------------------

        if command in {
            "search that",
            "search it",
            "look that up",
            "look it up"
        }:

            if last_goal:

                if last_goal.startswith("search "):
                    return last_goal

                return f"search {last_goal}"

        # -----------------------------------------
        # OPEN IT / OPEN THAT
        # -----------------------------------------

        if command in {
            "open it",
            "open that"
        }:

            if last_goal.startswith("open "):

                return last_goal

        # -----------------------------------------
        # CLOSE IT / CLOSE THAT
        # -----------------------------------------

        if command in {
            "close it",
            "close that",
            "exit it",
            "quit it"
        }:

            if last_goal.startswith("open "):

                return f"close {last_goal[5:].strip()}"

        # -----------------------------------------
        # GO BACK
        # -----------------------------------------

        if command in {
            "go back",
            "go backwards",
            "back"
        }:

            return "go back"

        # -----------------------------------------
        # GO FORWARD
        # -----------------------------------------

        if command in {
            "go forward",
            "forward"
        }:

            return "go forward"

        return command
