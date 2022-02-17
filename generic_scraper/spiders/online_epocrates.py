import time

import requests
import scrapy
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.config import Config
from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver, write_results_to_csv, read_file, \
    write_results_to_txt, download_image_by_wget
from utils.logging import ScraperLogger


class OnlineEpocratesSpider(scrapy.Spider):
    name = 'online_epocrates'
    allowed_domains = ['www.epocrates.com', 'online.epocrates.com']
    start_urls = ['https://www.epocrates.com/']

    base_url = 'https://online.epocrates.com'

    logger = None

    def __init__(self, param):
        super(OnlineEpocratesSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.scraping_target = param['scraping_target']
        self.target_category = param['target_category']
        self.category_file_path = param['category_file_path']
        self.result_list_suc_f_path = param['result_list_suc_f_path']
        self.result_list_err_f_path = param['result_list_err_f_path']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        delay = 5

        if self.scraping_target == SCRAPPING_TARGET_LIST:
            category_urls = [
                'https://online.epocrates.com/drugs',
                'https://online.epocrates.com/diseases'
            ]
            driver = initialize_chrome_driver()
            driver = self.login(driver)
            for category_url in category_urls:
                driver.get(category_url)
                if self.target_category == "drugs":
                    cls_elements = driver.find_elements(By.CSS_SELECTOR, "div#classlist > ul > li > a")
                    if cls_elements:
                        cls_elements.pop(0)
                    for cls_element in cls_elements:
                        cls_name = cls_element.get_attribute("title")
                        cls_element.click()
                        time.sleep(delay)
                        sub_cls_elements = driver.find_elements(By.CSS_SELECTOR, "div#subclasslist > ul > li > a")
                        for sub_cls_element in sub_cls_elements:
                            items = []
                            sub_cls_name = sub_cls_element.get_attribute("title")
                            sub_cls_element.click()
                            time.sleep(delay)
                            scrapy_selector = Selector(text=driver.page_source)
                            item_selectors = scrapy_selector.css('div#drugTableBody > table tr td a')
                            for item_selector in item_selectors:
                                item_url = item_selector.css('::attr(href)').get()
                                if item_url:
                                    item_url = f"{self.base_url}{item_url}"
                                    items.append({
                                        'category': self.target_category,
                                        'cls_name': cls_name,
                                        'sub_cls_name': sub_cls_name,
                                        'item_url': item_url
                                    })

                            write_results_to_csv(self.result_list_suc_f_path, items)

                            self.logger.info(f'Get list - category: {self.target_category} - item count: {len(items)}')
                            print(f'Get list - category: {self.target_category} - item count: {len(items)}')

                            time.sleep(1)
        elif self.scraping_target == SCRAPPING_TARGET_ITEM:
            items = read_file(self.result_list_suc_f_path)

            self.get_items(items)
        else:
            pass

    def get_items(self, items):
        progress_f_path = os.path.join(OUTPUT_DIR, 'progress.txt')
        processed_item_urls = read_file(progress_f_path, file_format="txt")
        prev_save_dir = None
        for item in items:
            category = item.get('category')
            cls_name = item.get('cls_name').replace("/", "_").replace(" ", "_")
            sub_cls_name = item.get('sub_cls_name').replace("/", "_").replace(" ", "_")
            item_url = item.get('item_url')

            if item_url in processed_item_urls:
                self.logger.info(f'Skipped url: {item_url}')
                print(f'Skipped url: {item_url}')
                continue

            item_name = item_url.split('/')[-1]

            category_dir = os.path.join(OUTPUT_RESULT_DIR, category)
            cls_dir = os.path.join(category_dir, cls_name)
            save_dir = os.path.join(cls_dir, sub_cls_name)
            os.makedirs(save_dir, exist_ok=True)

            if prev_save_dir != save_dir:
                driver = initialize_chrome_driver(printable=True, save_dir=save_dir)
                driver = self.login(driver)

            prev_save_dir = save_dir

            item_monograph_url = f"{item_url}/Monograph"
            driver.get(item_monograph_url)
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='rx_navSections']/div/ul/li[1]/a")))
                time.sleep(2)
                driver.find_element(By.XPATH, "//*[@id='rx_navSections']/div/ul/li[1]/a").click()
                time.sleep(2)

                driver.execute_script('window.print();')

                time.sleep(10)

                item_urls = [item_url]
                write_results_to_txt(progress_f_path, item_urls, f_open_mode="a")

                self.logger.info(f'success_url: {item_url}')
                print(f'success_url: {item_url}')
            except Exception as e:
                self.logger.info(f'failed_url: {item_url}')
                print(str(e))
                print(f'failed_url: {item_url}')
                failed_items = [item]
                write_results_to_csv(self.result_list_err_f_path, failed_items)

    def login(self, driver):
        driver.get("https://www.epocrates.com/login?refernext=https://online.epocrates.com/")
        username = driver.find_element(By.ID, "email_input")
        password = driver.find_element(By.ID, "password")

        username.send_keys(Config.email)
        password.send_keys(Config.password)

        time.sleep(2)
        driver.find_element(By.ID, "signin").click()

        time.sleep(5)

        return driver
