import time

from termcolor import cprint
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


from common import Utils


class InteractWithButtons:

    def __init__(self, driver, site_name):
        self.driver = driver
        self.xpaths = Utils.load_configs(site_name)

    def enter_button(self):
        """
        Interact with enter button.
        """
        enter_btt_xpaths = self.xpaths.get("enter_button", [])
        if enter_btt_xpaths == [""]:
            cprint("No defined enter_button xpath", "red")
            return None
        if not enter_btt_xpaths:
            return None

        for xpath in enter_btt_xpaths:
            try:
                enter = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", enter)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", enter)
                cprint("Entered the site.", "green")
                break
            except NoSuchElementException:
                cprint("No enter button.", "red")
                continue
            except TimeoutException:
                cprint("Enter button timed out.", "red")
                continue
        return None

    def second_enter_button(self):
        """
        Interact with enter button.
        """
        enter_btt_xpaths = self.xpaths.get("second_enter_button", [])
        if enter_btt_xpaths == [""]:
            cprint("No defined second_enter_button xpath", "red")
            return None
        if not enter_btt_xpaths:
            return None

        for xpath in enter_btt_xpaths:
            try:
                enter = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", enter)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", enter)
                cprint("Entered the site.", "green")
                break
            except NoSuchElementException:
                cprint("No enter button.", "red")
                continue
            except TimeoutException:
                cprint("Enter button timed out.", "red")
                continue
        return None

    def click_video(self):
        """
        Interact with video.
        """
        video_btt_xpaths = self.xpaths.get("video_button", [])
        if video_btt_xpaths == [""]:
            cprint("No defined video_button xpath", "red")
            return None
        if not video_btt_xpaths:
            return None

        for xpath in video_btt_xpaths:
            try:
                video = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                try:
                    video.click()
                except WebDriverException:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView();", video)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", video)
                    time.sleep(3)
                cprint("Video clicked.", "green")
                break
            except NoSuchElementException:
                cprint("No video button.", "red")
                continue
            except TimeoutException:
                cprint("Video button timed out.", "red")
                continue
            except ElementNotInteractableException:
                cprint("Video button is not interactable.", "red")
                continue
        return None

    def expand_desc_button(self):
        """
        Interact with expand description button.
        """
        expand_btt_xpaths = self.xpaths.get("expand_desc_button", [])
        if expand_btt_xpaths == [""]:
            cprint("No defined expand_desc_button xpath", "red")
            return None
        if not expand_btt_xpaths:
            return None

        for xpath in expand_btt_xpaths:
            try:
                expand = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", expand)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", expand)
                time.sleep(1)
                cprint("Expanded description.", "green")
                break
            except NoSuchElementException:
                cprint("No expand description button.", "red")
                continue
            except TimeoutException:
                cprint("Expand description button timed out.", "red")
                continue
        return None

    def expand_tags_button(self):
        """
        Interact with expand tags button.
        """
        expand_btt_xpaths = self.xpaths.get("expand_tags_button", [])
        if expand_btt_xpaths == [""]:
            cprint("No defined expand_tags_button xpath", "red")
            return None
        if not expand_btt_xpaths:
            return None

        for xpath in expand_btt_xpaths:
            try:
                expand_tags = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView();", expand_tags)
                time.sleep(0.5)
                self.driver.execute_script(
                    "arguments[0].click();", expand_tags)
                time.sleep(1)
                cprint("Expanded tags.", "green")
                break
            except NoSuchElementException:
                cprint("No expand tags button.", "red")
                continue
            except TimeoutException:
                cprint("Expand tags button timed out.", "red")
                continue
        return None

    def ad_button(self):
        """
        Interact with ad button.
        """
        ad_btt_xpaths = self.xpaths.get("ad_button", [])
        if ad_btt_xpaths == [""]:
            cprint("No defined ad_button xpath", "red")
            return None
        if not ad_btt_xpaths:
            return None
        while True:
            for xpath in ad_btt_xpaths:
                try:
                    click_ad = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, xpath)))
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView();", click_ad)
                    time.sleep(0.5)
                    self.driver.execute_script(
                        "arguments[0].click();", click_ad)
                    cprint("Ad button clicked.", "green")
                    continue
                except NoSuchElementException:
                    cprint("No ad button.", "red")
                    continue
                except TimeoutException:
                    continue
