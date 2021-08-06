import json
import time
import csv

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.helpers import initialize_chrome_driver, scroll_to_bottom


class AlibabaSpider(scrapy.Spider):
    name = 'alibaba'
    allowed_domains = ['www.alibaba.com']
    start_urls = ['http://www.alibaba.com/']

    logger = None

    def __init__(self, param):
        super(AlibabaSpider, self).__init__()

        # self.logger = ScraperLogger(label='SPIDER', log_file='alibaba.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

        # self.action_type = param['action_type']
        # self.target_category = param['target_category']
        # self.scraping_target = param['scraping_target']
        self.item_url_file_path = param['item_url_file_path']
        self.media_urls_file_path = param['media_urls_file_path']
        self.category = param['sub_category']
        self.category_url = param['sub_category_url']
        self.processed_url_path = param['processed_url_path']
        self.processed_page_path = param["processed_page_path"]
        self.total_page_count = 100
        self.start_page_number = 1

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers
            )

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        yield scrapy.Request(
            url=self.category_url, callback=self.parse_list_one, headers=headers
        )

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
        # self.logger.info(f'Parse List - {response.request.url}')
        print(f'Parse List - {response.request.url}')

        # main_url = 'https://www.alibaba.com/catalog/transformers_cid141907'
        main_url = self.category_url
        if not os.path.exists(self.processed_page_path):
            with open(self.processed_page_path, 'w') as csv_file:
                csv.writer(csv_file, delimiter=',')
                processed_pages = []
        else:
            with open(self.processed_page_path, newline='') as f:
                reader = csv.reader(f)
                processed_pages = list(reader)
        if not os.path.exists(self.item_url_file_path):
            with open(self.item_url_file_path, 'w') as csv_file:
                csv.writer(csv_file, delimiter=',')

        for page_number in range(self.start_page_number, self.total_page_count+1):
            try:
                if [str(page_number)] in processed_pages:
                    continue
                print(f"Current Page: {page_number}")
                request_url = f'{main_url}?page={page_number}&ISJSON=1&_bx-v=1.1.20'

                r = requests.get(url=request_url, headers=headers, timeout=30)
                # self.logger.info(f'Current page url: {request_url}')
                print(f'Current page url: {request_url}')

                offer_result_count_str = json.loads(r.text).get('offerResultData').get('totalCount')
                offer_result_count = int(offer_result_count_str) if offer_result_count_str else 0
                if offer_result_count == 0:
                    time.sleep(120)
                    # self.logger.info(f'Waiting 120s...')
                    print(f'Waiting 120s...')
                    r = requests.get(url=request_url, headers=headers, timeout=30)
                    offer_result_count_str_two = json.loads(r.text).get('offerResultData').get('totalCount')
                    offer_result_count_two = int(offer_result_count_str_two) if offer_result_count_str_two else 0

                    if offer_result_count_two == 0:
                        time.sleep(300)
                        # self.logger.info(f'Waiting 300s...')
                        print(f'Waiting 300s...')
                        r = requests.get(url=request_url, headers=headers, timeout=30)
                else:
                    time.sleep(5)

                headers['referer'] = f'{main_url}?page={page_number}&ISJSON=1&_bx-v=1.1.20'

                data = json.loads(r.text)
                products_per_page = data.get('offerResultData').get('offerList')
                for product in products_per_page:
                    item_url = product.get('information').get('productUrl')
                    with open(self.item_url_file_path, 'a') as csv_file_:
                        file_writer = csv.writer(csv_file_, delimiter=',')
                        file_writer.writerow(["https:" + item_url])
                        # file_writer.writerow([item_url])
                with open(self.processed_page_path, 'a') as csv_file_:
                    file_writer = csv.writer(csv_file_, delimiter=',')
                    file_writer.writerow([page_number])

            except Exception as e:
                # self.logger.info(f'Error page number: {page_number}')
                print(f'Error page number: {page_number}, {e}')
                break
        with open(self.item_url_file_path, newline='') as f:
            reader = csv.reader(f)
            item_urls = list(reader)
        if not os.path.exists(self.processed_url_path):
            with open(self.processed_url_path, 'w') as csv_file:
                csv.writer(csv_file, delimiter=',')
                processed_urls = []
        else:
            with open(self.processed_url_path, newline='') as f:
                reader = csv.reader(f)
                processed_urls = list(reader)
        driver = initialize_chrome_driver()
        for item_url_dict in item_urls:
            if item_url_dict in processed_urls:
                continue
            if item_url_dict[0] == "":
                continue
            url = item_url_dict[0]
            item = self.get_item_detail_one(
                request_url=url, category=self.category, driver=driver, scrapy_response=response
            )
            yield item
            time.sleep(1)
        driver.close()

    def get_item_detail_one(self, request_url, category, driver, scrapy_response):
        # self.logger.info(f'Parse Items - {request_url}')
        print(f'Parse Items - {request_url}')
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
        with open(self.processed_url_path, 'a') as csv_file_:
            file_writer = csv.writer(csv_file_, delimiter=',')
            file_writer.writerow([request_url])

        return item
