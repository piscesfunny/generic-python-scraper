import os.path
import time

import scrapy
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from utils.config import OUTPUT_MEDIA_URL_LIST_DIR
from utils.helpers import initialize_chrome_driver, write_results_to_txt
from utils.logging import ScraperLogger


class HindawiSpider(scrapy.Spider):
    name = 'hindawi'
    allowed_domains = ['www.hindawi.com']
    start_urls = [
        'https://www.hindawi.com'
    ]

    search_url = 'https://www.hindawi.com/search/all/mycobacterium AND tuberculosis AND protein AND structure/page/1?fromYear=2018&toYear=2021'

    logger = None

    def __init__(self, param):
        super(HindawiSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger
        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')
        self.list_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, 'urls.txt')
        self.page_count = 16

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers, meta={'page_number': 1}
            )

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        urls = []
        driver = initialize_chrome_driver()
        for page_number in range(1, self.page_count + 1):
            search_url = self.search_url.replace(f'page/1', f'page/{page_number}')
            driver.get(url=search_url)
            scrapy_selector = Selector(text=driver.page_source)

            category_selector = scrapy_selector.css(
                '#searchContent > div.ant-card.ant-card-bordered.article-card'
            )

            for selector in category_selector:
                url = selector.css('ul.ant-card-actions > li a::attr(href)').get()
                urls.append(url)

            time.sleep(1)

        write_results_to_txt(feed_uri=self.list_file_path, item_urls=urls)
