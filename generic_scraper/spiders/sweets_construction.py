import json
import os
import time

import scrapy
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium.common.exceptions import NoSuchElementException

from utils.config import OUTPUT_RESULT_DIR
from utils.helpers import initialize_chrome_driver, write_results_to_json
from utils.logging import ScraperLogger


class SweetsConstructionSpider(scrapy.Spider):
    name = 'ironplanet'
    allowed_domains = ['sweets.construction.com']
    start_urls = ['https://sweets.construction.com/BrowseByDivision']

    base_url = 'https://sweets.construction.com'

    logger = None

    def __init__(self, param):
        super(SweetsConstructionSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='sweets_construction.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.category_file_path = param['category_file_path']
        self.list_file_path = param['list_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.feed_uri = param['feed_uri']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers
            )

    def parse(self, response):
        with open(self.category_file_path) as f:
            categories = json.load(f)

        driver = initialize_chrome_driver()

        for category in categories:
            category_name = category['name']
            category_url = category['url']

            items = self.get_items(request_url=category_url, category=category_name, driver=driver)
            print(len(items))

            time.sleep(1)

        driver.close()

    def get_items(self, request_url, category, driver):
        self.logger.info(f'Parse Items - {request_url}')
        feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{category}.json')
        if os.path.exists(feed_uri):
            os.remove(feed_uri)

        driver.get(url=request_url)
        try:
            els = driver.find_elements_by_css_selector('#ulMf > li')
            selected_count = 0
            total_count = len(els)
            while True:
                els[selected_count].click()
                time.sleep(2)
                els = driver.find_elements_by_css_selector('#ulMf > li')
                selected_count += 1
                if selected_count > total_count - 1:
                    break
        except NoSuchElementException as exception:
            self.logger.info(f"Exception - {exception}")

        total_items = []
        while True:
            items = []
            scrapy_selector = Selector(text=driver.page_source)
            item_selectors = scrapy_selector.css('#ctl00_cphMain_divResults > div')
            for selector in item_selectors:
                _item_url = selector.css('.col-md-10 > a::attr(href)').get()
                item_url = self.base_url + _item_url
                name = selector.css('.col-md-10 > a::text').get()
                description = selector.css('.col-md-10 > span::text').get()
                brand_block_selectors = selector.css('.col-md-10 .brandBlock > p')
                manufacturer = search_category = master_format = ''
                for idx, brand_block_selector in enumerate(brand_block_selectors):
                    if idx == 0:
                        manufacturer = driver.find_element_by_xpath(
                            '//*[@id="ctl00_cphMain_divResults"]/div[1]/div[2]/div/div/p[1]'
                        ).text.replace('Manufacturer:', '')
                    elif idx == 1:
                        search_category = driver.find_element_by_xpath(
                            '//*[@id="ctl00_cphMain_divResults"]/div[1]/div[2]/div/div/p[2]')\
                            .text.replace('Category:', '')
                    else:
                        master_format = driver.find_element_by_xpath(
                            '//*[@id="ctl00_cphMain_divResults"]/div[1]/div[2]/div/div/p[3]'
                        ).text.replace('MasterFormat:', '')
                _img_url = selector.css('.col-md-2 > a > img::attr(src)').get()
                img_url = _img_url.replace('/150_150/', '/300_300/')

                raw_item = {
                    'category': category, 'name': name, 'description': description, 'search_category': search_category,
                    'manufacturer': manufacturer, 'master_format': master_format, 'img_url': img_url,
                    'item_url': item_url
                }

                for (k, v) in raw_item.items():
                    if v is None:
                        raw_item[k] = ''

                items.append(raw_item)
                total_items.append(raw_item)

            write_results_to_json(feed_uri=feed_uri, items=items, write_mode='a')

            try:
                driver.find_element_by_id('ctl00_cphMain_cntrPaginationControl_lnkNext').click()
            except NoSuchElementException:
                break

        return total_items
