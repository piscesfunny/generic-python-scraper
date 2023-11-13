import os.path
import time
from datetime import datetime

import scrapy
from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.config import OUTPUT_RESULT_DIR, OUTPUT_STATUS_DIR
from utils.constants import SCRAPPING_TARGET_LIST
from utils.helpers import initialize_chrome_driver, write_results_to_txt, read_file
from utils.logging import ScraperLogger


class ScienceDailySpider(scrapy.Spider):
    name = 'science_daily'
    allowed_domains = ['www.sciencedaily.com']
    start_urls = ['https://www.sciencedaily.com']

    base_url = 'https://www.sciencedaily.com'

    logger = None

    def __init__(self, param):
        super(ScienceDailySpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36'
        }

        self.scraping_target = param['scraping_target']
        self.target_start_date = param['target_start_date']
        self.target_end_date = param['target_end_date']
        self.result_list_f_path = param['result_list_f_path']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response, **kwargs):
        if self.scraping_target == SCRAPPING_TARGET_LIST:
            driver = initialize_chrome_driver()
            driver.get(f"{response.url}/news")

            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'directory')))
            time.sleep(5)

            driver.find_element_by_css_selector('ul#directory > li:first-child > a').click()
            time.sleep(1)

            driver.find_element_by_css_selector('ul#list > li:last-child > a').click()
            time.sleep(1)

            for i in range(0, 2):
                driver.find_element_by_id('load_more_stories').click()
                # page_source = scroll_to_bottom(driver, time_delay=1)
                time.sleep(1)

            el_selector = Selector(text=driver.page_source)
            first_page_weekdays = el_selector.css('#headlines > div::text').getall()
            other_page_weekdays = el_selector.css('#headlines > div > div > div::text').getall()
            weekdays = first_page_weekdays + other_page_weekdays
            n_weekdays = 0
            for weekday in weekdays:
                dt = datetime.strptime(weekday, "%A, %B %d, %Y")
                if dt < self.target_start_date:
                    break
                n_weekdays += 1

            total_news_elems = el_selector.css('#headlines > ul') + el_selector.css('#headlines > div > div > ul')
            news_elems = total_news_elems[:n_weekdays]
            urls = []
            for el in news_elems:
                urls_per_day = el.css('li > a::attr(href)').getall()
                urls += urls_per_day

            full_urls = [self.base_url + url for url in urls]
            filtered_urls = list(set(full_urls))
            write_results_to_txt(self.result_list_f_path, filtered_urls)
        else:
            urls = read_file(self.result_list_f_path, 'txt')
            save_dir = os.path.join(OUTPUT_RESULT_DIR, self.name)
            os.makedirs(save_dir, exist_ok=True)

            success_f_name = os.path.splitext(os.path.basename(self.result_list_f_path))[0]
            success_f_path = os.path.join(OUTPUT_STATUS_DIR, f'{success_f_name}_success.txt')
            _prev_success_urls = read_file(success_f_path, 'txt') if os.path.exists(success_f_path) else []
            prev_success_urls = list(set(_prev_success_urls))

            driver = initialize_chrome_driver(maximized=False, printable=True, save_dir=save_dir)
            current_success_urls = []
            for url in urls:
                if url in prev_success_urls:
                    print(f"Skipped - request_url: {url}")
                    continue

                driver.get(url)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'story_text')))
                # Save the PDF
                driver.execute_script("window.print();")  # Chrome-specific command to save page as PDF
                time.sleep(5)

                current_success_urls.append(url)
                write_results_to_txt(success_f_path, [url], "a")

            success_urls = prev_success_urls + current_success_urls
            write_results_to_txt(success_f_path, success_urls, "w")
        driver.close()
