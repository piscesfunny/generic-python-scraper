import os
import time
import csv

import requests
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem


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

        yield scrapy.Request(
            url=self.category_url, callback=self.parse_list, headers=headers
        )

    def parse_list(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        # self.logger.info(f'Parse List - {response.request.url}')

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
                request_url = f'{main_url}?pages={page_number}'

                r = requests.get(url=request_url, headers=headers, timeout=30)
                # self.logger.info(f'Current page url: {request_url}')
                print(f'Current page url: {request_url}')

                time.sleep(5)

                headers['referer'] = f'{main_url}?pages={page_number}'

                selector = Selector(text=r.text)
                products_per_page = selector.css('#datas > div')
                for product in products_per_page:
                    item_url = product.css('a::attr(href)').get()
                    with open(self.item_url_file_path, 'a') as csv_file_:
                        file_writer = csv.writer(csv_file_, delimiter=',')
                        file_writer.writerow([item_url])
                with open(self.processed_page_path, 'a') as csv_file_:
                    file_writer = csv.writer(csv_file_, delimiter=',')
                    file_writer.writerow([page_number])
            except Exception as err:
                # self.logger.info(f'Error page number: {page_number}')
                print(f'Error page number: {page_number}, {err}')
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
        for item_url_dict in item_urls:
            if item_url_dict in processed_urls:
                continue
            if item_url_dict[0] == "":
                continue
            url = item_url_dict[0]
            item = self.parse_items(request_url=url, category=self.category, headers=headers)
            yield item
            time.sleep(10)

    def parse_items(self, request_url, category, headers):
        # self.logger.info(f'Parse Items - {request_url}')
        print(f'Parse Items - {request_url}')
        r = requests.get(url=request_url, headers=headers, timeout=30)
        response = Selector(text=r.text)
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
        with open(self.processed_url_path, 'a') as csv_file_:
            file_writer = csv.writer(csv_file_, delimiter=',')
            file_writer.writerow([request_url])

        return item
