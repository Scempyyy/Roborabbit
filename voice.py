import os
import tempfile
import subprocess
import requests
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from groq import Groq


# =========================
# CONFIG
# =========================

SAMPLE_RATE = 16000
CHANNELS = 1
MIC_DEVICE = 10

ROBORABBIT_URL = "http://127.0.0.1:8000/chat"

PIPER_MODEL = os.path.expanduser(
    "~/.local/share/piper/voices/en_US-lessac-medium.onnx"
)

FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

VAD_MODE = 2

SILENCE_DURATION = 0.8
MIN_SPEECH_DURATION = 0.25


# =========================
# GROQ
# =========================

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set")

client = Groq(api_key=api_key)


# =========================
# VOICE ACTIVITY DETECTION
# =========================

vad = webrtcvad.Vad(VAD_MODE)


def is_speech(frame):
    return vad.is_speech(frame, SAMPLE_RATE)


def record_until_silence():

    print()
    print("🎙️ Listening...")

    audio_frames = []

    speech_started = False
    silence_frames = 0

    max_silence_frames = int(
        SILENCE_DURATION / (FRAME_DURATION_MS / 1000)
    )

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SIZE,
        dtype="int16",
        channels=CHANNELS,
        device=MIC_DEVICE
    )

    with stream:

        while True:

            data, overflowed = stream.read(FRAME_SIZE)

            if overflowed:
                continue

            frame = bytes(data)

            speech = is_speech(frame)

            if speech:

                if not speech_started:
                    print("🗣️ Speech detected!")

                speech_started = True
                silence_frames = 0
                audio_frames.append(frame)

            else:

                if speech_started:

                    audio_frames.append(frame)
                    silence_frames += 1

                    if silence_frames >= max_silence_frames:
                        break

    if not speech_started:
        return None

    print("⏹️ Speech finished.")

    return b"".join(audio_frames)


# =========================
# SAVE AUDIO
# =========================

def save_audio(audio_data):

    filename = tempfile.mktemp(suffix=".wav")

    # Convert raw PCM bytes → NumPy int16 array
    samples = np.frombuffer(
        audio_data,
        dtype=np.int16
    )

    sf.write(
        filename,
        samples,
        SAMPLE_RATE,
        subtype="PCM_16"
    )

    return filename


# =========================
# GROQ WHISPER
# =========================

def transcribe(audio_data):

    filename = save_audio(audio_data)

    try:

        with open(filename, "rb") as audio_file:

            result = client.audio.transcriptions.create(
                file=("voice.wav", audio_file.read()),
                model="whisper-large-v3-turbo",
                language="en",
                response_format="text"
            )

        return result.strip()

    finally:

        if os.path.exists(filename):
            os.remove(filename)


# =========================
# ROBO RABBIT
# =========================

def ask_roborabbit(text):

    try:

        response = requests.post(
            ROBORABBIT_URL,
            json={
                "message": text
            },
            timeout=30
        )

        response.raise_for_status()

        return response.json().get(
            "reply",
            "I didn't get a response."
        )

    except requests.RequestException as e:

        return f"Could not connect to RoboRabbit: {e}"


# =========================
# PIPER TTS
# =========================

def speak(text):

    print()
    print(f"🔊 RoboRabbit: {text}")

    output_file = "/tmp/roborabbit.wav"

    try:

        subprocess.run(
            [
                "piper",
                "--model",
                PIPER_MODEL,
                "--output_file",
                output_file
            ],
            input=text,
            text=True,
            check=True
        )

        subprocess.run(
            [
                "aplay",
                output_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

    except Exception as e:

        print(f"⚠️ TTS error: {e}")


# =========================
# MAIN
# =========================

def main():

    print()
    print("🐇 RoboRabbit Voice v3")
    print("======================")
    print("Continuous voice mode")
    print("Say 'quit' or 'exit' to stop.")
    print()

    while True:

        try:

            audio = record_until_silence()

            if audio is None:
                continue

            text = transcribe(audio)

            if not text:
                print("❌ I didn't understand.")
                continue

            print()
            print(f"📝 You: {text}")

            if text.lower().strip() in [
                "quit",
                "exit",
                "stop robo rabbit",
                "shutdown"
            ]:

                speak("Okay, shutting down.")
                break

            reply = ask_roborabbit(text)

            speak(reply)

            print()

        except KeyboardInterrupt:

            print()
            print("🐇 RoboRabbit stopped.")
            break

        except Exception as e:

            print()
            print(f"❌ Error: {e}")

            time.sleep(1)


if __name__ == "__main__":
    main()
