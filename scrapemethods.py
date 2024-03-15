import time


from termcolor import cprint
from itertools import zip_longest
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import concurrent.futures


from common import Paths, Utils, DataFrames
from scrape import SiteScraper, ImageScraper, VideoScraper
from buttons import InteractWithButtons


class Methods:
    def __init__(self):
        self.paths = Paths()
        self.data_frames = DataFrames()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.data = []

    def method_1(self, site):
        self.data = []

        start_time = Utils.start_time()
        cprint(f"{site} started executing at {Utils.get_current_time()}", "blue")

        config = Utils.load_configs(site)
        url = config.get("site")
        headless = config.get("headless")
        driver = Utils.setup_chrome_driver(headless=headless)
        actions = ActionChains(driver)
        driver.get(url)
        driver.implicitly_wait(5)

        site_name = Utils.extract_site_name(url)
        result = self.data_frames.save_dataframe_with_retry(
            self.data, "site", site_name)
        link_from_excel = [] if result is not None else []
        title_from_excel = [] if result is not None else []
        if result is not None:
            link_from_excel = result['Link for video'].tolist()
            title_from_excel = result['Title'].tolist()

        buttons = InteractWithButtons(driver, site_name)
        buttons.enter_button()
        buttons.second_enter_button()
        if not driver.current_url == url:
            driver.get(url)

        self.executor.submit(buttons.ad_button)
        scrape, scrape_image, scrape_video = SiteScraper(driver, site_name, site), ImageScraper(
            driver, site_name, site), VideoScraper(driver, site_name, site)
        scraped_items = scrape.scrape_elements(
            "element", "date", "title", "models", "image", "video")
        lists = {
            "element": scraped_items.get("element", []),
            "date": scraped_items.get("date", []),
            "title": scraped_items.get("title", []),
            "models": scraped_items.get("models", []),
            "image": scraped_items.get("image", []),
            "video": scraped_items.get("video", [])
        }

        href, date_el, title_el, models_el, models_names, image_home, vid_home = None, None, None, None, None, None, None
        for items in zip_longest(*lists.values()):
            for key, item in zip(lists.keys(), items):
                if item is None:
                    continue
                if key == "element":
                    href = item.get_attribute("href")
                    if href.startswith("https://join."):
                        continue
                    if "?" in href:
                        href = href.split("?")[0]
            if href:
                if href.endswith(".com/join"):
                    for key, item in zip(lists.keys(), items):
                        if item is None:
                            continue
                        if key == "title":
                            title_el = item.get_attribute(
                                "textContent").strip().title()
                    if title_el not in title_from_excel:
                        for key, item in zip(lists.keys(), items):
                            if item is None:
                                continue
                            if key == "date":
                                date_el = item.text.strip()
                            elif key == "models":
                                for location, attributes in config.get("models_info", {}).items():
                                    if location == "home":
                                        if isinstance(attributes, dict) and attributes:
                                            for xpath, _ in attributes.items():
                                                transformations = [
                                                    lambda text: text.title().replace(',', '').strip(),
                                                    lambda text: text.title().replace(',', '').strip().strip("Starring: ") if text.startswith(
                                                        "Starring: ") else text.title().replace(',', '').strip(),
                                                ]
                                                models_el = item.find_elements(
                                                    By.XPATH, xpath)
                                                models_names = []
                                                for model in models_el:
                                                    processed_name = model.get_attribute(
                                                        "textContent")
                                                    for transform in transformations:
                                                        processed_name = transform(
                                                            processed_name)
                                                    models_names.append(
                                                        processed_name)
                                        elif location == "inside":
                                            continue
                                    else:
                                        pass
                            elif key == "image":
                                for location, attributes in config.get("image_info", {}).items():
                                    if location == "home":
                                        if isinstance(attributes, dict) and attributes:
                                            for attribute, _ in attributes.items():
                                                replace_img_config = config.get(
                                                    "replace_img_link", {})
                                                replacements = replace_img_config.get(
                                                    "replacements", [])
                                                for replacement in replacements:
                                                    if "split" in replacement and replacement["split"] != "":
                                                        image_home = item.get_attribute(
                                                            attribute).split(replacement["split"])[0]
                                                    if "to_replace" in replacement and "replacement" in replacement:
                                                        image_home = item.get_attribute(attribute).replace(
                                                            replacement["to_replace"], replacement["replacement"])
                                                    else:
                                                        image_home = item.get_attribute(
                                                            attribute)
                            elif key == "video":
                                for location, attributes in config.get("video_info", {}).items():
                                    if location == "home":
                                        if isinstance(attributes, dict) and attributes:
                                            for attribute, _ in attributes.items():
                                                move_to_video = config.get(
                                                    "move_to_video")
                                                mtv_xpath = config.get(
                                                    "mtv_xpath")
                                                if move_to_video:
                                                    time.sleep(2)
                                                    driver.execute_script(
                                                        "arguments[0].scrollIntoView();", item)
                                                    time.sleep(1)
                                                    driver.execute_script(
                                                        "window.scrollBy(0, -200);")
                                                    time.sleep(1)
                                                    actions.move_to_element(
                                                        item).perform()
                                                    time.sleep(2)
                                                if mtv_xpath:
                                                    mtv = item.find_element(
                                                        By.XPATH, mtv_xpath)
                                                else:
                                                    mtv = item
                                                if mtv:
                                                    replace_vid_config = config.get(
                                                        "replace_vid_link", {})
                                                    replacements = replace_vid_config.get(
                                                        "replacements", [])
                                                    for replacement in replacements:
                                                        if "split" in replacement and replacement["split"] != "":
                                                            vid_home = mtv.get_attribute(
                                                                attribute).split(replacement["split"])[0]
                                                        if "to_replace" in replacement and "replacement" in replacement:
                                                            vid_home = mtv.get_attribute(attribute).replace(
                                                                replacement["to_replace"], replacement["replacement"])
                                                        else:
                                                            vid_home = mtv.get_attribute(
                                                                attribute)
                                                if vid_home is not None:
                                                    if vid_home.startswith("blob"):
                                                        cprint(
                                                            "Video starts with blob.", "red")
                                                    elif "https:" not in vid_home:
                                                        vid_home = "https://" + \
                                                            vid_home.lstrip(
                                                                '/')
                                                else:
                                                    cprint(
                                                        "vid_home is None.", "red")
                        tags, description = None, None
                        link_to_src_image, path_image = scrape_image.scrape_image_with_xpath(
                            image_home)
                        link_for_trailer, path_video = scrape_video.scrape_video(
                            vid_home)
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
                elif href not in link_from_excel:
                    for key, item in zip(lists.keys(), items):
                        if item is None:
                            continue
                        if key == "date":
                            date_el = item.text.strip()
                        elif key == "title":
                            title_el = item.get_attribute(
                                "textContent").strip().title()
                        elif key == "models":
                            for location, attributes in config.get("models_info", {}).items():
                                if location == "home":
                                    if isinstance(attributes, dict) and attributes:
                                        for xpath, _ in attributes.items():
                                            transformations = [
                                                lambda text: text.title().replace(',', '').strip(),
                                                lambda text: text.title().replace(',', '').strip().strip("Starring: ") if text.startswith(
                                                    "Starring: ") else text.title().replace(',', '').strip(),
                                            ]
                                            models_el = item.find_elements(
                                                By.XPATH, xpath)
                                            models_names = []
                                            for model in models_el:
                                                # processed_name = model.text #This retrieves the visible text of an element
                                                # This retrieves the text content of an element, including hidden or non-visible text
                                                processed_name = model.get_attribute(
                                                    "textContent")
                                                for transform in transformations:
                                                    processed_name = transform(
                                                        processed_name)
                                                models_names.append(
                                                    processed_name)
                                    elif location == "inside":
                                        continue
                                else:
                                    pass
                        elif key == "image":
                            for location, attributes in config.get("image_info", {}).items():
                                if location == "home":
                                    if isinstance(attributes, dict) and attributes:
                                        for attribute, _ in attributes.items():
                                            replace_img_config = config.get(
                                                "replace_img_link", {})
                                            replacements = replace_img_config.get(
                                                "replacements", [])
                                            for replacement in replacements:
                                                if "split" in replacement and replacement["split"] != "":
                                                    image_home = item.get_attribute(
                                                        attribute).split(replacement["split"])[0]
                                                if "to_replace" in replacement and "replacement" in replacement:
                                                    image_home = item.get_attribute(attribute).replace(
                                                        replacement["to_replace"], replacement["replacement"])
                                                else:
                                                    image_home = item.get_attribute(
                                                        attribute)
                        elif key == "video":
                            for location, attributes in config.get("video_info", {}).items():
                                if location == "home":
                                    if isinstance(attributes, dict) and attributes:
                                        for attribute, _ in attributes.items():
                                            move_to_video = config.get(
                                                "move_to_video")
                                            mtv_xpath = config.get("mtv_xpath")
                                            if move_to_video:
                                                time.sleep(2)
                                                driver.execute_script(
                                                    "arguments[0].scrollIntoView();", item)
                                                time.sleep(1)
                                                driver.execute_script(
                                                    "window.scrollBy(0, -200);")
                                                time.sleep(1)
                                                actions.move_to_element(
                                                    item).perform()
                                                time.sleep(2)
                                            if mtv_xpath:
                                                mtv = item.find_element(
                                                    By.XPATH, mtv_xpath)
                                            else:
                                                mtv = item
                                            if mtv:
                                                replace_vid_config = config.get(
                                                    "replace_vid_link", {})
                                                replacements = replace_vid_config.get(
                                                    "replacements", [])
                                                for replacement in replacements:
                                                    if "split" in replacement and replacement["split"] != "":
                                                        vid_home = mtv.get_attribute(
                                                            attribute).split(replacement["split"])[0]
                                                    if "to_replace" in replacement and "replacement" in replacement:
                                                        vid_home = mtv.get_attribute(attribute).replace(
                                                            replacement["to_replace"], replacement["replacement"])
                                                    else:
                                                        vid_home = mtv.get_attribute(
                                                            attribute)
                                            if vid_home is not None:
                                                if vid_home.startswith("blob"):
                                                    cprint(
                                                        "Video starts with blob.", "red")
                                                elif "https:" not in vid_home:
                                                    vid_home = "https://" + \
                                                        vid_home.lstrip('/')
                                            else:
                                                cprint(
                                                    "vid_home is None.", "red")
                    main_window = driver.current_window_handle
                    if href not in link_from_excel:
                        driver.execute_script(
                            f"window.open('{href}', '_blank');")
                        windows = driver.window_handles
                        for window in windows:
                            if window != main_window:
                                driver.switch_to.window(window)
                                link_to_src_image, path_image = scrape_image.scrape_image_with_xpath(
                                    image_home)
                                buttons.click_video()
                                link_for_trailer, path_video = scrape_video.scrape_video(
                                    vid_home)
                                gobackvp = config.get("gobackvp")
                                if gobackvp:
                                    driver.execute_script(
                                        "window.history.go(-1)")
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

        self.data_frames.save_dataframe_with_retry(self.data, "daily")
        self.data_frames.save_dataframe_with_retry(
            self.data, "site", site_name)

        end_time = Utils.end_time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
