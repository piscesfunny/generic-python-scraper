import json
import time

import requests
import scrapy
from scraper_api import ScraperAPIClient
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.constants import *
from utils.logging import ScraperLogger


class MachineryPeteSpider(scrapy.Spider):
    name = 'ironplanet'
    allowed_domains = ['www.machinerypete.com']
    start_urls = ['https://www.machinerypete.com/categories']

    base_url = 'https://www.machinerypete.com'

    logger = None

    def __init__(self, param):
        super(MachineryPeteSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='machinerypete.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')
        self.client = ScraperAPIClient(SCRAPER_API_KEY)

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.scraping_target = param['scraping_target']
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
        headers = self.default_headers

        if self.action_type == ACTION_GET_CATEGORY:
            categories = []
            category_selectors = response.css('.table.table-counts tr > td')
            for selector in category_selectors:
                _category_name = selector.css('div.category-header a::text').get()
                sub_category_selectors = selector.css('div.visible-sm > ul')
                sub_categories = []

                for sub_category_selector in sub_category_selectors:
                    subheader_selectors = sub_category_selector.css('li.subcategory-header')
                    subtype_selectors = sub_category_selector.css('div.subtype-header')

                    if len(subtype_selectors) > 0:
                        subheader_selectors = subtype_selectors

                    for subheader_selector in subheader_selectors:
                        name = subheader_selector.css('a::text').get()
                        _url = subheader_selector.css('a::attr(href)').get()
                        url = f'{self.base_url}/listings{_url}'

                        sub_categories.append({'name': name, 'url': url})

                if _category_name:
                    category_name = _category_name.replace(' ', '-').replace('&', '-').replace('/', '-')
                else:
                    category_name = ''

                category = {'name': category_name, 'sub_categories': sub_categories}
                categories.append(category)

            for category in categories:
                yield category

        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                with open(self.category_file_path) as f:
                    categories = json.load(f)
                for category in categories:
                    category_name = category['name']
                    sub_categories = category['sub_categories']
                    if category_name == self.target_category:
                        item_urls = []
                        for sub_category in sub_categories:
                            sub_category_url = sub_category['url']
                            while True:
                                headers['referer'] = sub_category_url
                                self.logger.info(f'Sub Category URL - {sub_category_url}')
                                res = requests.get(url=sub_category_url, headers=headers)
                                scrapy_selector = Selector(text=res.text)
                                item_selectors = scrapy_selector.css('.listing-wrapper')

                                for item_selector in item_selectors:
                                    item_url = item_selector.css('.listing-name > a::attr(href)').get()

                                    item_url = f'{self.base_url}{item_url}'

                                    if item_url in item_urls:
                                        continue

                                    item_urls.append(item_url)

                                    yield {
                                        'item_url': response.urljoin(item_url)
                                    }

                                next_page_elem = scrapy_selector.css("ul.pagination > li > a[rel=next]").get()

                                if not next_page_elem:
                                    break

                                next_page_url = scrapy_selector.css('ul.pagination > li > a[rel=next]::attr(href)').get()

                                sub_category_url = self.base_url + next_page_url

                                time.sleep(1)

            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                headers = self.default_headers
                headers['referer'] = response.request.url

                with open(self.list_file_path) as f:
                    item_urls = json.load(f)
                    for item_url_dict in item_urls:
                        url = item_url_dict['item_url']
                        item = self.get_items(request_url=url, category=self.target_category, headers=headers)

                        if item:
                            yield item

                        time.sleep(1)
        else:
            pass

    def get_items(self, request_url, category, headers):
        self.logger.info(f'Parse Items - {request_url}')
        response = requests.get(url=request_url, headers=headers, timeout=30)
        scrapy_selector = Selector(text=response.text)

        name = scrapy_selector.css('#seo-title::text').get()
        country = 'US'
        quick_details = ''
        specification = ''
        description = scrapy_selector.css('.listing-detail-wrapper').get()

        img_urls = []
        img_selectors = scrapy_selector.css('.thumbnails-wrapper > ul > li.image-thumb')
        img_count = len(img_selectors)

        if img_count < 4:
            return None

        for img_selector in img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            lazy_img_url = img_selector.css('::attr(lazy-src)').get()

            img_url = img_url if img_url else lazy_img_url

            if img_url:
                if img_url in img_urls:
                    continue

                normal_img_url = img_url.replace('thumbnail_', '')
                img_urls.append(normal_img_url)

        video_urls = []
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

        return item
