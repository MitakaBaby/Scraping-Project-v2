import os
import re
import json
import time


from anyio import Path
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Colors:
    """
    Provides ANSI escape sequences for text color, background color, and text style.
    """
    # Foreground colors
    FOREGROUND = {
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'ORANGE': '\033[38;5;208m'
    }

    # Background colors
    BACKGROUND = {
        'BLACK_BACKGROUND': '\033[40m',
        'RED_BACKGROUND': '\033[41m',
        'GREEN_BACKGROUND': '\033[42m',
        'YELLOW_BACKGROUND': '\033[43m',
        'BLUE_BACKGROUND': '\033[44m',
        'MAGENTA_BACKGROUND': '\033[45m',
        'CYAN_BACKGROUND': '\033[46m',
        'WHITE_BACKGROUND': '\033[47m'
    }

    # Styles
    STYLE = {
        'BOLD': '\033[1m',
        'ITALIC': '\033[3m',
        'UNDERLINE': '\033[4m',
        'INVERSE': '\033[7m'
    }

    RESET = '\033[0m'

    @staticmethod
    def color(*args):
        """
        Returns ANSI escape sequences for applying styles and colors in the console.

        Args:
            *args (str): Styles and colors to apply. Can be 'BOLD', 'ITALIC', 'UNDERLINE', 'INVERSE',
                         or any of the predefined color names in the FOREGROUND and BACKGROUND dictionaries.

        Returns:
            str: ANSI escape sequences.
        """
        escape_sequence = ''

        style_count = sum(1 for arg in args if arg.upper() in Colors.STYLE)
        fg_color_count = sum(
            1 for arg in args if arg.upper() in Colors.FOREGROUND)
        bg_color_count = sum(
            1 for arg in args if arg.upper() in Colors.BACKGROUND)

        if style_count > 1:
            raise ValueError("Only one style can be specified.")
        if fg_color_count > 1:
            raise ValueError("Only one foreground color can be specified.")
        if bg_color_count > 1:
            raise ValueError("Only one background color can be specified.")

        for style in args:
            if style.upper() in Colors.STYLE:
                escape_sequence += Colors.STYLE[style.upper()]

        for fg_color in args:
            if fg_color.upper() in Colors.FOREGROUND:
                escape_sequence += Colors.FOREGROUND[fg_color.upper()]

        for bg_color in args:
            if bg_color.upper() in Colors.BACKGROUND:
                escape_sequence += Colors.BACKGROUND[bg_color.upper()]

        return escape_sequence


class CustomLogger:
    """
    Logs messages to the console and log files with colored output based on log levels.
    """
    LOG_LEVEL_COLORS = {
        'DEBUG': Colors.color('MAGENTA'),
        'MISC': Colors.color('BLUE'),
        'INFO': Colors.color('GREEN'),
        'PATH': Colors.color("ORANGE"),
        'WARNING': Colors.color('YELLOW'),
        'ERROR': Colors.color('RED'),
        'CRITICAL': Colors.color('RED', 'UNDERLINE')
    }

    def log(self, message: str, level: str, site: str, exception=None):
        """
        Logs a message to the console and to log files.

        Args:
            message (str): The message to be logged.
            level (str): The log level, which determines the color of the log message.
            site (str): The name of the site being logged.
            exception (Optional): The exception to be logged, if any.

        Returns:
            None
        """
        folder_name = Utils.get_current_date()

        console_output = f"{message}"
        color = self.LOG_LEVEL_COLORS.get(level, '')
        print(f"{color}{console_output}{Colors.RESET}")

        log_entry = f"{Utils.get_current_time()} [{level}]"
        if site:
            log_entry += f" [{site}]"
        log_entry += f" {message}"

        if exception:
            log_entry += "\n" + str(exception)
        folder_path = os.path.join(Paths().log_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        if level in ['INFO', 'PATH', 'MISC']:
            level = 'INFO'
        log_file = os.path.join(folder_path, f"{level.lower()}.log")

        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

        main_log_file = os.path.join(folder_path, "main.log")
        with open(main_log_file, 'a') as f:
            f.write(log_entry + '\n')


class Paths:
    """
    Manages file paths and directory creation.
    """

    def __init__(self):
        """
        Initializes Paths object.
        """
        self.home_dir = os.path.expanduser("~")
        self.filename = os.path.basename(__file__)  # This is the file name
        self.script_dir = os.path.dirname(__file__)
        self.data_dir = os.path.join(self.home_dir, "Desktop", "Site", "Data")
        self.desktop_dir = os.path.join(self.home_dir, self.data_dir, "Data From Scrapers")
        self.image_dir = os.path.join(self.home_dir, self.data_dir, "Pictures", "Auto Downloaded")
        self.video_dir = os.path.join(self.home_dir, self.data_dir, "Videos", "Auto Downloaded Trailers")
        self.raw_data_dir = os.path.join(self.home_dir, self.data_dir, "Raw Data")
        self.log_dir = os.path.join(self.home_dir, self.data_dir, "Logs")
        self.daily_scrapped = ""
        self.site_scrapped = ""
        self.schedule_data = ""
        self.root = tk.Tk()
        self.root.withdraw()
        self.create_directories()
        self.date_utils = Utils()
        self.logger = CustomLogger()

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
        os.makedirs(folder_path_video, exist_ok=True)

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
        os.makedirs(folder_path_image, exist_ok=True)

        path_image = os.path.join(
            folder_path_image, f"{self.date_utils.get_current_datetime()}-{counter_img}.jpg")

        return path_image

    def create_directories(self):
        """ 
        Create necessary directories if they don't exist. 
        """
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.desktop_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)


