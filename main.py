import os
import sys
import traceback
import importlib.util
from importlib.machinery import SourceFileLoader

from dotenv import load_dotenv

from task_agent import TaskAgent
from action_executor import ActionExecutor



# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(
    os.path.join(BASE_DIR, ".env"),
    override=False
)

BACKUP_FILE = os.path.join(
    BASE_DIR,
    "main.py.backup"
)

print("🐇 Loading RoboRabbit core...")

if not os.path.exists(BACKUP_FILE):

    print("❌ main.py.backup was not found!")
    sys.exit(1)


# ============================================================
# LOAD EXISTING ROBO RABBIT CORE
# ============================================================

try:

    loader = SourceFileLoader(
        "roborabbit_base",
        BACKUP_FILE
    )

    spec = importlib.util.spec_from_loader(
        loader.name,
        loader
    )

    base = importlib.util.module_from_spec(
        spec
    )

    loader.exec_module(base)

except Exception:

    print("❌ Could not load main.py.backup")
    traceback.print_exc()
    sys.exit(1)


# ============================================================
# ROBO RABBIT TASK AGENT
# ============================================================

try:
    task_agent = TaskAgent()
    verified_executor = ActionExecutor()
    TASK_AGENT_AVAILABLE = True
    print("🤖 Task Agent: ENABLED")
except Exception as e:
    task_agent = None
    verified_executor = None
    TASK_AGENT_AVAILABLE = False
    print(f"⚠️ Task Agent unavailable: {e}")


# ============================================================
# COMPUTER CONTROL
# ============================================================

try:

    from computer_agent import ComputerAgent

    computer_agent = ComputerAgent()

    computer_status = computer_agent.status()

    COMPUTER_CONTROL_AVAILABLE = (
        computer_status.get("ready", False)
    )

except Exception as e:

    computer_agent = None

    computer_status = {
        "ready": False,
        "error": str(e)
    }

    COMPUTER_CONTROL_AVAILABLE = False


# ============================================================
# COMPUTER COMMAND HANDLER
# ============================================================

def computer_command(message):

    if (
        computer_agent is None
        or not COMPUTER_CONTROL_AVAILABLE
    ):

        return None

    text = message.strip()
    lower = text.lower()

    # Remove RoboRabbit prefix

    for prefix in (
        "roborabbit",
        "robo rabbit"
    ):

        if lower.startswith(prefix):

            text = text[
                len(prefix):
            ].strip(" ,:-")

            break

    lower = text.lower().strip()


    # --------------------------------------------------------
    # TYPE
    # --------------------------------------------------------

    for prefix in (
        "type ",
        "type:",
        "write ",
        "write:",
        "type text ",
        "type text:"
    ):

        if lower.startswith(prefix):

            content = text[
                len(prefix):
            ].strip()

            if not content:

                return "What should I type?"

            result = computer_agent.type_text(
                content
            )

            if result.get("success"):

                return f"Typed: {content}"

            return (
                "Computer control error: "
                f"{result.get('error')}"
            )


    # --------------------------------------------------------
    # PRESS KEY
    # --------------------------------------------------------

    for prefix in (
        "press ",
        "press key ",
        "hit "
    ):

        if lower.startswith(prefix):

            key = text[
                len(prefix):
            ].strip()

            if not key:

                return "Which key should I press?"

            result = computer_agent.press_key(
                key
            )

            if result.get("success"):

                return f"Pressed {key}."

            return (
                "Computer control error: "
                f"{result.get('error')}"
            )


    # --------------------------------------------------------
    # HOTKEY
    # --------------------------------------------------------

    for prefix in (
        "hotkey ",
        "shortcut ",
        "press shortcut "
    ):

        if lower.startswith(prefix):

            combo = text[
                len(prefix):
            ].strip()

            keys = [
                key.strip()
                for key in combo.replace(
                    "+",
                    " "
                ).split()
                if key.strip()
            ]

            if not keys:

                return (
                    "Which shortcut should I press?"
                )

            result = computer_agent.hotkey(
                *keys
            )

            if result.get("success"):

                return (
                    f"Pressed {' + '.join(keys)}."
                )

            return (
                "Computer control error: "
                f"{result.get('error')}"
            )


    # --------------------------------------------------------
    # COMMON SHORTCUTS
    # --------------------------------------------------------

    shortcuts = {

        "copy":
            ["ctrl", "c"],

        "paste":
            ["ctrl", "v"],

        "cut":
            ["ctrl", "x"],

        "undo":
            ["ctrl", "z"],

        "save":
            ["ctrl", "s"],

        "select all":
            ["ctrl", "a"],

        "new tab":
            ["ctrl", "t"],

        "close tab":
            ["ctrl", "w"],

        "refresh page":
            ["ctrl", "r"],

        "reload page":
            ["ctrl", "r"],
    }

    if lower in shortcuts:

        result = computer_agent.hotkey(
            *shortcuts[lower]
        )

        if result.get("success"):

            return (
                f"Done: {lower}."
            )

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    # --------------------------------------------------------
    # MOUSE MOVE
    # --------------------------------------------------------

    for prefix in (
        "move mouse to ",
        "move cursor to ",
        "move mouse ",
        "move cursor "
    ):

        if lower.startswith(prefix):

            coords = text[
                len(prefix):
            ].strip()

            coords = coords.replace(
                ",",
                " "
            )

            parts = coords.split()

            if len(parts) < 2:

                return (
                    "Use: move mouse to 500, 300"
                )

            try:

                x = int(parts[0])
                y = int(parts[1])

            except ValueError:

                return (
                    "Coordinates must be numbers."
                )

            result = computer_agent.move_mouse(
                x,
                y
            )

            if result.get("success"):

                return (
                    f"Moved mouse to {x}, {y}."
                )

            return (
                "Computer control error: "
                f"{result.get('error')}"
            )


    # --------------------------------------------------------
    # CLICK
    # --------------------------------------------------------

    if lower in (
        "click",
        "left click",
        "click left",
        "click mouse"
    ):

        result = computer_agent.click(
            "left"
        )

        if result.get("success"):

            return "Clicked."

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    if lower in (
        "right click",
        "click right"
    ):

        result = computer_agent.click(
            "right"
        )

        if result.get("success"):

            return "Right-clicked."

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    if lower in (
        "double click",
        "double-click",
        "double click mouse"
    ):

        result = computer_agent.double_click()

        if result.get("success"):

            return "Double-clicked."

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    # --------------------------------------------------------
    # SCROLL
    # --------------------------------------------------------

    if lower in (
        "scroll down",
        "scroll down a bit",
        "scroll down page"
    ):

        result = computer_agent.scroll(
            -5
        )

        if result.get("success"):

            return "Scrolled down."

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    if lower in (
        "scroll up",
        "scroll up a bit",
        "scroll up page"
    ):

        result = computer_agent.scroll(
            5
        )

        if result.get("success"):

            return "Scrolled up."

        return (
            "Computer control error: "
            f"{result.get('error')}"
        )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if lower in (
        "computer status",
        "computer control status",
        "input status"
    ):

        status = computer_agent.status()

        return (
            "Computer control is "
            f"{'ready' if status.get('ready') else 'not ready'}."
        )

    return None


