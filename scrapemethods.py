import time
import requests


from lxml import html
from itertools import zip_longest
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import concurrent.futures


from common import Utils
from scrape import SiteScraper, ImageScraper, VideoScraper
from buttons import InteractWithButtons
from exceptions_handling import RequestsHandling


def extract_href_data(item, config):
    """
    Extracts the href attribute from an HTML element.

    Args:
    - item (WebElement or Element): The HTML element to extract the href attribute from.
    - config (dict): Configuration settings for scraping.

    Returns:
    - str: The value of the href attribute.
    """
    method = config.get("scrape_method")
    if method == "method_selenium":
        href = item.get_attribute(config.get("elements_attribute"))
    elif method == "method_lxml":
        href = item.get(config.get("elements_attribute"))

    return href

def extract_title_data(item, config):
    """
    Extracts the title data from an HTML element.

    Args:
    - item (WebElement or Element): The HTML element to extract title data from.
    - config (dict): Configuration settings for scraping.

    Returns:
    - str: The extracted title data.
    """
    method = config.get("scrape_method")
    if method == "method_selenium":
        title_el = item.get_attribute("textContent").strip().title()
    elif method == "method_lxml":
        title_el = item.text_content().strip().title()

    return title_el

def extract_date_data(item, config):
    """
    Extracts the date data from an HTML element.

    Args:
    - item (WebElement or Element): The HTML element to extract date data from.
    - config (dict): Configuration settings for scraping.

    Returns:
    - str: The extracted date data.
    """
    method = config.get("scrape_method")
    if method == "method_selenium":
        date_el = item.get_attribute("textContent").strip().title()
    elif method == "method_lxml":
        date_el = item.text_content().strip()

    return date_el

def extract_models_data(item, config):
    """
    Extracts model names from the given item based on the provided configuration.

    Args:
    - item (WebElement or Element): The element to extract model names from.
    - config (dict): Configuration settings for scraping.

    Returns:
    - list: A list of model names extracted from the item.
    """
    method = config.get("scrape_method")
    for location, attributes in config.get("models_info", {}).items():
        if location == "home":
            if isinstance(attributes, dict) and attributes:
                for xpath, _ in attributes.items():
                    transformations = [
                        lambda text: text.title().replace(',', '').strip(),
                        lambda text: text.title().replace(',', '').strip().strip("Starring: ") if text.startswith("Starring: ") else text.title().replace(',', '').strip(),
                    ]
                    if method == "method_selenium":
                        models_el = item.find_elements(By.XPATH, xpath)
                        models_names = []
                        for model in models_el:
                            processed_name = model.get_attribute("textContent")
                            for transform in transformations:
                                processed_name = transform(processed_name)
                            models_names.append(processed_name)
                    elif method == "method_lxml":
                        models_el = item.xpath(xpath)
                        models_names = []
                        for model in models_el:
                            processed_name = model.text_content().strip()
                            for transform in transformations:
                                processed_name = transform(processed_name)
                            models_names.append(processed_name)

    return models_names

def extract_image_data(scrape_image, item, config):
    """
    Extracts image data from the given item based on the provided configuration.

    Args:
    - scrape_image (Image scraper): The Image scrapping function used for scraping images.
    - item (WebElement or Element): The element containing image data.
    - config (dict): Configuration settings for scraping.

    Returns:
    - str: The link to the image source.
    """
    replacements = config.get("replace_vid_link", {}).get("replacements", [])
    method = config.get("scrape_method")
    for location, attributes in config.get("image_info", {}).items():
        if location == "home":
            if isinstance(attributes, dict) and attributes:
                for attribute, _ in attributes.items():
                    if method == "method_selenium":
                        image_home_page = scrape_image.image_link_replacements(item.get_attribute(attribute), replacements)
                    elif method == "method_lxml":
                        image_home_page = scrape_image.image_link_replacements(item.get(attribute), replacements)

    return image_home_page

