import os
import subprocess
import tempfile

import sounddevice as sd
import soundfile as sf
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/roborabbit/.env"))

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.path.expanduser(
    "~/roborabbit/voices/en_US-lessac-medium.onnx"
)

def speak(text):
    print("🐇 RoboRabbit:", text)

    subprocess.run(
        ["piper-tts", "-m", MODEL, "-f", "/tmp/robo.wav"],
        input=text,
        text=True,
        check=True
    )

    audio, rate = sf.read("/tmp/robo.wav", dtype="float32")
    sd.play(audio, rate)
    sd.wait()

def listen():
    print("🎙️ Speak...")

    audio = sd.rec(
        int(5 * 44100),
        samplerate=44100,
        channels=2,
        dtype="float32"
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        sf.write(f.name, audio, 44100)

        with open(f.name, "rb") as file:
            result = groq.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo"
            )

    return result.text.strip()

speak("Hello bro. RoboRabbit is online.")

while True:
    text = listen()

    if not text:
        continue

    print("🗣️ You:", text)

    if text.lower() in ["exit", "quit", "stop"]:
        speak("Alright bro. Goodbye.")
        break

    # Temporary response
    speak("I heard you say " + text)
