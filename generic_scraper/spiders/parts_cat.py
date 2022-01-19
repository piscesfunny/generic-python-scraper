import csv
import json
import time

import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium.webdriver.common.by import By

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver, scroll_to_bottom, write_results_to_csv
from utils.logging import ScraperLogger


class PartsCatSpider(scrapy.Spider):
    name = 'alibaba'
    allowed_domains = ['parts.cat.com']
    start_urls = ['https://parts.cat.com/en/catcorp/']

    base_url = 'https://parts.cat.com'

    logger = None

    def __init__(self, param):
        super(PartsCatSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='parts_cat.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.scraping_target = param['scraping_target']
        self.category_file_path = param['category_file_path']
        self.result_list_suc_f_path = param['result_list_suc_f_path']
        self.result_list_err_f_path = param['result_list_err_f_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.feed_uri = param['feed_uri']

    def start_requests(self):
        categories = []
        with open(self.category_file_path, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)

            # extracting each data row one by one
            for row in csvreader:
                _row = row[0]
                name = os.path.split(_row)[1]
                url = self.base_url + _row
                categories.append({'name': name, 'url': url})

        for category in categories:
            name = category.get('name')
            url = category.get('url')
            if name == self.target_category:
                yield scrapy.Request(
                    url=url, callback=self.parse, headers=self.default_headers,
                    meta={'category': name})

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        category = response.meta.get('category')

        sub_cat_selectors = response.css("div.category-image > ul > li")
        sub_categories = []
        for sub_cat_selector in sub_cat_selectors:
            sub_cat_name = sub_cat_selector.css('a::text').get()
            sub_cat_url = sub_cat_selector.css('a::attr(href)').get()
            if sub_cat_url:
                sub_cat_url = self.base_url + sub_cat_url
            sub_categories.append({'name': sub_cat_name, 'url': sub_cat_url})

        if self.scraping_target == SCRAPPING_TARGET_LIST:
            yield self.get_item_list(
                meta={'category': category, 'sub_categories': sub_categories})
        elif self.scraping_target == SCRAPPING_TARGET_ITEM:
            headers = self.default_headers
            headers['referer'] = response.request.url
            with open(self.result_list_suc_f_path) as f:
                item_urls = json.load(f)
                for item_url_dict in item_urls:
                    url = item_url_dict['item_url']

                    yield scrapy.Request(
                        url=url, callback=self.parse_items, headers=headers,
                        meta={'category': self.target_category}
                    )

                    time.sleep(1)
        else:
            pass

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

    def get_item_list(self, meta):
        driver = initialize_chrome_driver()
        category = meta.get('category')
        sub_categories = meta.get('sub_categories')
        for sub_category in sub_categories:
            sub_cat_url = sub_category.get('url')
            sub_cat_name = sub_category.get('name')
            driver.get(url=sub_cat_url)
            while True:
                page_source = scroll_to_bottom(driver, time_delay=1)
                load_more_btn = driver.find_element(By.ID, "loadMoreButton")
                style_attribute = load_more_btn.get_attribute('style')
                if 'none' in style_attribute.lower():
                    break
                else:
                    load_more_btn.click()
                    self.logger.info(f'Clicked LoadMoreBtn - category: {category} - sub_category: {sub_category}')

            scrapy_selector = Selector(text=page_source)

            item_selectors = scrapy_selector.css('div.product_listing_container > ul.product_card_list > li')
            items = []
            for item_selector in item_selectors:
                item_url = item_selector.css('div.product a::attr(href)').get()
                if item_url:
                    item_url = self.base_url + item_url

                item = {'category': category, 'sub_category': sub_cat_name, 'item_url': item_url}
                items.append(item)

            write_results_to_csv(self.result_list_suc_f_path, items)

            self.logger.info("Exported result")
