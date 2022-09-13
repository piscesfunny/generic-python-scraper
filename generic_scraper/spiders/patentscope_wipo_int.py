import os
import time

import requests
import scrapy
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from utils.config import OUTPUT_LIST_DIR, OUTPUT_FAILED_DIR, OUTPUT_STATUS_DIR
from utils.constants import *
from utils.helpers import initialize_chrome_driver, write_results_to_csv, read_file, write_results_to_txt
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
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
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

    def start_requests(self):
        if self.scraping_target == SCRAPPING_TARGET_LIST:
            driver = initialize_chrome_driver()
            category_url = 'https://patentscope.wipo.int/search/en/resultWeeklyBrowse.jsf'
            driver.get(category_url)
            time.sleep(2)

            year_elem_id = 'weeklyPublicationForm:currGazette:input'
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, year_elem_id)))
            select = Select(driver.find_element_by_id('weeklyPublicationForm:currGazette:input'))

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

                excel_download_elem_id = 'weeklyPublicationForm:j_idt1221'
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, excel_download_elem_id)))
                driver.find_element_by_id(excel_download_elem_id).click()
                time.sleep(5)
        else:

            for url in self.start_urls:
                yield scrapy.Request(
                    url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        for i in range(self.target_start_week, self.target_end_week + 1):
            week_num = f'{self.target_year}{i}'
            input_f_name = f'patentscope_wipo_int_list_{week_num}.csv'
            input_f_path = os.path.join(OUTPUT_LIST_DIR, input_f_name)
            failed_f_path = os.path.join(OUTPUT_STATUS_DIR, f'patentscope_wipo_int_list_{week_num}_failed.txt')
            success_f_path = os.path.join(OUTPUT_STATUS_DIR, f'patentscope_wipo_int_list_{week_num}_success.txt')

            items = read_file(input_f_path)
            succeeded_urls = read_file(success_f_path, file_format='txt')

            output_items = []
            failed_items = []
            success_urls = []
            failed_urls = []
            for index, item in enumerate(items):
                num_of_items = len(items)
                count = index + 1
                original_doc_id = item.get('ID')
                title = item.get('Title')
                doc_id = original_doc_id.replace('/', '')
                request_url = f'{self.base_url}/search/en/detail.jsf?docId={doc_id}&_gid={week_num}'
                if request_url in succeeded_urls:
                    print(f'Skipped - Index: {count}/{num_of_items} - URL: {request_url}')
                    self.logger.info(f'Skipped - Index: {count}/{num_of_items} - URL: {request_url}')
                    continue
                try:
                    res = requests.get(url=request_url, headers=headers)
                    time.sleep(1)

                    scrapy_selector = Selector(text=res.text)

                    main_data_elems_css = '.ps-biblio-data--biblio-card > div'
                    publication_number = scrapy_selector.css(main_data_elems_css)[0].css('span')[1].css('::text').get()
                    publication_date = scrapy_selector.css(main_data_elems_css)[1].css('span')[1].css('::text').get()
                    application_number = scrapy_selector.css(main_data_elems_css)[2].css('span')[1].css('::text').get()
                    applicants = scrapy_selector.css(main_data_elems_css)[6].css('span li span::text').getall()
                    inventors = scrapy_selector.css(main_data_elems_css)[7].css('span li span::text').getall()
                    agents = scrapy_selector.css(main_data_elems_css)[8].css('span li span::text').getall()
                    priority_data = scrapy_selector.css(main_data_elems_css)[9].css('span tr *::text').getall()
                    publication_language = scrapy_selector.css(main_data_elems_css)[10].css('span')[1].css('::text').get()
                    detailed_title = scrapy_selector.css('.PCTtitle').get()
                    abstract = scrapy_selector.css('.patent-abstract').get()

                    raw_output_item = {
                        'week_number': week_num,
                        'title': title,
                        'publication_number': publication_number,
                        'publication_date': publication_date,
                        'application_number': application_number,
                        'applicants': applicants,
                        'inventors': inventors,
                        'agents': agents,
                        'priority_data': priority_data,
                        'publication_language': publication_language,
                        'detailed_title': detailed_title,
                        'abstract': abstract,
                        'item_url': request_url,
                        'website': self.base_url
                    }

                    output_item = self.transform_item(raw_output_item)
                    output_items.append(output_item)
                    success_urls.append(request_url)
                    print(f'Success - Index: {count}/{num_of_items} - InputFile: {week_num} - URL: {request_url}')
                    self.logger.info(f'Success - Index: {count}/{num_of_items} - InputFile: {week_num} - URL: {request_url}')

                except Exception as e:
                    failed_items.append(item)
                    failed_urls.append(request_url)
                    print(f'Failed - Index: {count}/{num_of_items} - InputFile: {week_num} - URL: {request_url}')
                    print(f'Exception - {str(e)}')
                    self.logger.info(f'Failed - Index: {count}/{num_of_items} - InputFile: {week_num} - URL: {request_url}')
                    self.logger.info(f'Exception - {str(e)}')

                n_output_items = len(output_items)
                if (n_output_items > 0 and n_output_items % 100 == 0) or count == num_of_items:
                    write_results_to_csv(self.feed_uri, output_items)
                    write_results_to_txt(success_f_path, success_urls, f_open_mode='a')
                    output_items = []
                    success_urls = []

            if failed_items:
                write_results_to_csv(os.path.join(OUTPUT_FAILED_DIR, input_f_name), failed_items, rewrite_mode=True)
                write_results_to_txt(failed_f_path, failed_urls)

    @staticmethod
    def transform_item(raw_item):
        item = {}
        list_item_keys = ['applicants', 'inventors', 'agents', 'priority_data']
        delimiter = ' ||| '
        for k, v in raw_item.items():
            if k in list_item_keys:
                filtered_item = [elem.strip() for elem in v]
                item[k] = delimiter.join(filtered_item)
            else:
                item[k] = v.strip() if v else v
        return item
