import os
import re
import time
from datetime import datetime

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from dateutil.parser import parse, ParserError
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException


from common import Paths, Utils, CustomLogger
from exceptions_handling import RequestsHandling

class SiteScraper:

    def __init__(self, site_name, site, driver = None, tree = None):
        if driver is not None:
            self.driver = driver
        if tree is not None:
            self.tree = tree
        self.site_name = site_name
        self.date, self.title, self.description, self.tags, self.models = None, None, None, None, None
        self.link_for_trailer, self.link_for_image = None, None
        self.counter_img = 0
        self.counter_vid = 0
        self.scraped_items = {}
        self.config = Utils.load_configs(site)
        self.url_site = self.config.get("site")
        self.paths = Paths()
        self.logger = CustomLogger()

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
            method = self.config.get("scrape_method")
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
                    if method == "method_selenium":
                        try:
                            elements = self.driver.find_elements(By.XPATH, xpath)
                        except NoSuchElementException:
                            continue

                    elif method == "method_lxml":
                        elements = self.tree.xpath(xpath)

                    num_elements = len(elements)
                    if elements:
                        elements_found = True
                        items.extend(elements)
                        break


            if xpaths_block and not elements_found:
                if scrape_type == "element":
                    self.logger.log(
                        f"No {scrape_type} found", level='CRITICAL', site=self.site_name)
                else:
                    self.logger.log(
                        f"No {scrape_type} found", level='ERROR', site=self.site_name)
            elif xpaths_block:
                self.logger.log(
                    f"Number of {scrape_type} found: {num_elements}", level='INFO', site=self.site_name)
                self.scraped_items[scrape_type] = items

        return self.scraped_items

    def scrape_date(self, date_el=None, inner_tree=None):
        """
        Scrape and process Date from the web page.

        Returns:
        str: Date.
        """
        date = None
        if inner_tree is not None:
            tree = inner_tree
        method = self.config.get("scrape_method")
        if date_el:
            date = date_el
        else:
            date_xpaths = []
            xpaths_key = self.config.get("date_info", {})
            for location, xpaths in xpaths_key.items():
                if location == "inside":
                    date_xpaths = xpaths
                    if date_xpaths == [""]:
                        self.logger.log("No defined date xpaths",
                                        level='ERROR',
                                        site=self.site_name)
                        return None
                    if not date_xpaths:
                        return None
            for xpath in date_xpaths:
                if method == "method_selenium":
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
                elif method == "method_lxml":
                    date_element = tree.find(xpath)
                    if date_element is not None:
                        date = date_element.text_content().replace('\n', '').strip()
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
        parser_error = None
        value_error = None
        if date is not None:
            for transform in transformations:
                try:
                    date = transform(date)
                    date_format = self.config.get("date_format", [])
                    if date_format:
                        date = datetime.strptime(
                            date, date_format).strftime("%b %d, %Y")
                    else:
                        date = parse(date).strftime("%b %d, %Y")
                    self.logger.log("Date found", level='INFO',
                                    site=self.site_name)
                    self.date = date
                    transform_success = True
                    break
                except ParserError as e:
                    parser_error = e
                except ValueError as e:
                    value_error = e

            if not transform_success:
                if parser_error is not None:
                    self.logger.log("Parsing error",
                                    level='ERROR',
                                    site=self.site_name,
                                    exception=parser_error)
                elif value_error is not None:
                    self.logger.log("Value error",
                                    level='ERROR',
                                    site=self.site_name,
                                    exception=value_error)
            return self.date        
        else:
            self.logger.log("No date found",
                            level='ERROR',
                            site=self.site_name,
                            exception=value_error)
            return None

    def scrape_title(self, title_el=None, inner_tree=None):
        """
        Scrape and process Title from the web page.

        Returns:
        str: Title.
        """
        if inner_tree is not None:
            tree = inner_tree
        method = self.config.get("scrape_method")
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
                    self.logger.log("No defined title xpaths",
                                    level='ERROR',
                                    site=self.site_name)
                    return None
                if not xpath:
                    return None
                if method == "method_selenium":
                    try:
                        title_element = self.driver.find_element(By.XPATH, xpath)
                        self.title = title_element.get_attribute(
                            "textContent").replace('\n', '').strip().title()
                        break
                    except NoSuchElementException:
                        continue
                elif method == "method_lxml":
                    title_element = tree.find(xpath)
                    if title_element is not None:
                        self.title = title_element.text_content().replace('\n', '').strip().title()

        if self.title:
            self.logger.log("Title found", level='INFO',
                            site=self.site_name)
            return self.title
        else:
            self.logger.log("No title found",
                            level='ERROR',
                            site=self.site_name)
            return None

    def scrape_description(self, inner_tree=None):
        """
        Scrape and process Description from the web page.

        Returns:
        str: Description.
        """
        if inner_tree is not None:
            tree = inner_tree
        method = self.config.get("scrape_method")
        description_xpaths = self.config.get("description_xpaths", [])
        if description_xpaths == [""]:
            self.logger.log("No defined description xpaths",
                            level='ERROR',
                            site=self.site_name)
            return None
        if not description_xpaths:
            return None
        text = None
        for xpath in description_xpaths:
            if method == "method_selenium":
                try:
                    description_element = self.driver.find_element(By.XPATH, xpath)
                    text = description_element.get_attribute("textContent")
                except NoSuchElementException:
                    continue

            elif method == "method_lxml":
                description_element = tree.find(xpath)
                if description_element is not None:
                    text = description_element.text_content()

        if text:
            transformations = [
                lambda text: text.replace('\n', ''),
                lambda text: text.replace("Synopsis", ""),
                lambda text: text.replace("DESCRIPTION:", ""),
                lambda text: text.replace("Description:", ""),
                lambda text: text.replace("Episode Summary", ""),
                lambda text: text.strip(),
            ]
            for transform in transformations:
                text = transform(text)

            self.description = text
            self.logger.log("Description found",
                            level='INFO',
                            site=self.site_name)
            return self.description
        else:
            self.logger.log("No description found",
                            level='ERROR',
                            site=self.site_name)
            return None

    def scrape_tags(self, inner_tree=None):
        """
        Scrape and process tags from the web page.

        Returns:
        list: A list of scraped tags.
        """
        if inner_tree is not None:
            tree = inner_tree
        method = self.config.get("scrape_method")
        tags_xpaths = self.config.get("tags_xpaths", [])
        if tags_xpaths == [""]:
            self.logger.log("No defined tags xpaths",
                            level='ERROR',
                            site=self.site_name)
            return None
        if not tags_xpaths:
            return None

        for xpath in tags_xpaths:
            num_tags_elements = []
            if method == "method_selenium":
                try:
                    tags_elements = self.driver.find_elements(By.XPATH, xpath)
                    num_tags_elements = len(tags_elements)
                    if not tags_elements:
                        raise NoSuchElementException
                    tags_names = [tag.get_attribute("textContent").title().replace(",", "").replace('\n', '').strip() for tag in tags_elements]
                    self.tags = ', '.join(tags_names)
                    break
                except NoSuchElementException:
                    continue
            elif method == "method_lxml":
                tags_elements = tree.xpath(xpath)
                num_tags_elements = len(tags_elements)
                if tags_elements:
                    tags_names = [tag.text_content().title().replace(",", "").replace('\n', '').strip() for tag in tags_elements]
                    self.tags = ', '.join(tags_names)

        if not self.tags:
            self.logger.log("No tags found",
                            level='ERROR',
                            site=self.site_name)
        else:
            self.logger.log(f"Number of tags found: {num_tags_elements}",
                            level='INFO',
                            site=self.site_name)

        return self.tags

    def scrape_models(self, models_names=None, inner_tree=None):
        """
        Scrape and process models from the web page.

        Returns:
        list: A list of scraped models.
        """
        transformations = [
            lambda text: text.title().replace(',', '').strip(),
            lambda text: text.title().replace(',', '').strip().strip("Starring: ") if text.startswith("Starring: ") else text.title().replace(',', '').strip(),
        ]

        if inner_tree is not None:
            tree = inner_tree
        xpaths_key = self.config.get(f"image_info", {})
        method = self.config.get("scrape_method")
        num_models_elements = []
        if models_names:
            num_models_elements = len(models_names)
            self.models = ', '.join(models_names)
        else:
            xpaths_key = self.config.get("models_info", {})
            for location, models_xpaths in xpaths_key.items():
                if location == "inside":
                    for xpath in models_xpaths:
                        if xpath == [""]:
                            self.logger.log("No defined models xpaths",
                                            level='ERROR', 
                                            site=self.site_name)
                            return None
                        if not xpath:
                            return None
                        models_names = []
                        if method == "method_selenium":
                            try:
                                models_elements = self.driver.find_elements(By.XPATH, xpath)
                                if not models_elements:
                                    raise NoSuchElementException
                            except NoSuchElementException:
                                continue
                        elif method == "method_lxml":
                            models_elements = tree.xpath(xpath)
                        num_models_elements = len(models_elements)
                        for model in models_elements:
                            if method == "method_selenium":
                                processed_name = model.get_attribute("textContent")
                            elif method == "method_lxml":
                                processed_name = model.text_content()
                            for transform in transformations:
                                processed_name = transform(processed_name)
                            models_names.append(processed_name)
                        self.models = ', '.join(models_names)
                        break


        if not self.models:
            self.logger.log("No models found",
                            level='ERROR',
                            site=self.site_name)
        else:
            self.logger.log(f"Number of models found: {num_models_elements}",
                level='INFO',
                site=self.site_name)
            
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
        path_image = self.paths.create_image_path(self.site_name, self.counter_img)
        response_image, img_inside = RequestsHandling(self.url_site, self.link_for_image).main()
        if response_image:
            try:
                image = Image.open(BytesIO(response_image.content))
                image = image.convert("RGB")
                image.save(path_image, optimize=True, quality=50)
                if os.path.exists(path_image):
                    self.logger.log(
                        f"Image saved at {path_image}.", level='PATH', site=self.site_name)
                else:
                    self.logger.log("Failed to save image",
                                    level='ERROR', site=self.site_name)
                self.counter_img += 1
                self.logger.log("Image saved", level='INFO', site=self.site_name)
            except UnidentifiedImageError as e:
                self.logger.log("UnidentifiedImageError: Image format not recognized.",
                                level='ERROR', site=self.site_name, exception=e)
                return None, None
        return img_inside, path_image

    def scrape_image(self, image_home=None, inner_tree=None):
        """ Scrape image link from the web page.

        Parameters:
            image_home (str): Optional link to the image.

        Returns:
            tuple: Tuple containing the scraped image link and the path to the saved image file.
        """
        if inner_tree is not None:
            tree = inner_tree
        xpaths_key = self.config.get(f"image_info", {})
        method = self.config.get("scrape_method")
        replacements = self.config.get("replace_img_link", {}).get("replacements", [])
        img_inside = None
        image_found = False
        for location, attributes in xpaths_key.items():
            if location == "inside":
                if isinstance(attributes, dict) and attributes:
                    for attribute, image_xpaths in attributes.items():
                        if not image_xpaths and not image_home:
                            return None, None

                        for xpath in image_xpaths:
                            if xpath == [""]:
                                self.logger.log(
                                    "No defined image xpaths", level='ERROR', site=self.site_name)
                                return None, None

                            if method == "method_selenium":
                                try:
                                    link_to_source = self.driver.find_element(By.XPATH, xpath)
                                except NoSuchElementException:
                                    continue
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    self.logger.log(
                                        "Stale element. Re-finding elements.", 
                                        level='WARNING', 
                                        site=self.site_name)
                                    link_to_source = self.driver.find_element(By.XPATH, xpath)
                                try:
                                    img_inside = self.image_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    self.logger.log(
                                        "Stale element. Re-finding elements.",
                                        level='WARNING',
                                        site=self.site_name)
                                    link_to_source = self.driver.find_element(By.XPATH, xpath)
                                    img_inside = self.image_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)

                            elif method =="method_lxml":
                                link_to_source = tree.find(xpath)
                                img_inside = self.image_link_replacements(link_to_source.get(attribute), replacements)

                            if img_inside:
                                if attribute == "style":
                                    url_pattern = re.compile(r"url\((.+?)\)")
                                    match = re.search(url_pattern, img_inside)
                                    if match:
                                        url = match.group(1)
                                        img_inside = url.strip('"')
                            if img_inside is not None and img_inside != "":
                                if img_inside:
                                    image_found = True
                                    break
                            if img_inside:
                                image_found = True
                                break
                            else:
                                self.logger.log(
                                    "img_inside is None", level='ERROR', site=self.site_name)
                                continue
                        if image_found:
                            break
                    if image_found:
                        break
        if img_inside:
            self.link_for_image = img_inside
            self.link_for_image, path_image = self.save_image()
            return self.link_for_image, path_image
        elif image_home:
            self.link_for_image = image_home
            self.link_for_image, path_image = self.save_image()
            return self.link_for_image, path_image

        if not self.link_for_image:
            self.logger.log("No image found", level='CRITICAL',
                            site=self.site_name)

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
                    to_replace = replacement["to_replace"]
                    replacement_str = replacement["replacement"]
                    if replacement_str not in link:
                        link = link.replace(to_replace, replacement_str)
        return link

    def save_video(self):
        """ 
        Save the video from the provided link.

        Returns:
            str: Path to the saved video file, or None if saving failed.
        """
        path_video = None
        if self.link_for_trailer is not None and self.link_for_trailer.startswith("blob"):
            self.logger.log(f"Video starts with blob",
                            level='WARNING', 
                            site=self.site_name)
        else:
            path_video = self.paths.create_video_path(self.site_name, self.counter_vid)
            response_video, vid_inside = RequestsHandling(self.url_site, self.link_for_trailer).main()
            if response_video:
                with open(path_video, 'wb') as video_file:
                    video_file.write(response_video.content)
            if os.path.exists(path_video):
                self.logger.log(
                    f"Trailer saved at {path_video}", level='PATH', site=self.site_name)
            else:
                self.logger.log("Failed to save trailer",
                                level='ERROR', site=self.site_name)
            self.counter_vid += 1

        return vid_inside, path_video

    def scrape_video(self, vid_home_page=None, inner_tree = None):
        """ Scrape video link from the web page.

        Parameters:
            vid_home_page (str): Optional link to the video.

        Returns:
            tuple: Tuple containing the scraped video link and the path to the saved video file.
        """
        if inner_tree is not None:
            tree = inner_tree
        vid_inside = None
        method = self.config.get("scrape_method")
        xpaths_key = self.config.get(f"video_info", {})
        replacements = self.config.get("replace_vid_link", {}).get("replacements", [])
        for location, attributes in xpaths_key.items():
            if location == "inside":
                if isinstance(attributes, dict) and attributes:
                    for attribute, video_xpaths in attributes.items():
                        if not video_xpaths and not vid_home_page:
                            return None, None
                        for xpath in video_xpaths:
                            if xpath == [""]:
                                self.logger.log(
                                    "No defined video xpaths", 
                                    level='CRITICAL', 
                                    site=self.site_name)
                                return None, None

                            if method == "method_selenium":
                                try:
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                except NoSuchElementException:
                                    continue
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    self.logger.log(
                                        "Stale element. Re-finding elements.", level='WARNING', site=self.site_name)
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                try:
                                    vid_inside = self.video_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)
                                except StaleElementReferenceException:
                                    time.sleep(3)
                                    self.logger.log(
                                        "Stale element. Re-finding elements.", level='WARNING', site=self.site_name)
                                    link_to_source = self.driver.find_element(
                                        By.XPATH, xpath)
                                    vid_inside = self.video_link_replacements(
                                        link_to_source.get_attribute(attribute), replacements)

                            elif method =="method_lxml":
                                link_to_source = tree.find(xpath)
                                if link_to_source is not None:
                                    vid_inside = self.video_link_replacements(link_to_source.get(attribute), replacements)
                            if vid_inside:
                                if attribute == "onclick":
                                    patterns = [
                                        r"tload\(['\"]?(https?://[^'\" ]+?)['\"]?,\s*this\);?",
                                        r"tload\('(.+?)'\);?",
                                        r"tload\(['\"]?(https?://.+?)['\"]?,\s*this\);?",
                                        r"tload\(['\"]?(\/[^'\" ]+?)['\"]?,\s*this\);?"
                                    ]
                                    for pattern in patterns:
                                        url_pattern = re.compile(pattern)
                                        match = re.search(url_pattern, vid_inside)
                                        if match:
                                            vid_inside = match.group(1)
                                            break
                            if not vid_inside:
                                self.logger.log("vid_inside is None", level='ERROR', site=self.site_name)
                                continue
                            break

        if vid_inside and not vid_inside.startswith("blob"):
            self.link_for_trailer = vid_inside
            self.link_for_trailer, path_video = self.save_video()
            self.logger.log("Video found", level='INFO', site=self.site_name)
            return self.link_for_trailer, path_video
        elif vid_home_page:
            self.link_for_trailer = vid_home_page
            self.link_for_trailer, path_video = self.save_video()
            self.logger.log("Video found", level='INFO', site=self.site_name)
            return self.link_for_trailer, path_video

        if not self.link_for_trailer:
            self.logger.log("No video found", level='CRITICAL',
                            site=self.site_name)

        return self.link_for_trailer, None
