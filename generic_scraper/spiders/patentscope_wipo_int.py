import os
import random
import time
from datetime import datetime

import scrapy
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from utils.config import OUTPUT_LIST_DIR, OUTPUT_STATUS_DIR, OUTPUT_RESULT_DIR
from utils.constants import *
from utils.helpers import initialize_chrome_driver, read_file, write_results_to_txt
from utils.logging import ScraperLogger


class PatentScopeWipoSpider(scrapy.Spider):
    name = 'patentscope_wipo_int'
    allowed_domains = ['patentscope_wipo.wipo.int']
    start_urls = ['https://patentscope.wipo.int/search/en/search.jsf']

    base_url = 'https://patentscope.wipo.int'

    logger = None

    def __init__(self, param):
        super(PatentScopeWipoSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.scraping_target = param['scraping_target']
        self.target_year = param['target_year']
        self.target_start_week = param['target_start_week']
        self.target_end_week = param['target_end_week']
        self.category_file_path = param['category_file_path']
        self.result_list_suc_f_path = param['result_list_suc_f_path']
        self.result_list_err_f_path = param['result_list_err_f_path']
        self.feed_uri = param['feed_uri']

        self.min_date = datetime.strptime("13.07.2023", "%d.%m.%Y")

        self.result_dir = os.path.join(OUTPUT_RESULT_DIR, self.name)
        self.list_dir = os.path.join(OUTPUT_LIST_DIR, self.name)
        self.status_dir = os.path.join(OUTPUT_STATUS_DIR, self.name)
        os.makedirs(self.result_dir, exist_ok=True)
        os.makedirs(self.list_dir, exist_ok=True)
        os.makedirs(self.status_dir, exist_ok=True)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response, **kwargs):
        if self.scraping_target == SCRAPPING_TARGET_LIST:
            driver = initialize_chrome_driver()
            category_url = 'https://patentscope.wipo.int/search/en/resultWeeklyBrowse.jsf'
            driver.get(category_url)
            time.sleep(2)

            year_elem_id = 'weeklyPublicationForm:currGazette:input'
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, year_elem_id)))
            select = Select(driver.find_element(By.ID, year_elem_id))

            for i in range(self.target_start_week, self.target_end_week + 1):
                if i < 10:
                    option_value = f"0{i}/{self.target_year}"
                else:
                    option_value = f"{i}/{self.target_year}"
                select.select_by_value(option_value)
                time.sleep(10)

                week_data = select.first_selected_option.text
                self.logger.info(f"111 - {i}: {week_data}")
                print(f"111 - {i}: {week_data}")

                excel_download_elem_id = 'weeklyPublicationForm:j_idt1240'
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, excel_download_elem_id)))
                driver.find_element(By.ID, excel_download_elem_id).click()
                time.sleep(5)
        else:
            for i in range(self.target_start_week, self.target_end_week + 1):
                if i < 10:
                    week_num = f'{self.target_year}0{i}'
                else:
                    week_num = f'{self.target_year}{i}'

                download_dir = os.path.join(self.result_dir, "raw", week_num)
                os.makedirs(download_dir, exist_ok=True)
                driver = initialize_chrome_driver(save_dir=download_dir)

                status_dir = os.path.join(self.status_dir, self.action_type)
                os.makedirs(status_dir, exist_ok=True)
                success_f_path = os.path.join(status_dir, f'list_{week_num}_success.txt')
                ignored_f_path = os.path.join(status_dir, f'list_{week_num}_ignored.txt')

                input_f_path = os.path.join(self.list_dir, f"{week_num}.csv")
                items = read_file(input_f_path)
                if len(items) < 1:
                    continue

                _prev_success_urls = read_file(success_f_path, 'txt') if os.path.exists(success_f_path) else []
                prev_success_urls = list(set(_prev_success_urls))

                _prev_ignored_urls = read_file(ignored_f_path, 'txt') if os.path.exists(ignored_f_path) else []
                prev_ignored_urls = list(set(_prev_ignored_urls))

                urls_to_skip = prev_success_urls + prev_ignored_urls

                current_success_urls = []
                for index, item in enumerate(items):
                    original_doc_id = item.get('ID')
                    doc_id = original_doc_id.replace('/', '')
                    request_url = f'{self.base_url}/search/en/detail.jsf?docId={doc_id}&_gid={week_num}'
                    if request_url in urls_to_skip:
                        print(f"Skipped - {index+1}/{len(items)} - request_url: {request_url}")
                        continue

                    try:
                        driver.get(request_url)
                        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
                            By.CSS_SELECTOR, "ul.ui-tabs-nav > li"))
                        )
                        driver.find_element(By.CSS_SELECTOR, "ul.ui-tabs-nav > li:first-child > a").click()
                        time.sleep(1)

                        main_data_elems_css = '.ps-biblio-data--biblio-card > div'
                        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
                            By.CSS_SELECTOR, main_data_elems_css))
                        )

                        el_selector = Selector(text=driver.page_source)
                        publication_date_str = el_selector.css(main_data_elems_css)[1].css(
                            'span:last-child::text').get().strip()
                        publication_date = datetime.strptime(publication_date_str, "%d.%m.%Y")
                        if publication_date < self.min_date:
                            print("ignored_url: ", request_url)
                            write_results_to_txt(ignored_f_path, [request_url], "a")
                            continue

                        driver.find_element(By.CSS_SELECTOR, "ul.ui-tabs-nav > li:last-child > a").click()
                        WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".patent-documents > div"))
                        )

                        driver.find_element(By.CSS_SELECTOR, ".patent-documents > div:first-child tbody > tr > "
                                                             "td:last-child > div > span:last-child > a").click()

                        current_success_urls.append(request_url)
                        write_results_to_txt(success_f_path, [request_url], "a")
                    except Exception as e:
                        print("failed_url: ", request_url)
                        print(e)

                    t_delay = random.randint(5, 10)
                    time.sleep(t_delay)

                success_urls = prev_success_urls + current_success_urls
                write_results_to_txt(success_f_path, success_urls, "w")