def extract_video_data(scrape_video, item, config, driver=None):
    """
    Extracts video data from the given item based on the provided configuration.

    Args:
    - scrape_video (Video scrapper): The Video scrapping function used for scraping videos.
    - item (WebElement or Element): The element containing video data.
    - config (dict): Configuration settings for scraping.
    - driver (WebDriver, optional): The WebDriver instance. Required if using Selenium.

    Returns:
    - str: The link to the video source.
    """
    replacements = config.get("replace_vid_link", {}).get("replacements", [])
    method = config.get("scrape_method")
    for location, attributes in config.get("video_info", {}).items():
        if location == "home":
            if isinstance(attributes, dict) and attributes:
                for attribute, _ in attributes.items():
                    if method == "method_selenium":
                        move_to_video = config.get("move_to_video")
                        mtv_xpath = config.get("mtv_xpath")
                        if move_to_video and driver:
                            actions = ActionChains(driver)
                            time.sleep(2)
                            driver.execute_script("arguments[0].scrollIntoView();", item)
                            time.sleep(1)
                            driver.execute_script("window.scrollBy(0, -200);")
                            time.sleep(1)
                            actions.move_to_element(item).perform()
                            time.sleep(2)
                        if mtv_xpath:
                            mtv = item.find_element(By.XPATH, mtv_xpath)
                        else:
                            mtv = item
                        if mtv:
                            vid_home_page = scrape_video.video_link_replacements(mtv.get_attribute(attribute), replacements)
                    elif method == "method_lxml":
                        vid_home_page = scrape_video.video_link_replacements(item.get(attribute), replacements)

    return vid_home_page


