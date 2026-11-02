import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FirefoxAgent:

    def __init__(self):

        self.driver = None

        self.profile_path = os.path.expanduser(
            "~/.roborabbit-firefox"
        )

        os.makedirs(
            self.profile_path,
            exist_ok=True
        )

        self.start()

    # ========================================================
    # START FIREFOX
    # ========================================================

    def start(self):

        if self.driver is not None:

            try:
                self.driver.quit()
            except Exception:
                pass

        options = Options()

        options.binary_location = "/usr/bin/firefox"

        options.add_argument("-profile")
        options.add_argument(
            self.profile_path
        )

        options.set_preference(
            "marionette.enabled",
            True
        )

        self.driver = webdriver.Firefox(
            options=options
        )

        self.driver.maximize_window()

        time.sleep(1)

    # ========================================================
    # CONNECTION
    # ========================================================

    def ensure_connection(self):

        try:

            _ = self.driver.current_url

        except Exception:

            print(
                "🦊 Firefox session expired. "
                "Reconnecting..."
            )

            self.start()

    # ========================================================
    # WAIT
    # ========================================================

    def wait_for_page(
        self,
        seconds=10
    ):

        self.ensure_connection()

        try:

            WebDriverWait(
                self.driver,
                seconds
            ).until(
                lambda d:
                d.execute_script(
                    "return document.readyState"
                ) == "complete"
            )

        except Exception:
            pass

    # ========================================================
    # OPEN
    # ========================================================

    def open(self, url):

        self.ensure_connection()

        self.driver.get(url)

        self.wait_for_page()

        return f"Opened {url}."

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    def search_google(
        self,
        query
    ):

        self.ensure_connection()

        self.driver.get(
            "https://www.google.com/"
        )

        self.wait_for_page()

        try:

            box = WebDriverWait(
                self.driver,
                10
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "textarea[name='q'], "
                        "input[name='q']"
                    )
                )
            )

            box.click()

            box.clear()

            box.send_keys(query)

            box.send_keys(
                Keys.ENTER
            )

        except Exception as e:

            return (
                f"Google search failed: {e}"
            )

        self.wait_for_page()

        return (
            f"Searched Google for: {query}."
        )

    # ========================================================
    # YOUTUBE SEARCH
    # ========================================================

    def search_youtube(
        self,
        query
    ):

        self.ensure_connection()

        print(
            f"🔎 YouTube search: {query}"
        )

        self.driver.get(
            "https://www.youtube.com/"
        )

        # Wait for YouTube to load its dynamic UI.

        try:

            WebDriverWait(
                self.driver,
                15
            ).until(
                lambda d:
                d.execute_script(
                    "return document.readyState"
                ) == "complete"
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # FIND SEARCH BOX
        # ----------------------------------------------------

        box = None

        selectors = [

            "input#search",

            "input[name='search_query']",

            "input[placeholder*='Search']",

            "input[aria-label*='Search']",

            "ytd-searchbox input",

        ]

        for selector in selectors:

            try:

                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                for element in elements:

                    if element.is_displayed():

                        box = element

                        print(
                            f"✅ Found YouTube search "
                            f"box: {selector}"
                        )

                        break

                if box is not None:
                    break

            except Exception:
                continue

        # ----------------------------------------------------
        # FAIL IF NO SEARCH BOX
        # ----------------------------------------------------

        if box is None:

            return (
                "YouTube search failed: "
                "search box not found."
            )

        # ----------------------------------------------------
        # TYPE QUERY
        # ----------------------------------------------------

        try:

            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center'
                });
                """,
                box
            )

            time.sleep(0.3)

            box.click()

            try:
                box.clear()
            except Exception:
                pass

            box.send_keys(query)

            time.sleep(0.5)

        except Exception as e:

            return (
                f"YouTube typing failed: {e}"
            )

        # ----------------------------------------------------
        # SUBMIT SEARCH
        # ----------------------------------------------------

        submitted = False

        # Method 1: Enter key

        try:

            box.send_keys(
                Keys.ENTER
            )

            submitted = True

            print(
                "⌨️ Submitted YouTube search "
                "with Enter"
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # WAIT FOR NAVIGATION
        # ----------------------------------------------------

        time.sleep(2)

        current_url = ""

        try:

            current_url = (
                self.driver.current_url
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # VERIFY URL
        # ----------------------------------------------------

        if (
            "search_query=" in
            current_url.lower()
        ):

            self.wait_for_page()

            return (
                f"Searched YouTube for: "
                f"{query}."
            )

        # ----------------------------------------------------
        # METHOD 2: SEARCH BUTTON
        # ----------------------------------------------------

        print(
            "⚠️ Enter did not navigate. "
            "Trying search button..."
        )

        button_selectors = [

            "button#search-icon-legacy",

            "ytd-searchbox button",

            "button[aria-label*='Search']",

            "button[title*='Search']",

        ]

        for selector in button_selectors:

            try:

                buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                for button in buttons:

                    if not button.is_displayed():
                        continue

                    try:

                        button.click()

                    except Exception:

                        self.driver.execute_script(
                            "arguments[0].click();",
                            button
                        )

                    submitted = True

                    print(
                        f"🔘 Clicked search button: "
                        f"{selector}"
                    )

                    break

                if submitted:
                    break

            except Exception:
                continue

        time.sleep(2)

        # ----------------------------------------------------
        # FINAL VERIFICATION
        # ----------------------------------------------------

        try:

            current_url = (
                self.driver.current_url
            )

        except Exception:

            current_url = ""

        if (
            "search_query=" in
            current_url.lower()
        ):

            self.wait_for_page()

            return (
                f"Searched YouTube for: "
                f"{query}."
            )

        # ----------------------------------------------------
        # JAVASCRIPT FALLBACK
        # ----------------------------------------------------

        print(
            "⚠️ Search button did not navigate. "
            "Trying direct YouTube search URL..."
        )

        try:

            from urllib.parse import quote_plus

            search_url = (
                "https://www.youtube.com/results"
                "?search_query="
                + quote_plus(query)
            )

            self.driver.get(
                search_url
            )

            self.wait_for_page()

            time.sleep(1)

            current_url = (
                self.driver.current_url
            )

            if (
                "search_query=" in
                current_url.lower()
            ):

                return (
                    f"Searched YouTube for: "
                    f"{query}."
                )

        except Exception as e:

            return (
                f"YouTube search failed: {e}"
            )

        return (
            "YouTube search could not be "
            "verified."
        )

    # ========================================================
    # SMART ELEMENT FINDER
    # ========================================================

    def find_element_smart(
        self,
        target
    ):

        self.ensure_connection()

        target = target.strip()

        lower_target = target.lower()

        elements = self.driver.find_elements(
            By.XPATH,
            "//*"
        )

        # Exact matches

        for element in elements:

            try:

                if not element.is_displayed():
                    continue

                values = [

                    element.text.strip(),

                    element.get_attribute(
                        "aria-label"
                    ) or "",

                    element.get_attribute(
                        "title"
                    ) or "",

                    element.get_attribute(
                        "placeholder"
                    ) or "",

                    element.get_attribute(
                        "name"
                    ) or "",

                    element.get_attribute(
                        "id"
                    ) or "",

                    element.get_attribute(
                        "value"
                    ) or "",

                ]

                for value in values:

                    if (
                        value.strip().lower()
                        == lower_target
                    ):

                        return element

            except Exception:
                continue

        # Partial matches

        for element in elements:

            try:

                if not element.is_displayed():
                    continue

                values = [

                    element.text.strip(),

                    element.get_attribute(
                        "aria-label"
                    ) or "",

                    element.get_attribute(
                        "title"
                    ) or "",

                    element.get_attribute(
                        "placeholder"
                    ) or "",

                    element.get_attribute(
                        "name"
                    ) or "",

                    element.get_attribute(
                        "id"
                    ) or "",

                    element.get_attribute(
                        "value"
                    ) or "",

                ]

                for value in values:

                    value = value.strip().lower()

                    if (
                        value
                        and lower_target in value
                    ):

                        return element

            except Exception:
                continue

        return None

    # ========================================================
    # CLICK TEXT
    # ========================================================

    def click_text(
        self,
        text
    ):

        self.ensure_connection()

        element = self.find_element_smart(
            text
        )

        if element is None:

            return (
                f"I couldn't find "
                f"'{text}' in the page."
            )

        try:

            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center',
                    inline: 'center'
                });
                """,
                element
            )

            time.sleep(0.3)

            try:

                element.click()

            except Exception:

                self.driver.execute_script(
                    "arguments[0].click();",
                    element
                )

            self.wait_for_page()

            return (
                f"Clicked '{text}'."
            )

        except Exception as e:

            return (
                f"Couldn't click "
                f"'{text}': {e}"
            )

    # ========================================================
    # CLICK FIRST GOOGLE RESULT
    # ========================================================

    def click_first_google_result(
        self
    ):

        self.ensure_connection()

        try:

            WebDriverWait(
                self.driver,
                10
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "h3"
                    )
                )
            )

            headings = self.driver.find_elements(
                By.CSS_SELECTOR,
                "h3"
            )

            for heading in headings:

                try:

                    if not heading.is_displayed():
                        continue

                    link = heading.find_element(
                        By.XPATH,
                        "./ancestor::a[1]"
                    )

                    if not link.is_displayed():
                        continue

                    title = heading.text.strip()

                    self.driver.execute_script(
                        """
                        arguments[0].scrollIntoView({
                            block: 'center'
                        });
                        """,
                        link
                    )

                    time.sleep(0.3)

                    try:

                        link.click()

                    except Exception:

                        self.driver.execute_script(
                            "arguments[0].click();",
                            link
                        )

                    self.wait_for_page()

                    return (
                        "Opened the first "
                        f"Google result: {title}"
                    )

                except Exception:
                    continue

            return (
                "I couldn't find a Google "
                "search result."
            )

        except Exception as e:

            return (
                f"Couldn't open first "
                f"Google result: {e}"
            )

    # ========================================================
    # CLICK FIRST YOUTUBE RESULT
    # ========================================================

    def click_first_youtube_result(
        self
    ):

        self.ensure_connection()

        try:

            WebDriverWait(
                self.driver,
                15
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "a#video-title"
                    )
                )
            )

            videos = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a#video-title"
            )

            for video in videos:

                try:

                    if not video.is_displayed():
                        continue

                    title = (
                        video.get_attribute(
                            "title"
                        )
                        or video.text
                        or "first video"
                    )

                    self.driver.execute_script(
                        """
                        arguments[0].scrollIntoView({
                            block: 'center'
                        });
                        """,
                        video
                    )

                    time.sleep(0.3)

                    try:

                        video.click()

                    except Exception:

                        self.driver.execute_script(
                            "arguments[0].click();",
                            video
                        )

                    self.wait_for_page()

                    return (
                        "Opened the first "
                        f"YouTube result: {title}"
                    )

                except Exception:
                    continue

            return (
                "I couldn't find a YouTube "
                "video result."
            )

        except Exception as e:

            return (
                f"Couldn't open first "
                f"YouTube result: {e}"
            )

    # ========================================================
    # INPUT
    # ========================================================

    def find_input(
        self,
        field="search"
    ):

        self.ensure_connection()

        field = field.strip().lower()

        selectors = [

            f"input[name='{field}']",

            f"textarea[name='{field}']",

            f"input[id='{field}']",

            f"textarea[id='{field}']",

            f"input[placeholder*='{field}']",

            f"textarea[placeholder*='{field}']",

            f"input[aria-label*='{field}']",

            f"textarea[aria-label*='{field}']",

        ]

        for selector in selectors:

            try:

                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                for element in elements:

                    if element.is_displayed():
                        return element

            except Exception:
                pass

        if field == "search":

            selectors = [

                "textarea[name='q']",

                "input[name='q']",

                "input#search",

                "input[type='search']",

                "textarea[aria-label*='Search']",

                "input[aria-label*='Search']",

            ]

            for selector in selectors:

                try:

                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        selector
                    )

                    for element in elements:

                        if element.is_displayed():
                            return element

                except Exception:
                    pass

        return None

    # ========================================================
    # TYPE
    # ========================================================

    def type_into(
        self,
        text,
        field="search"
    ):

        self.ensure_connection()

        element = self.find_input(
            field
        )

        if element is None:

            return (
                f"I couldn't find "
                f"an input for '{field}'."
            )

        try:

            element.click()

            element.clear()

            element.send_keys(text)

            return (
                f"Typed '{text}' "
                f"into {field}."
            )

        except Exception as e:

            return (
                f"Couldn't type into "
                f"{field}: {e}"
            )

    # ========================================================
    # ENTER
    # ========================================================

    def press_enter(self):

        self.ensure_connection()

        try:

            active = (
                self.driver.switch_to
                .active_element
            )

            active.send_keys(
                Keys.ENTER
            )

            self.wait_for_page()

            return "Pressed Enter."

        except Exception:

            element = self.find_input(
                "search"
            )

            if element is None:

                return (
                    "I couldn't find "
                    "an input for 'search'."
                )

            try:

                element.send_keys(
                    Keys.ENTER
                )

                self.wait_for_page()

                return "Pressed Enter."

            except Exception as e:

                return (
                    f"Couldn't press Enter: {e}"
                )

    # ========================================================
    # SCROLL
    # ========================================================

    def scroll_down(self):

        self.ensure_connection()

        self.driver.execute_script(
            "window.scrollBy(0, 650);"
        )

        return "Scrolled down."

    def scroll_up(self):

        self.ensure_connection()

        self.driver.execute_script(
            "window.scrollBy(0, -650);"
        )

        return "Scrolled up."

    # ========================================================
    # NAVIGATION
    # ========================================================

    def back(self):

        self.ensure_connection()

        self.driver.back()

        self.wait_for_page()

        return "Went back."

    def forward(self):

        self.ensure_connection()

        self.driver.forward()

        self.wait_for_page()

        return "Went forward."

    def refresh(self):

        self.ensure_connection()

        self.driver.refresh()

        self.wait_for_page()

        return "Page refreshed."

    # ========================================================
    # PAGE INFO
    # ========================================================

    def get_title(self):

        self.ensure_connection()

        return self.driver.title

    def get_url(self):

        self.ensure_connection()

        return self.driver.current_url

    def get_visible_text(self):

        self.ensure_connection()

        try:

            element = self.driver.find_element(
                By.TAG_NAME,
                "body"
            )

            return element.text[:12000]

        except Exception as e:

            return (
                f"Couldn't read page: {e}"
            )

    # ========================================================
    # SCREENSHOT
    # ========================================================

    def screenshot(
        self,
        filename=None
    ):

        self.ensure_connection()

        if filename is None:

            filename = os.path.expanduser(
                "~/roborabbit/screenshots/firefox.png"
            )

        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        self.driver.save_screenshot(
            filename
        )

        return filename

    def click_second_youtube_result(
        self
    ):

        self.ensure_connection()

        try:

            WebDriverWait(
                self.driver,
                15
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "a#video-title"
                    )
                )
            )

            videos = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a#video-title"
            )

            visible_videos = []

            for video in videos:

                try:
                    if video.is_displayed():
                        visible_videos.append(video)
                except Exception:
                    continue

            if len(visible_videos) < 2:
                return (
                    "I couldn't find a second "
                    "YouTube video result."
                )

            video = visible_videos[1]

            title = (
                video.get_attribute("title")
                or video.text
                or "second video"
            )

            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center'
                });
                """,
                video
            )

            time.sleep(0.3)

            try:
                video.click()
            except Exception:
                self.driver.execute_script(
                    "arguments[0].click();",
                    video
                )

            self.wait_for_page()

            return (
                "Opened the second "
                f"YouTube result: {title}"
            )

        except Exception as e:

            return (
                f"Couldn't open second "
                f"YouTube result: {e}"
            )


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        if self.driver is not None:

            try:
                self.driver.quit()
            except Exception:
                pass

            self.driver = None

        return "Firefox closed."


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "🦊 Starting RoboRabbit Firefox..."
    )

    browser = FirefoxAgent()

    print(
        browser.search_youtube(
            "Minecraft tutorials"
        )
    )

    print(
        "\nTitle:",
        browser.get_title()
    )

    print(
        "URL:",
        browser.get_url()
    )

    print(
        "\n📜 Page text:\n"
    )

    print(
        browser.get_visible_text()[:3000]
    )

    print(
        "\n✅ Firefox agent test complete."
    )
