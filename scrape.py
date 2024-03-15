import os
import re
import requests
import time
from datetime import datetime


from io import BytesIO
from termcolor import cprint
from PIL import Image, UnidentifiedImageError
from dateutil.parser import parse, ParserError
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By


from common import Paths, Utils


class SiteScraper:

    def __init__(self, driver, site_name, site):
        self.driver = driver
        self.site_name = site_name
        self.date, self.title, self.description, self.tags, self.models = None, None, None, None, None
        self.link_for_trailer, self.link_for_image = None, None
        self.counter_img = 0
        self.counter_vid = 0
        self.scraped_items = {}
        self.config = Utils.load_configs(site)
        self.paths = Paths()

    def scrape_elements(self, *scrape_types):
        """ 
        Scrape elements from the web page based on specified types.

        Parameters:
            *scrape_types (str): Types of elements to scrape.

        Returns:
            dict: Dictionary containing scraped items for each scrape type.
        """
        self.scraped_items = {}
        for scrape_type in scrape_types:
            xpaths = []
            items = []
            elements_found = False
            xpaths_key = self.config.get(f"{scrape_type}_info", {})
            xpaths_block = False
            if scrape_type == "element":
                xpaths = self.config.get(f"{scrape_type}_xpaths", {})
            for location, attributes in xpaths_key.items():
                if location == "home":
                    if isinstance(attributes, dict) and attributes:
                        for attribute, xpaths1 in attributes.items():
                            if not any(xpaths1):
                                continue
                            xpaths = xpaths1
                    elif isinstance(attributes, list) and attributes:
                        if not any(attributes):
                            continue
                        else:
                            xpaths = attributes
                    else:
                        continue

            for xpath in xpaths:
                xpaths_block = True
                if xpath:
                    try:
                        if scrape_type == "element":
                            elements = self.driver.find_elements(
                                By.XPATH, xpath)
                            num_elements = len(elements)
                            cprint(
                                f"Number of elements found: {num_elements}.", "green")
                            if elements:
                                elements_found = True  # Set the flag
                                items.extend(elements)
                                break
                        elif scrape_type == "date":
                            dates = self.driver.find_elements(By.XPATH, xpath)
                            num_elements = len(dates)
                            cprint(
                                f"Number of dates found: {num_elements}.", "green")
                            if dates:
                                elements_found = True
                                items.extend(dates)
                                break
                        elif scrape_type == "title":
                            titles = self.driver.find_elements(By.XPATH, xpath)
                            num_elements = len(titles)
                            cprint(
                                f"Number of titles found: {num_elements}.", "green")
                            if titles:
                                elements_found = True
                                items.extend(titles)
                                break
                        elif scrape_type == "models":
                            models = self.driver.find_elements(By.XPATH, xpath)
                            num_elements = len(models)
                            cprint(
                                f"Number of models found: {num_elements}.", "green")
                            if models:
                                elements_found = True
                                items.extend(models)
                                break
                        elif scrape_type == "image":
                            images = self.driver.find_elements(By.XPATH, xpath)
                            num_elements = len(images)
                            cprint(
                                f"Number of images found: {num_elements}.", "green")
                            if images:
                                elements_found = True
                                items.extend(images)
                                break
                        elif scrape_type == "video":
                            videos = self.driver.find_elements(By.XPATH, xpath)
                            num_elements = len(videos)
                            cprint(
                                f"Number of videos found: {num_elements}.", "green")
                            if videos:
                                elements_found = True
                                items.extend(videos)
                                break
                        elif scrape_type == "site_name":
                            pass
                    except NoSuchElementException:
                        continue

            if xpaths_block and not elements_found:
                cprint(f"No {scrape_type} found.", "red")
            else:
                self.scraped_items[scrape_type] = items

        return self.scraped_items

    def scrape_date(self, date_el=None):
        """
        Scrape and process Date from the web page.

        Returns:
        str: Date.
        """
        date = None
        if date_el:
            date = date_el
        else:
            date_xpaths = []
            xpaths_key = self.config.get("date_info", {})
            for location, xpaths in xpaths_key.items():
                if location == "inside":
                    date_xpaths = xpaths
            for xpath in date_xpaths:
                if xpath == [""]:
                    cprint("No defined date xpath", "red")
                    return None
                if not xpath:
                    return None
                try:
                    date_element = self.driver.find_element(By.XPATH, xpath)
                    date_attribute = self.config.get("date_attribute", [])
                    if date_attribute:
                        try:
                            date = date_element.get_attribute(date_attribute)
                        except WebDriverException as js_exception:
                            print(
                                f"JavascriptException occurred: {js_exception}")
                        date = date_element.get_attribute(date_attribute)
                    else:
                        date = date_element.get_attribute(
                            "textContent").replace('\n', '').strip()
                except NoSuchElementException:
                    continue
        transformations = [
            lambda text: text,  # No transformation
            lambda text: text.replace(
                "Date Added:", "") if "Date Added:" in text else text,
            lambda text: text.replace(
                "Published: ", "") if "Published: " in text else text,
            lambda text: text.replace(
                "PUBLISHED", "") if "PUBLISHED" in text else text,
            lambda text: text.replace(
                "Published", "") if "Published" in text else text,
            lambda text: text.replace(
                "Release Date:", "") if "Release Date:" in text else text,
            lambda text: text.replace(
                "Date:", "") if "Date:" in text else text,
            lambda text: text.replace(
                "Released:", "") if "Released:" in text else text,
            lambda text: text.replace(
                "Added on:", "") if "Added on:" in text else text,
            lambda text: text.replace(
                "Added:", "") if "Added:" in text else text,
            lambda text: text.replace(
                "Added", "") if "Added" in text else text,
            lambda text: text.split('Available')[
                0] if "Available" in text else text,
            lambda text: text.split('Runtime')[
                0] if "Runtime" in text else text,
            lambda text: text.split("|")[0] if "|" in text else text,
            lambda text: text.split("|")[1] if "|" in text else text,
            lambda text: text.split("•")[1] if "•" in text else text,
            lambda text: text.split(":")[1] if ":" in text else text,
            lambda text: text.split("📅")[1] if "📅" in text else text,
            lambda text: text.strip()
        ]

        transform_success = False
        if date:
            for transform in transformations:
                try:
                    date = transform(date)
                    date_format = self.config.get("date_format", [])
                    if date_format:
                        date = datetime.strptime(
                            date, date_format).strftime("%b %d, %Y")
                    else:
                        date = parse(date).strftime("%b %d, %Y")
                    cprint("Date element found.", "green")
                    self.date = date
                    transform_success = True
                    break
                except (ParserError, ValueError):
                    continue

            if not transform_success:
                cprint("Parsing error.", "red")

            if not self.date:
                cprint("No date found.", "red")

        return self.date

    def scrape_title(self, title_el=None):
        """
        Scrape and process Title from the web page.

        Returns:
        str: Title.
        """
        if title_el:
            self.title = title_el
        else:
            title_xpaths = []
            xpaths_key = self.config.get("title_info", {})
            for location, xpaths in xpaths_key.items():
                if location == "inside":
                    title_xpaths = xpaths
            for xpath in title_xpaths:
                if xpath == [""]:
                    cprint("No defined title xpath", "red")
                    return None
                if not xpath:
                    return None
                try:
                    title_element = self.driver.find_element(By.XPATH, xpath)
                    self.title = title_element.get_attribute(
                        "textContent").replace('\n', '').strip().title()
                    cprint("Title element found.", "green")
                    break
                except NoSuchElementException:
                    continue

            if not self.title:
                cprint("No title found.", "red")

        return self.title

    def scrape_description(self):
        """
        Scrape and process Description from the web page.

        Returns:
        str: Description.
        """
        description_xpaths = self.config.get("description_xpaths", [])
        if description_xpaths == [""]:
            cprint("No defined description xpath", "red")
            return None
        if not description_xpaths:
            return None

        for xpath in description_xpaths:
            try:
                description_element = self.driver.find_element(By.XPATH, xpath)
                text = description_element.get_attribute("textContent")
                text = text.replace('\n', '').strip()
                text = text.replace("Synopsis", "").strip()
                text = text.replace("DESCRIPTION:", "").strip()
                text = text.replace("Description:", "").strip()
                text = text.replace("Episode Summary", "").strip()
                if text.strip():
                    self.description = text
                    cprint("Description element found.", "green")
                    return self.description
            except NoSuchElementException:
                continue

        cprint("No description found.", "red")
        return None

    def scrape_tags(self):
        """
        Scrape and process tags from the web page.

        Returns:
        list: A list of scraped tags.
        """
        tags_xpaths = self.config.get("tags_xpaths", [])
        if tags_xpaths == [""]:
            cprint("No defined tags xpath", "red")
            return None
        if not tags_xpaths:
            return None

        for xpath in tags_xpaths:
            try:
                tags_elements = self.driver.find_elements(By.XPATH, xpath)
                num_tags_elements = len(tags_elements)
                cprint(f"Number of tags found: {num_tags_elements}.", "green")
                if not tags_elements:
                    raise NoSuchElementException
                tags_names = [tag.get_attribute("textContent").title().replace(
                    ",", "").replace('\n', '').strip() for tag in tags_elements]
                self.tags = ', '.join(tags_names)
                break
            except NoSuchElementException:
                continue

        if not self.tags:
            cprint("No tags found.", "red")

        return self.tags

    def scrape_models(self, models_names=None):
        """
        Scrape and process models from the web page.

        Returns:
        list: A list of scraped models.
        """
        transformations = [
            lambda text: text.title().replace(',', '').strip(),
            lambda text: text.title().replace(',', '').strip().strip("Starring: ") if text.startswith(
                "Starring: ") else text.title().replace(',', '').strip(),
        ]
        if models_names:
            self.models = ', '.join(models_names)
        else:
            xpaths_key = self.config.get("models_info", {})
            for location, models_xpaths in xpaths_key.items():
                if location == "inside":
                    for xpath in models_xpaths:
                        if xpath == [""]:
                            cprint("No defined models xpath", "red")
                            return None
                        if not xpath:
                            return None
                        try:
                            models_elements = self.driver.find_elements(
                                By.XPATH, xpath)
                            num_models_elements = len(models_elements)
                            cprint(
                                f"Number of models found: {num_models_elements}.", "green")
                            if not models_elements:
                                raise NoSuchElementException
                            models_names = []

                            for model in models_elements:
                                # processed_name = model.text # Retrieves the visible text of an element
                                # Retrieves the text content of an element, including hidden or non-visible text
                                processed_name = model.get_attribute(
                                    "textContent")
                                for transform in transformations:
                                    processed_name = transform(processed_name)
                                models_names.append(processed_name)

                            self.models = ', '.join(models_names)
                            break
                        except NoSuchElementException:
                            continue

        if not self.models:
            cprint("No models found.", "red")

        return self.models


