import os
import re
import json
import time


import pandas as pd
from datetime import datetime
from termcolor import cprint
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Paths:

    def __init__(self):
        self.home_dir = os.path.expanduser("~")
        self.filename = os.path.basename(__file__)  # This is the file name
        self.data_dir = os.path.join(self.home_dir, "Desktop", "Site", "Data")
        self.desktop_dir = os.path.join(
            self.home_dir, self.data_dir, "Data From Scrapers")
        self.image_dir = os.path.join(
            self.home_dir, self.data_dir, "Pictures", "Auto Downloaded")
        self.video_dir = os.path.join(
            self.home_dir, self.data_dir, "Videos", "Auto Downloaded Trailers")
        self.raw_data_dir = os.path.join(
            self.home_dir, self.data_dir, "Raw Data")
        self.daily_scrapped = ""
        self.site_scrapped = ""
        self.schedule_data = ""
        self.create_directories()
        self.date_utils = Utils()

    def set_daily_scrapped(self):
        """
        Set the file path for the daily scrapped data and create an Excel file if it does not exist.

        Returns:
            str: File path for the daily scrapped data Excel file.
        """
        self.daily_scrapped = os.path.join(
            self.raw_data_dir, f"DailyScrapped+{self.date_utils.get_current_date()}.xlsx")

        if not os.path.exists(self.daily_scrapped):
            df = pd.DataFrame(columns=["Site", "Date", "Title", "Description", "Tags", "Models", "Video to embed",
                                       "Link for video", "Link for image", "Path image", "Path video"])
            df.to_excel(self.daily_scrapped, index=False)

        return self.daily_scrapped

    def set_site_scrapped(self, site_name):
        """
        Set the file path for the site scrapped data and create an Excel file if it does not exist.

        Returns:
            str: File path for the site scrapped data Excel file.
        """
        self.site_scrapped = os.path.join(
            self.desktop_dir, f"{site_name}.xlsx")
        if not os.path.exists(self.site_scrapped):
            df = pd.DataFrame(columns=["Site", "Date", "Title", "Description", "Tags", "Models", "Video to embed",
                                       "Link for video", "Link for image", "Path image", "Path video"])
            df.to_excel(self.site_scrapped, index=False)
        return self.site_scrapped

    def set_schedule_dataframe(self):
        """
        Set the file path for the scheduling data Excel file and create it if it does not exist.

        Returns:
            str: File path for the scheduling data Excel file.
        """
        self.schedule_data = os.path.join(
            self.data_dir, "SitesScheduling.xlsx")
        if not os.path.exists(self.schedule_data):
            df = pd.DataFrame()
            df.to_excel(self.schedule_data, index=False)

        return self.schedule_data

    def create_video_path(self, site_name, counter_vid):
        """
        Create a path for a video file based on the site name and video counter.

        Parameters:
            site_name (str): Name of the site.
            counter_vid (int): Counter for the video.

        Returns:
            str: Path for the video file.
        """
        folder_path_video = os.path.join(self.video_dir, site_name)
        if not os.path.exists(folder_path_video):
            os.makedirs(folder_path_video)

        path_video = os.path.join(
            folder_path_video, f"{self.date_utils.get_current_datetime()}-{counter_vid}.mp4")

        return path_video

    def create_image_path(self, site_name, counter_img):
        """
        Create a path for a image file based on the site name and image counter.

        Parameters:
            site_name (str): Name of the site.
            counter_img (int): Counter for the image.

        Returns:
            str: Path for the image file.
        """
        folder_path_image = os.path.join(self.image_dir, site_name)
        if not os.path.exists(folder_path_image):
            os.makedirs(folder_path_image)

        path_image = os.path.join(
            folder_path_image, f"{self.date_utils.get_current_datetime()}-{counter_img}.jpg")

        return path_image

    def create_directories(self):
        """ 
        Create necessary directories if they don't exist. 
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.desktop_dir):
            os.makedirs(self.desktop_dir)
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir)
        if not os.path.exists(self.raw_data_dir):
            os.makedirs(self.raw_data_dir)


class DataFrames(Paths):

    def save_dataframe_with_retry(self, data, output_path, site_name=None):
        """ 
        Save DataFrame to Excel file with retry mechanism in case of permission errors.

        Parameters:
            data (list or DataFrame): Data to be saved.
            output_path (str): Path to the output Excel file.
            site_name (str): Name of the site (optional).

        Returns:
            DataFrame: The DataFrame that was saved.
        """
        saved_successfully = False
        df = None
        if output_path == 'daily':
            output_path = self.set_daily_scrapped()
        elif output_path == 'site':
            output_path = self.set_site_scrapped(site_name)
        new_data = len(data)
        for attempt in range(5):
            try:
                df = pd.DataFrame(data, columns=["Site", "Date", "Title", "Description", "Tags", "Models", "Video to embed",
                                                 "Link for video", "Link for image", "Path image", "Path video"])
                existing_df = pd.read_excel(output_path)
                df = pd.concat([df, existing_df], ignore_index=True)
                if new_data:
                    df.to_excel(output_path, index=False)
                    saved_successfully = True
                break
            except PermissionError:
                cprint(
                    f"Attempt {attempt + 1}: A permission error occurred while saving the file {output_path}.", 'red')
                time.sleep(5)

        if not saved_successfully:
            if new_data:
                cprint(
                    f"Exceeded the maximum number of retry attempts. The file {output_path} may be opened.", 'red')
                input("Press Enter to make one more attempt...")
                try:
                    df = pd.DataFrame(data, columns=["Site", "Date", "Title", "Description", "Tags", "Models", "Video to embed",
                                                     "Link for video", "Link for image", "Path image", "Path video"])
                    existing_df = pd.read_excel(output_path)
                    df = pd.concat([df, existing_df], ignore_index=True)
                    if data:
                        df.to_excel(output_path, index=False)
                        cprint("Manual attempt successful.", 'green')

                except Exception as e:
                    cprint(f"Manual attempt failed. Error is /n {e}", 'red')

        return df

    def read_save_schedule_df(self, list_name):
        """ 
        Read and save schedule data to Excel file.

        Parameters:
            list_name (str): Name of the list.

        Returns:
            str: Status of the list for the current date.
        """
        self.set_schedule_dataframe()
        existing_df = pd.read_excel(self.schedule_data, index_col=0)

        current_date = Utils.get_current_date()

        if current_date not in existing_df.columns:
            new_col = pd.DataFrame(columns=[current_date])
            existing_df = pd.concat([existing_df, new_col], axis=1, sort=False)

        try:
            if pd.isna(existing_df.at[list_name, current_date]):
                existing_df.at[list_name, current_date] = 'No'
        except KeyError:
            existing_df.loc[list_name, current_date] = 'No'

        existing_df = existing_df.reindex(
            sorted(existing_df.columns, reverse=True), axis=1)
        existing_df.to_excel(self.schedule_data, index=True)

        return existing_df.at[list_name, current_date]

    def update_schedule_df(self, list_name):
        """ 
        Update schedule data in Excel file.

        Parameters:
            list_name (str): Name of the list.
        """
        self.set_schedule_dataframe()
        existing_df = pd.read_excel(self.schedule_data, index_col=0)

        current_date = Utils.get_current_date()

        try:
            existing_df.at[list_name, current_date] = 'Yes'
        except KeyError:
            existing_df.loc[list_name, current_date] = 'Yes'

        existing_df = existing_df.reindex(
            sorted(existing_df.columns, reverse=True), axis=1)
        existing_df.to_excel(self.schedule_data, index=True)


class Utils:
    @staticmethod
    def setup_chrome_driver(headless=True):
        """
        Setup chrome driver.

        Returns:
        driver.
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--mute-audio')

        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-remote-debugging')
        chrome_options.add_argument('--disable-infobars')

        if headless:
            chrome_options.add_argument("--headless")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver

    @staticmethod
    def get_current_date():
        """
        Returns current date in format: Month day, year (Jan 08, 2020)
        """
        return datetime.now().strftime("%b %d, %Y")

    @staticmethod
    def get_day_of_week():
        return datetime.now().weekday()

    @staticmethod
    def get_current_datetime():
        """
        Returns current date + time in format: 
        """
        return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    @staticmethod
    def get_current_time():
        """
        Returns current time in format:  hour : minutes : second (21:04:32)
        """
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def start_time():
        return time.time()

    @staticmethod
    def end_time():
        return time.time()

    @staticmethod
    def load_configs(site):
        """
        Load xpaths.

        Returns:
        list: A list of xpaths.
        """
        with open('D:\\Visual Studio Code\\Scrapers\\Progam\\V2\\sites_config.json',
                  'r', encoding='utf-8') as json_file:
            xpaths = json.load(json_file)

            # Convert keys to lowercase
            xpaths_lower = {key.lower(): value for key,
                            value in xpaths.items()}

            return xpaths_lower.get(site.lower(), {})

    @staticmethod
    def extract_site_name(url):
        parsed_url = urlparse(url)
        match = re.match(
            r"^(?:https?://)?(?:www\.)?(?:.*?\.)?(?P<site_name>.+?)\.", parsed_url.netloc)
        site_name = match.group("site_name").replace(
            "-", "").replace("tour.", "").title() if match else None
        if site_name == "Dreamnet":
            site_name = "Girlsdreamnet"
        elif site_name == "Twistysnetwork":
            site_name = "Twistys"
        elif site_name == "Elxcomplete":
            site_name = "Evolvedfights"
        return site_name
