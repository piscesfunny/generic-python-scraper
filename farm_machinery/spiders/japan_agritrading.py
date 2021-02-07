import json
import time

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from farm_machinery.items import FarmMachineryItem
from utils.constants import *
from utils.logging import ScraperLogger


class JapanAgriTradingSpider(scrapy.Spider):
    name = 'alibaba'
    allowed_domains = ['japan-agritrading.com']
    start_urls = ['https://japan-agritrading.com/']

    base_url = 'https://japan-agritrading.com/'

    logger = None

    def __init__(self, param):
        super(JapanAgriTradingSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='japan_agritrading.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.scraping_target = param['scraping_target']
        self.list_file_path = param['list_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.feed_uri = param['feed_uri']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers
            )

    def parse(self, response):
        category_url = 'https://japan-agritrading.com/category/select/cid/325'
        headers = self.default_headers
        headers['referer'] = response.request.url

        yield scrapy.Request(
            url=category_url, callback=self.parse_category, headers=headers
        )

    def parse_category(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        categories = []
        category_selectors = response.css('ul.sub_category_list > li')
        for selector in category_selectors:
            name = selector.css('a p.text::text').get()
            url = selector.css('a::attr(href)').get()

            modified_name = name.replace(' ', '').replace('&', '-').replace(',', '-').replace('and', '-')\
                .replace('and', '-').replace('(', '-').replace(')', '-').replace('/', '-')

            category = {'name': modified_name, 'url': url}
            categories.append(category)

        if self.action_type == ACTION_GET_CATEGORY:
            for category in categories:
                yield category
        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                item_urls = []
                for category in categories:
                    category_name = category['name']
                    category_url = category['url']
                    if category_name == self.target_category:
                        while True:
                            res = requests.get(url=category_url, headers=headers)
                            scrapy_selector = Selector(text=res.text)

                            item_selectors = scrapy_selector.css('.itemlist_img > .item')
                            for item_selector in item_selectors:
                                item_url = item_selector.css('a::attr(href)').get()

                                if item_url in item_urls:
                                    continue

                                item_urls.append(item_url)

                                yield {
                                    'item_url': response.urljoin(item_url)
                                }

                            next_page_elem = scrapy_selector.css('.bottom_navi > .page_navi .navi > li.next a').get()

                            if not next_page_elem:
                                break

                            next_page_url = scrapy_selector.css(
                                '.bottom_navi > .page_navi .navi > li.next a::attr(href)'
                            ).get()

                            category_url = next_page_url
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
        name = response.css('.title_item h2::text').get()
        country = 'Japan'
        quick_details = ''
        specification = ''
        description = response.css('.product-description .main-column').get()

        thumb_img_urls = []
        thumb_img_selectors = response.css('.categoryFrame > .item_schema .imageFrame img')
        for img_selector in thumb_img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            lazy_img_url = img_selector.css('::attr(lazy-src)').get()

            img_url = img_url if img_url else lazy_img_url

            if img_url:
                if img_url in thumb_img_urls:
                    continue

                img_url = self.base_url + img_url
                thumb_img_urls.append(img_url)

        other_img_urls = []
        other_img_selectors = response.css('.categoryFrame > .item_schema .product-description img')
        for img_selector in other_img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            lazy_img_url = img_selector.css('::attr(lazy-src)').get()

            img_url = img_url if img_url else lazy_img_url

            if img_url:
                if img_url in other_img_urls:
                    continue

                img_url = self.base_url + img_url
                other_img_urls.append(img_url)

        img_urls = thumb_img_urls + other_img_urls
        video_urls = []
        video_selectors = response.css('.product-description .youtube')
        for video_selector in video_selectors:
            video_url = video_selector.css('iframe::attr(src)').get()

            if video_url:
                if video_url in video_urls:
                    continue

                video_urls.append(video_url)

        doc_urls = []

        separator = ';'
        img_urls_str = separator.join(img_urls)
        video_urls_str = separator.join(video_urls)
        doc_urls_str = separator.join(doc_urls)

        media_urls = img_urls + video_urls + doc_urls
        with open(self.media_urls_file_path, "a") as f:
            for url in media_urls:
                f.write(f'{url}\n')

        raw_item = {
            'name': name, 'category': category, 'country': country, 'quick_details': quick_details,
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
        loader.add_value('quick_details', quick_details)
        loader.add_value('description', description)
        loader.add_value('specification', specification)
        loader.add_value('img_urls', img_urls_str)
        loader.add_value('video_urls', video_urls_str)
        loader.add_value('doc_urls', doc_urls_str)
        loader.add_value('item_url', request_url)
        loader.add_value('website', self.base_url)

        item = loader.load_item()

        yield item
