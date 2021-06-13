import json
import os
import time

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.constants import *
from utils.logging import ScraperLogger


class MeganormSpider(scrapy.Spider):
    name = 'meganorm'
    allowed_domains = ['meganorm.ru']
    start_urls = [
        'https://meganorm.ru/list0.htm',
        'https://meganorm.ru/list1.htm',
        'https://meganorm.ru/list2.htm',
    ]

    base_url = 'https://meganorm.ru'

    logger = None

    def __init__(self, param):
        super(MeganormSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='meganorm.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.scraping_target = param['scraping_target']
        self.category_file_path = param['category_file_path']
        self.list_file_path = param['list_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.feed_uri = param['feed_uri']
        self.error_file_path = param['error_file_path']
        self.failed_items = []

        if self.target_category == 'Строительный_каталог':
            self.start_url = self.start_urls[1]
            self.list_prefix = 'list1'
        elif self.target_category == 'Строительная_база':
            self.start_url = self.start_urls[2]
            self.list_prefix = 'list2'
        else:
            self.start_url = ''
            self.list_prefix = 'list'

    def start_requests(self):
        url = self.start_url

        yield scrapy.Request(
            url=url, callback=self.parse, headers=self.default_headers
        )

    def parse(self, response):
        headers = self.default_headers

        if self.action_type == ACTION_GET_CATEGORY:
            categories = []
            category_selectors = response.css('table.doctab3 tr.m2 > td > a')
            for selector in category_selectors:
                sub_category_name = selector.css('::text').get()
                url = selector.css('::attr(href)').get()
                full_url = f'{self.base_url}/{url}'

                if sub_category_name:
                    sub_category_name = sub_category_name.replace(' ', '-').replace('&', '-').replace('/', '-')
                else:
                    sub_category_name = ''

                category = {'name': sub_category_name, 'url': full_url}
                categories.append(category)

            for category in categories:
                yield category

        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                with open(self.category_file_path) as f:
                    categories = json.load(f)
                for category in categories:
                    sub_category = category['name']
                    category_url = category['url']

                    item_urls = []

                    request_url = category_url

                    try:
                        res = requests.get(url=request_url, headers=headers)
                    except Exception as e:
                        with open(self.error_file_path, "a") as f:
                            f.write(f'{sub_category}, {request_url}\n')

                    scrapy_selector = Selector(text=res.text)
                    _page_count = scrapy_selector.css("#ecatbody .pagebox > a:last-child::text").get()
                    page_count = int(_page_count) if _page_count else 1

                    f_name = os.path.split(request_url)[1]
                    prefix = f_name.replace('-0.htm', '')

                    referer_url = response.request.url
                    current_page_number = 1
                    while True:
                        headers['referer'] = referer_url
                        self.logger.info(f'Request URL - {request_url}')
                        try:
                            res = requests.get(url=request_url, headers=headers)
                        except Exception as e:
                            with open(self.error_file_path, "a") as f:
                                f.write(f'{sub_category}, {request_url}\n')

                        scrapy_selector = Selector(text=res.text)

                        if self.target_category == 'Строительный_каталог':
                            item_selectors = scrapy_selector.css('#ecatbody .doctab1 tr.m3 > td > a.a2')
                        elif self.target_category == 'Строительная_база':
                            item_selectors = scrapy_selector.css('#ecatbody .doctab1 tr.m3 > td > a:not(.a2)')
                        else:
                            item_selectors = []

                        for item_selector in item_selectors:
                            item_url = item_selector.css('::attr(href)').get()
                            item_url = item_url.replace('..', '')

                            item_url = f'{self.base_url}{item_url}'

                            if item_url in item_urls:
                                self.logger.info(f'List url skipped - {item_url}')
                                continue

                            item_urls.append(item_url)

                            yield {
                                'sub_category': sub_category,
                                'item_url': response.urljoin(item_url)
                            }

                        current_page_number += 1

                        if current_page_number > page_count:
                            break

                        page_number_index = current_page_number - 1

                        next_page_url = f'{self.list_prefix}/{prefix}-{page_number_index}.htm'

                        referer_url = request_url

                        request_url = self.base_url + '/' + next_page_url

                        time.sleep(1)

            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                headers = self.default_headers
                headers['referer'] = response.request.url

                with open(self.list_file_path) as f:
                    item_urls = json.load(f)
                    for item_url_dict in item_urls:
                        url = item_url_dict['item_url']
                        sub_category = item_url_dict['sub_category']
                        item = self.get_items(request_url=url, sub_category=sub_category, headers=headers)

                        if item:
                            yield item

        else:
            pass

    def get_items(self, request_url, sub_category, headers):
        self.logger.info(f'Parse Items - {request_url}')
        try:
            response = requests.get(url=request_url, headers=headers, timeout=30)
        except Exception as e:
            self.logger.info(f'{request_url}: Error - {str(e)}')
            with open(self.error_file_path, "a") as f:
                f.write(f'{sub_category}, {request_url}\n')

            return None
        scrapy_selector = Selector(text=response.text)

        names = scrapy_selector.css('#ecatbody h3::text').getall()
        name = names[1] if len(names) > 1 else ''
        country = ''
        quick_details = ''
        specification = ''
        description = scrapy_selector.css('table.ecattab1').get()

        doc_urls = []

        if self.target_category == 'Строительный_каталог':
            doc_selectors = scrapy_selector.css('#ecatbody b > a')
        elif self.target_category == 'Строительная_база':
            doc_selectors = scrapy_selector.css('h2 > a')
        else:
            doc_selectors = []

        for doc_selector in doc_selectors:
            _doc_url = doc_selector.css('::attr(href)').get()

            if _doc_url:
                if self.target_category == 'Строительная_база':
                    doc_url = self.base_url + _doc_url.replace('../../../', '/')
                else:
                    doc_url = self.base_url + _doc_url.replace('../../', '/')

                if doc_url in doc_urls:
                    continue

                doc_urls.append(doc_url)

        img_urls = []
        video_urls = []

        separator = ';'
        doc_urls_str = separator.join(doc_urls)
        img_urls_str = separator.join(img_urls)
        video_urls_str = separator.join(video_urls)

        media_urls = img_urls + video_urls + doc_urls
        with open(self.media_urls_file_path, "a") as f:
            for url in media_urls:
                f.write(f'{url}\n')

        category = self.target_category

        raw_item = {
            'name': name, 'category': category, 'sub_category': sub_category, 'country': country, 'quick_details': quick_details,
            'description': description, 'specification': specification, 'img_urls_str': img_urls_str,
            'video_urls_str': video_urls_str, 'doc_urls_str': doc_urls_str
        }

        for (k, v) in raw_item.items():
            if v is None:
                raw_item[k] = ''

        loader = ItemLoader(item=FarmMachineryItem())
        loader.add_value('name', name)
        loader.add_value('category', category)
        loader.add_value('sub_category', sub_category)
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
