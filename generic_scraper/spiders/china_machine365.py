import json
import time

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.constants import *
from utils.helpers import initialize_chrome_driver, scroll_to_bottom
from utils.logging import ScraperLogger


class ChinaMachine365Spider(scrapy.Spider):
    name = 'china_machine365'
    allowed_domains = ['china.machine365.com']
    start_urls = ['http://china.machine365.com/']

    logger = None

    def __init__(self, param):
        super(ChinaMachine365Spider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.scraping_target = param['scraping_target']
        self.list_file_path = param['list_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.base_category = param['base_category']
        self.specific_category_url = param['specific_category_url']
        self.total_page_count = int(param['total_page_count'])
        self.start_page_number = int(param['start_page_number'])

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
                driver = initialize_chrome_driver()
                with open(self.list_file_path) as f:
                    item_urls = json.load(f)
                    for item_url_dict in item_urls:
                        url = item_url_dict['item_url']
                        item = self.get_item_detail_one(
                            request_url=url, category=self.target_category, driver=driver, scrapy_response=response
                        )
                        yield item
                        time.sleep(1)
                driver.close()
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

    def get_item_detail_one(self, request_url, category, driver, scrapy_response):
        self.logger.info(f'Parse Items - {request_url}')
        driver.get(url=request_url)
        page_source = scroll_to_bottom(driver)

        selector = Selector(text=page_source)

        name = selector.css('h1::text').get()
        price = selector.css('.ma-price-wrap').get()
        quick_details = selector.css('.widget-detail-overview .do-entry-separate').get()
        quick_details_entry_selectors = selector.css(
            '.widget-detail-overview .do-entry-separate .do-entry-list > dl.do-entry-item')

        place_of_origin = ''
        for quick_details_entry_selector in quick_details_entry_selectors:
            k = quick_details_entry_selector.css('.do-entry-item > .attr-name::text').get()
            if k == 'Place of Origin:':
                _place_of_origin = selector.css('.do-entry-item-val > .text-ellipsis::text').get()
                place_of_origin = _place_of_origin if _place_of_origin else ''

        place_of_origin_list = place_of_origin.split(',')
        place_of_origin_list_length = len(place_of_origin_list)

        country = None
        if place_of_origin_list_length > 0:
            country = place_of_origin_list[place_of_origin_list_length - 1]

        specification = selector.css('.richtext-detail.rich-text-description table').get()
        description = selector.css('.richtext-detail.rich-text-description').get()

        thumb_img_selectors = selector.css('ul.main-image-thumb-ul > li.main-image-thumb-item img')
        thumb_img_urls = []
        for img_selector in thumb_img_selectors:
            sm_img_url = img_selector.css('::attr(src)').get()
            if sm_img_url:
                img_url = sm_img_url \
                    .replace('.jpg_50x50', '') \
                    .replace('.jpeg_50x50', '') \
                    .replace('.png_50x50', '')
                thumb_img_urls.append(scrapy_response.urljoin(img_url))

        thumb_video_selectors = selector.css('body video')
        thumb_video_urls = []
        for video_selector in thumb_video_selectors:
            video_url = video_selector.css('::attr(src)').get()
            if video_url:
                thumb_video_urls.append(scrapy_response.urljoin(video_url))

        detail_img_selectors = selector.css('.richtext-detail.rich-text-description img')
        detail_img_urls = []
        for selector in detail_img_selectors:
            img_url = selector.css('::attr(data-src)').get()
            if img_url:
                detail_img_urls.append(scrapy_response.urljoin(img_url))

        img_urls = thumb_img_urls + detail_img_urls
        video_urls = thumb_video_urls
        doc_urls = []

        media_urls = img_urls + video_urls + doc_urls
        with open(self.media_urls_file_path, "a") as f:
            for url in media_urls:
                f.write(f'{url}\n')

        separator = ';'
        img_urls_str = separator.join(img_urls)
        video_urls_str = separator.join(video_urls)
        doc_urls_str = separator.join(doc_urls)

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
        loader.add_value('website', 'http://www.alibaba.com')

        item = loader.load_item()

        return item
