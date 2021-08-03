import json
import time

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium import webdriver

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.constants import *
from utils.logging import ScraperLogger


class AlibabaSpider(scrapy.Spider):
    name = 'alibaba'
    allowed_domains = ['www.alibaba.com']
    start_urls = ['http://www.alibaba.com/']

    logger = None

    def __init__(self, param):
        super(AlibabaSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='alibaba.log').logger

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
                    url=self.specific_category_url, callback=self.parse_list_one, headers=headers
                )
            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                pass
            else:
                pass
        else:
            url = 'https://www.alibaba.com/machinery/agricultural-machinery-equipment/p43_p100010631?spm=a27aq.13891069.scGlobalHomeHeader.381.5e015736OReuU7'
            if self.base_category == CATEGORY_MINING:
                url = 'https://www.alibaba.com/machinery/mining-machinery/p43_p100007279?spm=a27aq.industry_category_productlist.0.0.7472407dFMOLLf'

            yield scrapy.Request(
                url=url, callback=self.parse_categories, headers=headers
            )

    def parse_categories(self, response):
        categories = []
        non_target_category_names = [
            'Animal & Poultry Husbandry Equipment', 'Aquaculture Machine Aerators', 'Biomass Briquette Machines',
            'Biomass Dryers', 'Egg Incubators', 'Feed Processing Machines', 'Forestry Machinery', 'Milking Machines',
            'Oil Pressers', 'Silos', 'Slaughtering Equipment'
        ]
        if self.base_category == CATEGORY_MINING:
            non_target_category_names = []

        category_selectors = response.css('.industry-category-tree > .nav')
        for selector in category_selectors:
            name = selector.css('.name > a::text').get()
            url = selector.css('.name > a::attr(href)').get()
            if name in non_target_category_names:
                continue

            modified_name = name.replace(' ', '-').replace('&', '-')
            category = {'name': modified_name, 'url': url}
            categories.append(category)

        if self.action_type == ACTION_GET_CATEGORY:
            for category in categories:
                yield category

        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                for category in categories:
                    category_name = category['name']
                    category_url = category['url']
                    if category_name == self.target_category:
                        category_full_url = f'{category_url}'

                        driver = self.initialize_chrome_driver()
                        driver.get(url=category_full_url)
                        page_source = self.scrollToBottom(driver)
                        scrapy_selector = Selector(text=page_source)

                        driver.close()

                        item_selectors = scrapy_selector.css('div.flexColFloor.flex5ColFloor')
                        item_urls = []
                        for item_selector in item_selectors:
                            item_url = "https:" + item_selector.css('div.tpl-wrapper > a.dx-event-node::attr(href)').get()
                            if item_url in item_urls:
                                continue

                            item_urls.append(item_url)

                            yield {
                                'item_url': response.urljoin(item_url)
                            }

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

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        category = response.meta['category']
        name = response.css('h1::text').get()
        price = response.css('.ma-price-wrap').get()

        thumb_img_selectors = response.css('ul.main-image-thumb-ul > li.main-image-thumb-item img')
        thumb_img_urls = []
        for img_selector in thumb_img_selectors:
            sm_img_url = img_selector.css('::attr(src)').get()
            if sm_img_url:
                img_url = sm_img_url\
                    .replace('.jpg_50x50', '')\
                    .replace('.jpeg_50x50', '')\
                    .replace('.png_50x50', '')
                thumb_img_urls.append(response.urljoin(img_url))

        thumb_video_selectors = response.css('body video')
        thumb_video_urls = []
        for video_selector in thumb_video_selectors:
            video_url = video_selector.css('::attr(src)').get()
            if video_url:
                thumb_video_urls.append(response.urljoin(video_url))

        quick_details = response.css('.widget-detail-overview .do-entry-separate').get()
        quick_details_entry_selector = response.css(
            '.widget-detail-overview .do-entry-separate .do-entry-list > dl.do-entry-item')

        place_of_origin = ''
        for selector in quick_details_entry_selector:
            k = selector.css('.do-entry-item > .attr-name::text').get()
            if k == 'Place of Origin:':
                place_of_origin = selector.css('.do-entry-item-val > .ellipsis::text').get()

        place_of_origin_list = place_of_origin.split(', ')
        place_of_origin_list_length = len(place_of_origin_list)

        country = None
        if place_of_origin_list_length > 0:
            country = place_of_origin_list[place_of_origin_list_length - 1]

        detail_img_selectors = response.css('.richtext-detail.rich-text-description img')
        detail_img_urls = []
        for selector in detail_img_selectors:
            img_url = selector.css('::attr(data-src)').get()
            if img_url:
                detail_img_urls.append(response.urljoin(img_url))

        specification = response.css('.richtext-detail.rich-text-description table').get()
        description = response.css('.richtext-detail.rich-text-description').get()

        img_urls = thumb_img_urls + detail_img_urls
        video_urls = thumb_video_urls
        doc_urls = []

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

        yield item

        media_urls = img_urls + video_urls + doc_urls
        with open(self.media_urls_file_path, "a") as f:
            for url in media_urls:
                f.write(f'{url}\n')

    def parse_list_one(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        self.logger.info(f'Parse List - {response.request.url}')

        # main_url = 'https://www.alibaba.com/catalog/transformers_cid141907'
        main_url = self.specific_category_url
        for page_number in range(self.start_page_number, self.total_page_count+1):
            try:
                request_url = f'{main_url}?page={page_number}&ISJSON=1&_bx-v=1.1.20'

                r = requests.get(url=request_url, headers=headers, timeout=30)
                self.logger.info(f'Current page url: {request_url}')

                offer_result_count_str = json.loads(r.text).get('offerResultData').get('totalCount')
                offer_result_count = int(offer_result_count_str) if offer_result_count_str else 0
                if offer_result_count == 0:
                    time.sleep(120)
                    self.logger.info(f'Waiting 120s...')
                    r = requests.get(url=request_url, headers=headers, timeout=30)
                    offer_result_count_str_two = json.loads(r.text).get('offerResultData').get('totalCount')
                    offer_result_count_two = int(offer_result_count_str_two) if offer_result_count_str_two else 0

                    if offer_result_count_two == 0:
                        time.sleep(300)
                        self.logger.info(f'Waiting 300s...')
                        r = requests.get(url=request_url, headers=headers, timeout=30)
                else:
                    time.sleep(5)

                headers['referer'] = f'{main_url}?page={page_number}&ISJSON=1&_bx-v=1.1.20'

                data = json.loads(r.text)
                products_per_page = data.get('offerResultData').get('offerList')
                for product in products_per_page:
                    item_url = product.get('information').get('productUrl')

                    yield {
                        'item_url': response.urljoin(item_url)
                    }
            except Exception as e:
                self.logger.info(f'Error page number: {page_number}')
                break

    def get_items_one(self, request_url, category, driver):
        pass