# ============================================================
# PATCH ORIGINAL LOCAL ROUTER
# ============================================================

original_local_router = getattr(
    base,
    "local_router",
    None
)


def agent_command(message):
    if not TASK_AGENT_AVAILABLE:
        return None

    try:
        plan = task_agent.plan(message)

        if not plan.steps:
            return None

        if all(step.action == "unknown" for step in plan.steps):
            return None

        results = verified_executor.execute_plan(plan)

        if not results:
            return None

        failed = [r for r in results if not r.get("success")]

        if failed:
            return failed[-1].get(
                "result",
                "RoboRabbit could not complete the task."
            )

        return results[-1].get(
            "result",
            "Done."
        )

    except Exception as e:
        print("❌ Agent command error:", repr(e))
        traceback.print_exc()
        return f"RoboRabbit agent error: {e}"

def enhanced_local_router(message):

    result = agent_command(message)

    if result is not None:
        return result

    result = computer_command(message)

    result = computer_command(
        message
    )

    if result is not None:

        return result

    if original_local_router is not None:

        result = original_local_router(
            message
        )

        # Empty local results must not block
        # the Gemini brain.

        if result == "":

            return None

        return result

    return None


if original_local_router is not None:

    base.local_router = (
        enhanced_local_router
    )


# ============================================================
# PATCH CHAT RESPONSE
# ============================================================
#
# Keep the original chat logic.
# The only protection added here is that an accidental
# empty response is converted into a useful message instead
# of silently returning {"response": ""}.
#
# ============================================================

original_chat = getattr(
    base,
    "chat",
    None
)


def safe_chat(request):

    if original_chat is None:

        return {
            "response":
            "RoboRabbit chat handler is unavailable."
        }

    try:

        result = original_chat(
            request
        )

        if not isinstance(
            result,
            dict
        ):

            return {
                "response":
                str(result)
            }

        response = result.get(
            "response"
        )

        if response is None:

            return {
                "response":
                "RoboRabbit returned no response."
            }

        if isinstance(
            response,
            str
        ) and not response.strip():

            return {
                "response":
                "RoboRabbit received an empty "
                "response from the AI. Please try again."
            }

        return result

    except Exception as e:

        print(
            "❌ Chat error:",
            repr(e)
        )

        traceback.print_exc()

        return {
            "response":
            f"RoboRabbit error: {e}"
        }


# ============================================================
# PATCH THE EXISTING FASTAPI ROUTE
# ============================================================

try:

    from fastapi.routing import APIRoute
    from fastapi.dependencies.utils import get_dependant

    for route in base.app.routes:

        if (
            isinstance(route, APIRoute)
            and route.path == "/chat"
        ):

            route.endpoint = safe_chat

            route.dependant = get_dependant(
                path=route.path_format,
                call=safe_chat
            )

            print(
                "🔧 /chat route patched successfully."
            )

            break

except Exception:

    print(
        "⚠️ Could not patch /chat route."
    )

    traceback.print_exc()


# ============================================================
# STARTUP
# ============================================================

print("")
print("🐇 RoboRabbit starting...")
print("🧠 Gemini: gemini-3.6-flash")
print("🦊 Firefox: ENABLED")
print("🌐 Browser: DOM-FIRST")
print("🤖 Task Planner: ENABLED")
print("👁️ Vision: AVAILABLE")
print("💾 Memory: ENABLED")

if COMPUTER_CONTROL_AVAILABLE:

    print(
        "🖱️ Computer Control: ENABLED"
    )

else:

    print(
        "🖱️ Computer Control: DISABLED"
    )

    print(
        f"   Reason: {computer_status}"
    )

print("")
print("🚀 http://127.0.0.1:8000")
print("")


# ============================================================
# START SERVER
# ============================================================

try:

    import uvicorn

    uvicorn.run(
        base.app,
        host="127.0.0.1",
        port=8000
    )

except KeyboardInterrupt:

    print(
        "\n🐇 RoboRabbit stopped."
    )

except Exception:

    traceback.print_exc()