class ImageScraper(SiteScraper):

    def image_link_replacements(self, link, replacements):
        """ 
        Perform replacements on the given image link based on the provided replacements.

        Parameters:
            link (str): The original image link.
            replacements (list): List of replacement dictionaries.

        Returns:
            str: The modified image link after replacements.
        """
        for replacement in replacements:
            if link is not None:
                if "split" in replacement and replacement["split"] != "":
                    link = link.split(replacement["split"])[0]
                if "to_replace" in replacement and "replacement" in replacement:
                    link = link.replace(
                        replacement["to_replace"], replacement["replacement"])

        return link

    def save_image(self):
        """ 
        Save the image from the provided link.

        Returns:
            str: Path to the saved image file, or None if saving failed.
        """
        path_image = self.paths.create_image_path(
            self.site_name, self.counter_img)
        response_image = requests.get(self.link_for_image, timeout=120)
        try:
            image = Image.open(BytesIO(response_image.content))
            image = image.convert("RGB")
            image.save(path_image, optimize=True, quality=50)
            if os.path.exists(path_image):
                cprint(f"Image saved at {path_image}.", "yellow")
            else:
                cprint("Failed to save image.", "red")
            self.counter_img += 1
            cprint("Image found.", "green")
        except UnidentifiedImageError:
            cprint("UnidentifiedImageError: Image format not recognized.", "red")
            return None

        return path_image

    def scrape_image_with_xpath(self, image_home=None):
        """ Scrape image link from the web page.

        Parameters:
            image_home (str): Optional link to the image.

        Returns:
            tuple: Tuple containing the scraped image link and the path to the saved image file.
        """
        xpaths_key = self.config.get(f"image_info", {})
        img_inside = None
        image_found = False
        for location, attributes in xpaths_key.items():
            if location == "inside":
                if isinstance(attributes, dict) and attributes:
                    for attribute, image_xpaths in attributes.items():
                        for xpath in image_xpaths:
                            if xpath == [""]:
                                cprint("No defined image xpaths", "red")
                                return None, None
                            if not xpath:
                                return None, None
                            for xpath in image_xpaths:
                                try:
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                except NoSuchElementException:
                                    continue
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    cprint(
                                        "Stale element. Re-finding elements.", "yellow")
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                replace_img_config = self.config.get(
                                    "replace_img_link", {})
                                replacements = replace_img_config.get(
                                    "replacements", [])
                                try:
                                    img_inside = self.image_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    cprint(
                                        "Stale element. Re-finding element.", "yellow")
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                    img_inside = self.image_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)
                                if attribute == "style":
                                    url_pattern = re.compile(r"url\((.+?)\)")
                                    match = re.search(url_pattern, img_inside)
                                    if match:
                                        url = match.group(1)
                                        img_inside = url.strip('"')
                                if img_inside is not None and img_inside != "":
                                    if "https:" not in img_inside:
                                        img_inside = "https://" + \
                                            img_inside.lstrip('/')
                                    if img_inside:
                                        image_found = True
                                        break
                                if img_inside:
                                    image_found = True
                                    break
                                else:
                                    cprint("img_inside is None", "red")
                                    continue
                            if image_found:
                                break
                        if image_found:
                            break

        if img_inside:
            self.link_for_image = img_inside
            path_image = self.save_image()
            return self.link_for_image, path_image
        elif image_home:
            self.link_for_image = image_home
            path_image = self.save_image()
            return self.link_for_image, path_image

        if not self.link_for_image:
            cprint("No image found.", "red")

        return self.link_for_image, None


