#!/usr/bin/env python3
"""
    *******************************************************************************************
    WinkelstraatBot.
    Author: Ali Toori, Python Developer [Web-Automation Bot Developer | Web-Scraper Developer]
    Profiles:
        Upwork: https://www.upwork.com/freelancers/~011f08f1c849755c46
        Fiver: https://www.fiverr.com/alitoori
    *******************************************************************************************
"""
import os
import time
import pickle
import ntplib
import random
import pyfiglet
import datetime
import pandas as pd
import logging.config
from time import sleep
from pathlib import Path
import concurrent.futures
from selenium import webdriver
from multiprocessing import freeze_support
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import Winkel_Config


class Winkel:
    def __init__(self):
        self.logged_in = False
        self.driver = None
        self.stopped = False
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.main_url = 'https://www.winkelstraat.nl/'
        self.file_path_account = str(self.PROJECT_ROOT / "WinkelRes/Accounts.csv")
        self.file_categories_urls = str(self.PROJECT_ROOT / "WinkelRes/CategoriesURLs.csv")
        self.file_product_urls = str(self.PROJECT_ROOT / "WinkelRes/Itemurls.csv")
        self.file_used_categories = str(self.PROJECT_ROOT / "WinkelRes/Used_Categories.csv")
        self.file_account = str(self.PROJECT_ROOT / 'WinkelRes/Accounts.csv')
        self.directory_downloads = str(self.PROJECT_ROOT / 'WinkelRes/Downloads/')
        # self.proxies = self.get_proxies()
        self.user_agents = self.get_user_agents()
        self.LOGGER = self.get_logger()

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "filename": "WikelstraatBot.log"
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        # Enables Windows New ANSI Support for Colored Printing on CMD
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ WinkelStraatBot\n', colors='RED')
        print('Author: Ali Toori\n'
              'Website: https://botflocks.com/\n'
              '************************************************************************')

    # Get random user agent
    def get_proxies(self):
        file_proxies = str(self.PROJECT_ROOT / 'WinkelRes/proxies.txt')
        with open(file_proxies) as f:
            content = f.readlines()
        file_proxies = [x.strip() for x in content]
        return file_proxies

    # Get random user agent
    def get_user_agents(self):
        file_uagents = str(self.PROJECT_ROOT / 'WinkelRes/user_agents.txt')
        with open(file_uagents) as f:
            content = f.readlines()
        user_agents = [x.strip() for x in content]
        return user_agents

    # Get proxy web driver
    def get_proxy_driver(self, proxy=False, headless=False):
        self.LOGGER.info(f'Launching chrome browser')
        DRIVER_BIN = str(self.PROJECT_ROOT / 'WinkelRes/bin/chromedriver.exe')
        service = Service(executable_path=DRIVER_BIN)
        # user_dir = str(self.PROJECT_ROOT / 'WinkelRes/UserData')
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--dns-prefetch-disable")
        # options.add_argument('--incognito')
        options.add_argument('--disable-extensions')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        # options.add_argument(f"--user-data-dir={user_dir}")
        options.add_experimental_option('prefs', {
            'directory_upgrade': True,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_settings.popups': False,
            # "profile.managed_default_content_settings.images": 2,
            f'download.default_directory': f'{self.directory_downloads}'})
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        if proxy:
            proxy_selected = random.choice(self.proxies)
            self.LOGGER.info(f'Using proxy: {proxy_selected}')
            options.add_argument(f'--proxy-server={proxy_selected}')
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    
    # Login to the website for smooth processing
    def login(self, driver, account):
        email = account["Email"]
        password = account["Password"]
        cookies = 'Cookies_' + email + '.pkl'
        file_cookies = self.PROJECT_ROOT / 'WinkelRes' / cookies
        self.LOGGER.info(f'[Signing-in to the website ... ]: {email}]')
        main_url = 'https://www.winkelstraat.nl/'
        # Login to the website
        # if os.path.isfile(file_cookies):
        #     driver.get(main_url)
        #     self.LOGGER.info(f'[Loading cookies ...]: {email}]')
        #     with open(file_cookies, 'rb') as cookies_file:
        #         cookies = pickle.load(cookies_file)
        #     for cookie in cookies:
        #         driver.add_cookie(cookie)
        #     driver.get(main_url)
        driver.get(main_url)
        self.LOGGER.info(f'[Please sign-in manually ! You have 3 minutes to sign-in.]: {email}]')
        self.LOGGER.info(f'[Your Credentials: : Email: {email} Password: {password}]')
        # sleep(180)
        self.wait_until_visible(driver=driver, css_selector='.invert-underline.px-3', duration=10)
        driver.find_element(By.CSS_SELECTOR, '.invert-underline.px-3').click()
        self.wait_until_visible(driver=driver, css_selector='input[id="input-email"]', duration=10)
        driver.find_element(By.CSS_SELECTOR, 'input[id="input-email"]').send_keys(email)
        driver.find_element(By.CSS_SELECTOR, 'input[id="input-password"]').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, '.btn-secondary.w-full').click()
        sleep(5)
        # # Store user cookies for later use
        # with open(file_cookies, 'wb') as cookies_file:
        #     pickle.dump(driver.get_cookies(), cookies_file)
        # self.LOGGER.info(f"Cookies have been saved]: {email}]")

    def wait_until_visible(self, driver, xpath=None, element_id=None, name=None, class_name=None, tag_name=None, css_selector=None, duration=10000, frequency=0.01):
        if xpath:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        elif element_id:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
        elif name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
        elif class_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
        elif tag_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))
        elif css_selector:
            WebDriverWait(driver, duration, frequency).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))

    def get_heren(self, main_url):
        self.LOGGER.info('[Getting URLs for HEREN ...]')
        url_list = []
        for category in Winkel_Config.HEREN_DICT['heren']:
            url = ''
            category_list = None
            if category == '/schoenen':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.HEREN_DICT['heren_schoenen']
            elif category == '/jassen':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.HEREN_DICT['heren_jassen']
            elif category == '/kleding':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.HEREN_DICT['heren_kleding']
            elif category == '/accessoires':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.HEREN_DICT['heren_accessoires']
            elif category == '/scooters':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.HEREN_DICT['heren_scooters']
            for subcategory in category_list:
                final_url = url + '/designers/' + subcategory
                url_list.append(final_url)
        self.LOGGER.info(f'[URLs for HEREN: {str(url_list)}')
        return url_list

    def get_dames(self, main_url):
        self.LOGGER.info('[Getting URLs for DAMES ...]')
        url_list = []
        for category in Winkel_Config.DAMES_DICT['dames']:
            url = ''
            category_list = None
            if category == '/schoenen':
                url = main_url + 'heren' + category
                category_list = Winkel_Config.DAMES_DICT['dames_schoenen']
            elif category == '/jassen':
                url = main_url + 'dames' + category
                category_list = Winkel_Config.DAMES_DICT['dames_jassen']
            elif category == '/tassen':
                url = main_url + 'dames' + category
                category_list = Winkel_Config.DAMES_DICT['dames_tassen']
            elif category == '/accessoires':
                url = main_url + 'dames' + category
                category_list = Winkel_Config.DAMES_DICT['dames_accessoires']
            elif category == '/vintage':
                url = main_url + 'dames' + category
                category_list = Winkel_Config.DAMES_DICT['dames_vintage']
            elif category == '/kleding':
                url = main_url + 'dames' + category
                category_list = Winkel_Config.DAMES_DICT['dames_kleding']
            for subcategory in category_list:
                final_url = url + '/designers/' + subcategory
                url_list.append(final_url)
        self.LOGGER.info(f'[URLs for DAMES:{ str(url_list)}')
        return url_list

    def get_kinderen(self, main_url):
        self.LOGGER.info('[Getting URLs for KINDEREN ...]')
        url_list = []
        for category in Winkel_Config.KINDEREN_DICT['kinderen']:
            url = ''
            category_list = None
            if category == '/jongens':
                url = main_url + 'kinderen' + category
                category_list = Winkel_Config.KINDEREN_DICT['kinderen_jongens']
            elif category == '/meisjes':
                url = main_url + 'kinderen' + category
                category_list = Winkel_Config.KINDEREN_DICT['kinderen_meisjes']
            elif category == '/babys':
                url = main_url + 'kinderen' + category
                category_list = Winkel_Config.KINDEREN_DICT['kinderen_babys']
            for subcategory in category_list:
                final_url = url + '/designers/' + subcategory
                url_list.append(final_url)
        self.LOGGER.info(f'[URLs for KINDEREN: {str(url_list)}')
        return url_list

    def get_designer(self, main_url):
        self.LOGGER.info('[Getting URLs for DESIGNERS ...]')
        url_list = []
        for category in Winkel_Config.DESIGNERS_DICT['designer_all']:
            final_url = main_url + 'designers/' + category
            url_list.append(final_url)
        for category in Winkel_Config.DESIGNERS_DICT['designer_dutch']:
            final_url = main_url + 'designers/' + category
            url_list.append(final_url)
        for category in Winkel_Config.DESIGNERS_DICT['designer_luxe']:
            final_url = main_url + 'designers/' + category
            url_list.append(final_url)
        for category in Winkel_Config.DESIGNERS_DICT['designer_premium']:
            final_url = main_url + 'designers/' + category
            url_list.append(final_url)
        self.LOGGER.info(f'[URLs for DESIGNERS: {str(url_list)}')
        return url_list

    def get_product_urls(self, url, driver):
        file_product_urls = self.PROJECT_ROOT / "WinkelRes/Itemurls.csv"
        file_used_categories = self.PROJECT_ROOT / "WinkelRes/Used_Categories.csv"
        # Login to the website
        driver.get(url)
        # Wait for product to be visible
        try:
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'products-grid')))
        except:
            return
        driver.find_element_by_tag_name('html').send_keys(Keys.END)
        num_of_pages = None
        try:
            # Wait for the page number to be visible
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, 'select-page')))
            num_of_pages = driver.find_element_by_id('select-page').find_element_by_tag_name('option').text
            num_of_pages = str(num_of_pages).strip()
            self.LOGGER.info(f'[Number of pages text: {num_of_pages}')
            num_of_pages = int(num_of_pages[12:])
            self.LOGGER.info(f'[Number of pages found: {str(num_of_pages)}')
        except:
            num_of_pages = 1
            self.LOGGER.info('[No other pages were found !]')
        used_pages = 0
        for page in range(1, num_of_pages):
            self.LOGGER.info(f'[Getting product urls from URL: {str(driver.current_url)}')
            product_urls = {"ItemURL": [p.get_attribute('href') for p in driver.find_elements_by_css_selector('.image-urls.track-ga-click')]}
            df = pd.DataFrame.from_dict(product_urls)
            # if file does not exist write header
            if not os.path.isfile(file_product_urls) or os.path.getsize(file_product_urls) == 0:
                df.to_csv(file_product_urls, index=False)
            else:  # else if exists so append without writing the header
                df.to_csv(file_product_urls, mode='a', header=False, index=False)
            self.LOGGER.info(f'[urls has been saved to the file ItemUrls.csv')
            used_pages += 1
            driver.get(url=url + '?p=' + str(page + 1))
        if used_pages == num_of_pages:
            self.to_file(file_used_categories, url)

    def get_products(self, account):
        file_product_urls = self.PROJECT_ROOT / "WinkelRes/ItemUrls.csv"
        email = str(account["Email"])
        password = str(account["Password"])
        # proxy = str(account["Proxy"])
        # Create and launch proxy browsers
        driver = self.get_proxy_driver()
        # Login to the website
        self.login(driver=driver, account=account)
        sizes = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']
        self.LOGGER.info('[Processing products add-to-cart]')
        df = pd.read_csv(file_product_urls, index_col=None).drop_duplicates()
        # WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'top-header-urls')))
        to_cart = 0
        for index, row in df.iterrows():
            to_cart += 1
            if to_cart >= 10:
                to_cart = 0
            item = row["ItemURL"]
            available = False
            self.LOGGER.info(f'[Item Number: {str(index)} URL: {str(item)}]')
            driver.get(url=item)
            self.LOGGER.info('[Waiting for 20 Secs to be visible]')
            sleep(20)
            if to_cart == (3 or 9):
                size = random.choice(sizes)
                self.LOGGER.info(f'[Size to be selected: {str(size)}]')
                # Wait between each item
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-select-buttons')))
                self.LOGGER.info(f'[Available Sizes: ' + str(str(driver.find_element_by_class_name('product-select-buttons').text).strip().split('\n')) + ']')
                # driver.find_element_by_xpath("//lable[@id="+size+"]/following-sibling::label")
                for label in driver.find_element_by_class_name('product-select-buttons').find_elements_by_tag_name('label'):
                    if str(label.find_element_by_class_name('label').text).strip() == size and str(label.find_element_by_class_name('sub-label').text).strip() != ('Geef seintje' or ''):
                        available = True
                        label.click()
                        p_size = str(label.text).strip().split("\n")
                        self.LOGGER.info(f"[Product size selected: {p_size}")
                        break
                if not available:
                    self.LOGGER.info('[Product size not available]')
                    continue
                # Wait for Ad-To-Cart button to be visible and click
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.btn.btn-primary.btn-block.btn-secondary')))
                driver.find_element_by_css_selector('.btn.btn-primary.btn-block.btn-secondary').click()
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'close')))
                self.LOGGER.info('[Product has been added to cart]')
            self.LOGGER.info('[Waiting for 30 Seconds]')
            sleep(30)
            self.LOGGER.info('[Moving to next item]')
        self.finish(driver=driver)

    def to_file(self, filename, row):
        with open(filename, "a+") as file:
            file.write(row + '\n')

    def finish(self, driver):
        try:
            self.LOGGER.info(f'Closing the browser')
            driver.close()
            driver.quit()
        except WebDriverException as exc:
            self.LOGGER.info(f'Issue occurred while closing the browser')

    def main(self):
        freeze_support()
        self.enable_cmd_colors()
        # Print ASCII Art
        self.banner()
        self.LOGGER.info(f'CoinMarketCapBot launched')
        if os.path.isfile(self.file_account):
            # The main homepage URL (AKA base URL)ere
            # file_used_items = winkel.PROJECT_ROOT / "WinkelRes/Used_Items.csv")
            if os.path.isfile(self.file_used_categories):
                u_cat_df = pd.read_csv(self.file_used_categories, index_col=None)
                # Get accounts from Accounts.csv
                used_categories = [cat for cat in u_cat_df.iloc]
            # Get all the categories' URLs
            if not os.path.isfile(self.file_categories_urls):
                self.LOGGER.info('[Writing Categories file ...]')
                df = pd.DataFrame.from_dict({'item_category': self.get_heren(main_url=self.main_url)})
                df.to_csv(self.file_categories_urls, index=False)
                df = pd.DataFrame.from_dict({'item_category': self.get_dames(main_url=self.main_url)})
                df.to_csv(self.file_categories_urls, index=False)
                df = pd.DataFrame.from_dict({'item_category': self.get_kinderen(main_url=self.main_url)})
                df.to_csv(self.file_categories_urls, index=False)
                df = pd.DataFrame.from_dict({'item_category': self.get_designer(main_url=self.main_url)})
                df.to_csv(self.file_categories_urls, index=False)
            else:  # else if exists so append without writing the header
                self.LOGGER.info(f'[CategoriesURLs file size: {str(round(os.path.getsize(self.file_categories_urls).real/1024))} KB]')

            if os.path.isfile(self.file_path_account):
                account_df = pd.read_csv(self.file_path_account, index_col=None)
                # Get accounts from Accounts.csv
                account_list = [account for account in account_df.iloc]
                account = account_list[0]
                # If product urls are not found and categories urls are found
                if not os.path.isfile(self.file_product_urls) and os.path.isfile(self.file_categories_urls):
                    df = pd.read_csv(self.file_categories_urls, index_col=None).drop_duplicates()
                    self.LOGGER.info('[Generating item urls ...]')
                    if df is not None:
                        driver = self.get_proxy_driver()
                        self.login(driver=driver, account=account)
                        self.LOGGER.info(f'[Processing CategoriesURLs.csv]')
                        [self.get_product_urls(url=cat, driver=driver) for cat in df["item_category"]]
                        self.finish(driver=driver)
                    else:
                        self.LOGGER.info('[CategoriesURLs.csv file is empty]')
                self.get_products(account=account)
                # Launch the tasks
                # We can use a with statement to ensure threads are cleaned up promptly
                # with concurrent.futures.ThreadPoolExecutor(max_workers=len(account_list)) as executor:
                #     executor.map(winkel.get_products, account_list)
        else:
            pass
            # self.LOGGER.warning("Your trial has been expired"")
            # self.LOGGER.warning("Please contact fiverr.com/AliToori !")
    

if __name__ == '__main__':
    winkel_bot = Winkel()
    winkel_bot.main()