class Methods:

    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def _initialize_scrapers(self, site_name, site, driver=None, tree=None):
        """
        This function initializes the scrapers needed for scraping the website.
        
        Args:
            site_name (str): The name of the website being scraped.
            site (str): The URL of the website being scraped.
            driver (WebDriver, optional): An optional WebDriver object used for selenium scraping.
            tree (Tree, optional): An optional Tree object used for lxml scraping.
                                    
        Returns:
            tuple: A tuple containing initialized scrapers.
                - scrape (SiteScraper): A SiteScraper object used for scraping the main site.
                - image_scraper (ImageScraper): An ImageScraper object used for scraping images.
                - video_scraper (VideoScraper): A VideoScraper object used for scraping videos.
        """
        scrape = SiteScraper(site_name, site, driver=driver, tree=tree)
        image_scraper = ImageScraper(site_name, site, driver=driver)
        video_scraper = VideoScraper(site_name, site, driver=driver)

        return scrape, image_scraper, video_scraper

    def _scrape_items(self, scrape, *args):
        """
        This function scrapes elements from a website using the initialized scrapers.
        
        Args:
            scrape (SiteScraper): A SiteScraper object used for scraping the main site.
            *args: Variable-length positional arguments specifying the elements to scrape.
            
        Returns:
            dict: A dictionary containing scraped elements.
        """
        return scrape.scrape_elements(*args)

    def method_selenium(self, site):
        """
        Performs web scraping using Selenium for the given site.

        Args:
        - self: Instance of the class.
        - site (str): The name of the site to be scraped.

        Returns:
        - None
        """
        self.data = []

        config = Utils.load_configs(site)

        start_time = Utils.log_start_time(site)

        url_site, site_name = Utils.load_site_config(site)

        link_from_excel, title_from_excel = Utils().get_existing_data(site_name)

        driver = Utils.setup_chrome_driver(headless=config.get("headless"))
        driver.get(url_site)
        driver.implicitly_wait(5)

        buttons = InteractWithButtons(driver, site_name)
        buttons.enter_button()
        buttons.second_enter_button()

        if not driver.current_url == url_site:
            driver.get(url_site)

        self.executor.submit(buttons.ad_button)

        scrape, scrape_image, scrape_video = self._initialize_scrapers(site_name, site, driver=driver)
        scraped_items = self._scrape_items(scrape, "element", "date", "title", "models", "image", "video")

        href, date_el, title_el, models_names, image_home_page, vid_home_page = None, None, None, None, None, None
        for items in zip_longest(*scraped_items.values()):
            for key, item in zip(scraped_items.keys(), items):
                if item is None:
                    continue
                if key == "element":
                    href = extract_href_data(item, config)
                    if href.startswith("https://join."):
                        continue
                    if "?" in href:
                        href = href.split("?")[0]
                elif key == "title":
                    title_el = extract_title_data(item, config)
            if href and href.endswith(".com/join") and title_el not in title_from_excel:
                for key, item in zip(scraped_items.keys(), items):
                    if item is None:
                        continue
                    if key == "date":
                        date_el = extract_date_data(item, config)
                    elif key == "models":
                        models_names = extract_models_data(item, config)
                    elif key == "image":
                        image_home_page = extract_image_data(scrape_image, item, config)
                    elif key == "video":
                        vid_home_page = extract_video_data(scrape_video, item, config, driver=driver)
                tags, description = None, None
                link_to_src_image, path_image = scrape_image.scrape_image(image_home_page)
                link_for_trailer, path_video = scrape_video.scrape_video(vid_home_page)
                title = scrape.scrape_title(title_el)
                date = scrape.scrape_date(date_el)
                models = scrape.scrape_models(models_names)
                self.data.append([
                    site_name or '-',
                    date or '-',
                    title or '-',
                    description or '-',
                    tags or '-',
                    models or '-',
                    link_for_trailer or '-',
                    href or '-',
                    link_to_src_image or '-',
                    path_image or '-',
                    path_video or '-'
                ])
            elif all(href not in link for link in link_from_excel):
                for key, item in zip(scraped_items.keys(), items):
                    if item is None:
                        continue
                    if key == "date":
                        date_el = extract_date_data(item, config)
                    elif key == "title":
                        title_el = extract_title_data(item, config)
                    elif key == "models":
                        models_names = extract_models_data(item, config)
                    elif key == "image":
                        image_home_page = extract_image_data(
                            scrape_image, item, config)
                    elif key == "video":
                        vid_home_page = extract_video_data(scrape_video, item, config, driver=driver)
                main_window = driver.current_window_handle
                driver.execute_script(f"window.open('{href}', '_blank');")
                windows = driver.window_handles
                for window in windows:
                    if window != main_window:
                        driver.switch_to.window(window)
                        link_to_src_image, path_image = scrape_image.scrape_image(
                            image_home_page)
                        buttons.click_video()
                        link_for_trailer, path_video = scrape_video.scrape_video(vid_home_page)
                        gobackvp = config.get("gobackvp")
                        if gobackvp:
                            driver.execute_script("window.history.go(-1)")
                        buttons.expand_desc_button()
                        title = scrape.scrape_title(title_el)
                        date = scrape.scrape_date(date_el)
                        description = scrape.scrape_description()
                        buttons.expand_tags_button()
                        tags = scrape.scrape_tags()
                        models = scrape.scrape_models(models_names)
                        self.data.append([
                            site_name or '-',
                            date or '-',
                            title or '-',
                            description or '-',
                            tags or '-',
                            models or '-',
                            link_for_trailer or '-',
                            href or '-',
                            link_to_src_image or '-',
                            path_image or '-',
                            path_video or '-'
                        ])
                        driver.close()
                        driver.switch_to.window(main_window)

        self.executor.shutdown(wait=False)
        driver.quit()

        Utils.save_scraped_data(self.data, site_name)
        Utils.log_elapsed_time(start_time, site)

    def method_lxml(self, site):
        """
        Performs web scraping using requests and lxml for the given site.

        Args:
        - self: Instance of the class.
        - site (str): The name of the site to be scraped.

        Returns:
        - None
        """
        self.data = []

        config = Utils.load_configs(site)

        start_time = Utils.log_start_time(site)

        url_site, site_name = Utils.load_site_config(site)

        link_from_excel, title_from_excel = Utils.get_existing_data(site_name)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8',
        }
        response = requests.get(url_site, headers=headers)
        if response.status_code == 200:
            html_content = response.content
            tree = html.fromstring(html_content)
            scrape, scrape_image, scrape_video = self._initialize_scrapers(site_name, site, tree=tree)
            scraped_items = self._scrape_items(scrape, "element", "date", "title", "models", "image", "video")

        href, date_el, title_el, models_names, image_home_page, vid_home_page = None, None, None, None, None, None
        for items in zip_longest(*scraped_items.values()):
            for key, item in zip(scraped_items.keys(), items):
                if item is None:
                    continue
                if key == "element":
                    href = extract_href_data(item, config)
                    if href.startswith("https://join."):
                        continue
                    if "?" in href:
                        href = href.split("?")[0]
                elif key == "title":
                    title_el = extract_title_data(item, config)
            if href and href.endswith(".com/join") and title_el not in title_from_excel:
                for key, item in zip(scraped_items.keys(), items):
                    if item is None:
                        continue
                    if key == "date":
                        date_el = extract_date_data(item, config)
                    elif key == "models":
                        models_names = extract_models_data(item, config)
                    elif key == "image":
                        image_home_page = extract_image_data(scrape_image, item, config)
                    elif key == "video":
                        vid_home_page = extract_video_data(scrape_video, item, config)
                tags, description = None, None
                link_to_src_image, path_image = scrape_image.scrape_image(image_home_page)
                link_for_trailer, path_video = scrape_video.scrape_video(vid_home_page)
                title = scrape.scrape_title(title_el)
                date = scrape.scrape_date(date_el)
                models = scrape.scrape_models(models_names)
                self.data.append([
                    site_name or '-',
                    date or '-',
                    title or '-',
                    description or '-',
                    tags or '-',
                    models or '-',
                    link_for_trailer or '-',
                    href or '-',
                    link_to_src_image or '-',
                    path_image or '-',
                    path_video or '-'
                ])
            elif all(href not in link for link in link_from_excel):
                for key, item in zip(scraped_items.keys(), items):
                    if item is None:
                        continue
                    if key == "date":
                        date_el = extract_date_data(item, config)
                    elif key == "title":
                        title_el = extract_title_data(item, config)
                    elif key == "models":
                        models_names = extract_models_data(item, config)
                    elif key == "image":
                        image_home_page = extract_image_data(scrape_image, item, config)
                    elif key == "video":
                        vid_home_page = extract_video_data(scrape_video, item, config)
                response, href = RequestsHandling(url_site, href).main()
                if response:
                    inner_html_content = response.content
                inner_tree = html.fromstring(inner_html_content)
                link_to_src_image, path_image = scrape_image.scrape_image(image_home_page, inner_tree=inner_tree)
                link_for_trailer, path_video = scrape_video.scrape_video(vid_home_page, inner_tree=inner_tree)
                title = scrape.scrape_title(title_el, inner_tree=inner_tree)
                date = scrape.scrape_date(date_el, inner_tree=inner_tree)
                description = scrape.scrape_description(inner_tree=inner_tree)
                tags = scrape.scrape_tags(inner_tree=inner_tree)
                models = scrape.scrape_models(models_names, inner_tree=inner_tree)
                self.data.append([
                    site_name or '-',
                    date or '-',
                    title or '-',
                    description or '-',
                    tags or '-',
                    models or '-',
                    link_for_trailer or '-',
                    href or '-',
                    link_to_src_image or '-',
                    path_image or '-',
                    path_video or '-'
                ])

        Utils.save_scraped_data(self.data, site_name)
        Utils.log_elapsed_time(start_time, site)