class VideoScraper(SiteScraper):

    def video_link_replacements(self, link, replacements):
        """ 
        Perform replacements on the given video link based on the provided replacements.

        Parameters:
            link (str): The original video link.
            replacements (list): List of replacement dictionaries.

        Returns:
            str: The modified video link after replacements.
        """
        for replacement in replacements:
            if link is not None:
                if "split" in replacement and replacement["split"] != "":
                    link = link.split(replacement["split"])[0]
                if "to_replace" in replacement and "replacement" in replacement:
                    link = link.replace(
                        replacement["to_replace"], replacement["replacement"])

        return link

    def save_video(self):
        """ 
        Save the video from the provided link.

        Returns:
            str: Path to the saved video file, or None if saving failed.
        """
        path_video = None
        if self.link_for_trailer is not None and self.link_for_trailer.startswith("blob"):
            cprint("Video starts with blob.", "red")
        else:
            path_video = self.paths.create_video_path(
                self.site_name, self.counter_vid)
            response_video = requests.get(self.link_for_trailer, timeout=120)
            with open(path_video, 'wb') as video_file:
                video_file.write(response_video.content)
            if os.path.exists(path_video):
                cprint(f"Trailer saved at {path_video}.", "yellow")
            else:
                cprint("Failed to save trailer.", "red")
            self.counter_vid += 1

        return path_video

    def scrape_video(self, vid_home=None):
        """ Scrape video link from the web page.

        Parameters:
            vid_home (str): Optional link to the video.

        Returns:
            tuple: Tuple containing the scraped video link and the path to the saved video file.
        """
        vid_inside = None
        xpaths_key = self.config.get(f"video_info", {})
        for location, attributes in xpaths_key.items():
            if location == "inside":
                if isinstance(attributes, dict) and attributes:
                    for attribute, video_xpaths in attributes.items():
                        for xpath in video_xpaths:
                            if xpath == [""]:
                                cprint("No defined video xpaths", "red")
                                return None, None
                            if not xpath:
                                return None, None
                            try:
                                link_to_source = self.driver.find_element(
                                    By.XPATH, xpath)
                            except NoSuchElementException:
                                continue
                            except StaleElementReferenceException:
                                time.sleep(3)
                                cprint(
                                    "Stale element. Re-finding elements.", "yellow")
                                link_to_source = self.driver.find_element(
                                    By.XPATH, xpath)
                            replace_vid_config = self.config.get(
                                "replace_vid_link", {})
                            replacements = replace_vid_config.get(
                                "replacements", [])
                            try:
                                vid_inside = self.video_link_replacements(
                                    link_to_source.get_attribute(attribute), replacements)
                            except StaleElementReferenceException:
                                time.sleep(3)
                                cprint(
                                    "Stale element. Re-finding elements.", "yellow")
                                link_to_source = self.driver.find_element(
                                    By.XPATH, xpath)
                                vid_inside = self.video_link_replacements(
                                    link_to_source.get_attribute(attribute), replacements)
                            if attribute == "onclick":
                                url_pattern = re.compile(r"tload\('(.+?)'\); ")
                                match = re.search(url_pattern, vid_inside)
                                if match:
                                    vid_inside = match.group(1)
                            if not vid_inside:
                                cprint("vid_inside is None.", "red")
                                continue
                            if "https:" not in vid_inside:
                                vid_inside = "https://"+vid_inside.lstrip('/')
                            break

        if vid_inside and not vid_inside.startswith("blob"):
            self.link_for_trailer = vid_inside
            path_video = self.save_video()
            cprint("Video found.", "green")
            return self.link_for_trailer, path_video
        elif vid_home:
            self.link_for_trailer = vid_home
            path_video = self.save_video()
            cprint("Video found.", "green")
            return self.link_for_trailer, path_video

        if not self.link_for_trailer:
            cprint("No video found.", "red")

        return self.link_for_trailer, None
