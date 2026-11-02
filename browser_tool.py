import subprocess
import urllib.parse

FIREFOX = "/usr/bin/firefox"


def open_url(url):
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    subprocess.Popen(
        [FIREFOX, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"Opened {url}"


def google_search(query):
    query = query.strip()

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote(query)
    )

    subprocess.Popen(
        [FIREFOX, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"Searching Google for {query}"


def youtube_search(query):
    query = query.strip()

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
    )

    subprocess.Popen(
        [FIREFOX, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"Searching YouTube for {query}"


if __name__ == "__main__":

    print("🐇 RoboRabbit Firefox Controller")
    print("================================")

    google_search("Python programming tutorials")

    print("🦊 Firefox opened.")