class DataFrames(Paths):
    """
    Manages the creation and manipulation of Pandas DataFrames for storing scraped data.
    Inherits from Paths to utilize file paths and directory management functionalities.
    """

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
            except PermissionError as ps_error:
                self.logger.log(
                    f"Attempt {attempt + 1}: A permission error occurred while saving the file {output_path}",
                    level='ERROR',
                    site="DataFrame",
                    exception=ps_error)

                time.sleep(5)

        if not saved_successfully:
            if new_data:
                self.logger.log(
                    f"Exceeded the maximum number of retry attempts. The file {output_path} may be opened",
                    level='ERROR',
                    site="DataFrame"
                )

                success = self.manual_retry_prompt(
                    output_path, max_retries=3, data=data)
                if success:
                    self.logger.log(
                        "Manual attempt successful",
                        level='INFO',
                        site="DataFrame"
                    )
                else:
                    self.logger.log(
                        "Manual attempt failed",
                        level='ERROR',
                        site="DataFrame"
                    )

        return df

    def manual_retry_prompt(self, output_path, max_retries, data):
        """ Display retry prompt """
        retry_count = 0
        while retry_count < max_retries:
            retry = messagebox.askretrycancel(
                "Retry", f"Exceeded the maximum number of retry attempts to save file {output_path}. Retry? ({retry_count + 1}/{max_retries})")
            if retry:
                retry_count += 1
                try:
                    df = pd.DataFrame(data, columns=["Site", "Date", "Title", "Description", "Tags", "Models", "Video to embed",
                                                     "Link for video", "Link for image", "Path image", "Path video"])
                    existing_df = pd.read_excel(output_path)
                    df = pd.concat([df, existing_df], ignore_index=True)
                    if data:
                        df.to_excel(output_path, index=False)
                        return True
                except Exception as e:
                    self.logger.log(
                        f"Manual attempt failed. Error is {e}",
                        level='ERROR',
                        site="DataFrame"
                    )
            else:
                return False
        return False

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
    """
    Utility class for common functions.
    """
    @staticmethod
    def setup_chrome_driver(headless=True):
        """
        Setup chrome driver.

        Returns:
        driver.
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--mute-audio")

        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-remote-debugging")
        chrome_options.add_argument("--disable-infobars")

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
        """
        Returns the current day of the week (0 for Monday, 6 for Sunday).
        """
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
        """
        Returns the current time as a starting point for measuring elapsed time.
        """
        return time.time()

    @staticmethod
    def end_time():
        """
        Returns the current time as an ending point for measuring elapsed time.
        """
        return time.time()

    @staticmethod
    def log_start_time(site):
        """
        Logs the start time of an execution.

        Args:
            site (str): The name of the site or process being logged.

        Returns:
            float: The start time in seconds since the epoch.
        """
        start_time = Utils.start_time()
        CustomLogger().log(
            f"{site} started executing at {Utils.get_current_time()}",
            level='MISC',
            site=site)
        return start_time

    @staticmethod
    def log_elapsed_time(start_time, site):
        """
        Logs the elapsed time since the start time.

        Args:
            start_time (float): The start time in seconds since the epoch.
            site (str): The name of the site or process being logged.

        Returns:
            None
        """
        end_time = Utils.end_time()
        elapsed_time = end_time - start_time
        CustomLogger().log(
            f"Elapsed time: {elapsed_time:.2f} seconds\n{'_' * 100}",
            level='MISC',
            site=site)

    @staticmethod
    def load_configs(site):
        """
        Load xpaths from a JSON file.

        Args:
            site (str): The name of the site.

        Returns:
            dict: A dictionary of xpaths for the given site.
        """
        with open(os.path.join(Paths().script_dir, 'sites_config.json'), 'r', encoding='utf-8') as json_file:
            xpaths = json.load(json_file)

            xpaths_lower = {key.lower(): value for key, value in xpaths.items()}

            return xpaths_lower.get(site.lower(), {})

    @staticmethod
    def extract_site_name(url):
        """
        Extracts the site name from the given URL.

        Args:
            url (str): The URL from which to extract the site name.

        Returns:
            str: The extracted site name.
        """
        parsed_url = urlparse(url)
        match = re.match(r"^(?:https?://)?(?:www\.)?(?:.*?\.)?(?P<site_name>.+?)\.", parsed_url.netloc)
        site_name = match.group("site_name").replace("-", "").replace("tour.", "").title() if match else ""
        return site_name

    @staticmethod
    def load_site_config(site):
        """
        Load the site configuration and return the site URL and name.

        Args:
            site (str): The name of the site.

        Returns:
            tuple: A tuple containing the site URL and name.
        """
        url_site = Utils.load_configs(site).get("site")
        site_name = Utils.extract_site_name(url_site)
        return url_site, site_name

    @staticmethod
    def get_existing_data(site_name):
        """
        Retrieves existing data (links and titles) from a saved DataFrame for a given site.

        Args:
            site_name (str): The name of the site.

        Returns:
            tuple: A tuple containing lists of existing links and titles.
                - If no data is found, returns empty lists.
        """
        data = []
        result = DataFrames().save_dataframe_with_retry(
            data, "site", site_name)
        if result is None:
            return [], []
        else:
            link_from_excel = result['Link for video'].tolist()
            title_from_excel = result['Title'].tolist()
            return link_from_excel, title_from_excel

    @staticmethod
    def save_scraped_data(data, site_name):
        """
        Saves scraped data to Excel files.

        Args:
            data (list or DataFrame): Data to be saved.
            site_name (str): Name of the site for which the data is being saved.

        Returns:
            None
        """
        DataFrames().save_dataframe_with_retry(data, "daily")
        DataFrames().save_dataframe_with_retry(data, "site", site_name)
