import os
import base64
import requests

SCREENSHOT = os.path.expanduser("~/roborabbit/screenshots/firefox.png")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY is not set.")
    raise SystemExit(1)

if not os.path.exists(SCREENSHOT):
    print(f"❌ Screenshot not found: {SCREENSHOT}")
    print("Run your Firefox screenshot test first.")
    raise SystemExit(1)

with open(SCREENSHOT, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.6-flash:generateContent"
)

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": (
                        "Look at this computer screenshot. "
                        "Describe what is visible on the screen, "
                        "especially buttons, text fields, links, menus, "
                        "and other interactive elements. Keep it concise."
                    )
                },
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data,
                    }
                },
            ]
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

print("🧠 Sending screenshot to Gemini Vision...")

response = requests.post(
    f"{url}?key={API_KEY}",
    headers=headers,
    json=payload,
    timeout=60,
)

if response.status_code != 200:
    print("❌ Vision request failed:")
    print(response.text)
    raise SystemExit(1)

data = response.json()

try:
    answer = data["candidates"][0]["content"]["parts"][0]["text"]
except (KeyError, IndexError):
    print("❌ Unexpected Gemini response:")
    print(data)
    raise SystemExit(1)

print("\n🐇 RoboRabbit Vision:")
print(answer)
