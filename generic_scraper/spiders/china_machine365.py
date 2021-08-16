import json
import time
import csv

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.constants import *
# from utils.logging import ScraperLogger


class ChinaMachine365Spider(scrapy.Spider):
    name = 'china_machine365'
    allowed_domains = ['china.machine365.com']
    start_urls = ['http://china.machine365.com/']

    logger = None

    def __init__(self, param):
        super(ChinaMachine365Spider, self).__init__()

        # self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.item_url_file_path = param['item_url_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.category = param['sub_category']
        self.category_url = param['sub_category_url']
        self.processed_url_path = param['processed_url_path']
        self.processed_page_path = param["processed_page_path"]
        self.total_page_count = param["total_page_num"]
        self.start_page_number = 1

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers
            )

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        if self.base_category == CATEGORY_UNKNOWN:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                yield scrapy.Request(
                    url=self.specific_category_url, callback=self.parse_list, headers=headers
                )
            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                headers = self.default_headers
                headers['referer'] = response.request.url
                with open(self.list_file_path) as f:
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

    def parse_list(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        self.logger.info(f'Parse List - {response.request.url}')

        main_url = self.specific_category_url
        for page_number in range(self.start_page_number, self.total_page_count+1):
            try:
                request_url = f'{main_url}?pages={page_number}'

                r = requests.get(url=request_url, headers=headers, timeout=30)
                self.logger.info(f'Current page url: {request_url}')

                time.sleep(5)

                headers['referer'] = f'{main_url}?pages={page_number}'

                selector = Selector(text=r.text)
                products_per_page = selector.css('#datas > div')
                for product in products_per_page:
                    item_url = product.css('a::attr(href)').get()

                    yield {
                        'item_url': response.urljoin(item_url)
                    }
            except Exception as e:
                self.logger.info(f'Error page number: {page_number}')
                break

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        category = response.meta['category']

        name = response.css('.dc-t-r-title::text').get()
        price = response.css('.input-shell.price .is-r-price::text').get()
        quick_details = response.css('.hr2-left > .details-bottom').get()

        country = 'China'
        description = ''
        specification = ''

        img_urls = []
        video_urls = []
        doc_urls = []

        thumb_img = response.css('.swiper-slide-active img::attr(src)').get()
        img_urls.append(thumb_img)

        separator = ';'
        img_urls_str = separator.join(img_urls)
        video_urls_str = separator.join(video_urls)
        doc_urls_str = separator.join(doc_urls)

        media_urls = img_urls + video_urls + doc_urls

        with open(self.media_urls_file_path, "a") as f:
            for url in media_urls:
                f.write(f'{url}\n')

        raw_item = {
            'name': name, 'category': category, 'country': country, 'price': price, 'quick_details': quick_details,
            'description': description, 'specification': specification, 'img_urls_str': img_urls_str,
            'video_urls_str': video_urls_str, 'doc_urls_str': doc_urls_str
        }

        for (k, v) in raw_item.items():
            if v is None:
                raw_item[k] = ''

        loader = ItemLoader(item=FarmMachineryItem())
        loader.add_value('name', name)
        loader.add_value('category', category)
        loader.add_value('country', country)
        loader.add_value('price', price)
        loader.add_value('quick_details', quick_details)
        loader.add_value('description', description)
        loader.add_value('specification', specification)
        loader.add_value('img_urls', img_urls_str)
        loader.add_value('video_urls', video_urls_str)
        loader.add_value('doc_urls', doc_urls_str)
        loader.add_value('item_url', request_url)
        loader.add_value('website', self.start_urls[0])

        item = loader.load_item()

        return item
