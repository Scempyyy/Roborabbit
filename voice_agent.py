import os
import re
import subprocess
import tempfile
import time

import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from groq import Groq

from intelligent_agent import IntelligentAgent
from context_manager import ContextManager


# ============================================================
# CONFIG
# ============================================================

load_dotenv(os.path.expanduser("~/roborabbit/.env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SAMPLE_RATE = 44100
CHANNELS = 2
MIC_DEVICE = 10
RECORD_SECONDS = 5

PIPER_MODEL = os.path.expanduser(
    "~/roborabbit/voices/en_US-lessac-medium.onnx"
)

TEMP_WAV = "/tmp/roborabbit_tts.wav"


# ============================================================
# CLIENTS
# ============================================================

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing from ~/roborabbit/.env")

groq = Groq(api_key=GROQ_API_KEY)
agent = IntelligentAgent()


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_speech_text(text):
    """Clean RoboRabbit's response before sending it to TTS."""

    if not text:
        return ""

    text = str(text)

    # Remove JSON-ish formatting
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove markdown
    text = re.sub(r"[*_#>`]", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# TTS
# ============================================================

def speak(text):
    """Generate speech with Piper and play it."""

    text = clean_speech_text(text)

    if not text:
        return

    print(f"🔊 RoboRabbit: {text}")

    try:
        subprocess.run(
            [
                "piper-tts",
                "-m",
                PIPER_MODEL,
                "-f",
                TEMP_WAV,
            ],
            input=text,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        data, samplerate = sf.read(TEMP_WAV, dtype="float32")

        sd.play(data, samplerate)
        sd.wait()

    except Exception as e:
        print(f"❌ TTS error: {e}")


# ============================================================
# SPEECH TO TEXT
# ============================================================

def listen():
    print("\n🎙️ Listening...")

    recording = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=MIC_DEVICE,
    )

    sd.wait()

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp:
        filename = temp.name

    sf.write(filename, recording, SAMPLE_RATE)

    try:
        print("🧠 Transcribing...")

        with open(filename, "rb") as audio_file:

            transcription = groq.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
            )

        text = transcription.text.strip()

        if text:
            print(f"🗣️ You said: {text}")

        return text

    finally:
        try:
            os.remove(filename)
        except OSError:
            pass


# ============================================================
# INPUT NORMALIZATION
# ============================================================

def normalize_command(text):

    if not text:
        return ""

    text = text.strip()

    # Common Whisper mistakes
    replacements = {
        "fire folks": "firefox",
        "fire fox": "firefox",
        "fire box": "firefox",
        "robo rabbit": "roborabbit",
    }

    lowered = text.lower()

    for wrong, correct in replacements.items():
        lowered = lowered.replace(wrong, correct)

    return lowered


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print()
    print("========================================")
    print("🐇 RoboRabbit Voice System")
    print("========================================")
    print("🎙️ Speech Recognition: Groq Whisper")
    print("🧠 Brain: Intelligent Agent")
    print("🔊 Voice: Piper TTS")
    print("========================================")
    print()

    print("Speak for up to 5 seconds.")
    print("Say 'exit' or 'quit' to stop.")
    print()

    context = ContextManager()

    # Startup greeting
    speak("Hello bro. RoboRabbit is online.")

    while True:

        try:

            text = listen()

            if not text:
                continue

            command = normalize_command(text)

            if command in [
                "exit",
                "quit",
                "stop",
                "shutdown",
                "goodbye",
            ]:

                speak(
                    "Alright bro. Shutting down RoboRabbit."
                )

                break

            # ------------------------------------------------
            # Send command to IntelligentAgent
            # ------------------------------------------------

            print("🐇 Processing...")

            result = agent.run(command)

            # Save real voice conversation to persistent context
            if isinstance(result, dict):
                saved_response = (
                    result.get("response")
                    or result.get("message")
                    or result.get("result")
                    or ""
                )
            else:
                saved_response = str(result) if result is not None else ""

            context.add(
                user=command,
                assistant=saved_response,
                goal=command
            )

            # IntelligentAgent may return different types
            if isinstance(result, dict):

                response = (
                    result.get("response")
                    or result.get("message")
                    or result.get("result")
                    or ""
                )

            else:

                response = (
                    str(result)
                    if result is not None
                    else ""
                )

            if response:

                # Don't speak raw internal status unnecessarily
                response = clean_speech_text(response)

                speak(response)

            else:

                speak("Done bro.")

            time.sleep(0.2)

        except KeyboardInterrupt:

            print("\n")

            speak("Stopping RoboRabbit.")

            break

        except Exception as e:

            print(f"❌ Voice error: {e}")

            speak(
                "I ran into an error while processing that."
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n🐇 RoboRabbit voice system stopped."
        )

    except Exception as e:

        print(
            f"\n❌ Fatal error: {e}"
        )
