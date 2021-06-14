import json
import time

import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver, scroll_to_bottom
from utils.logging import ScraperLogger


class MachinioSpider(scrapy.Spider):
    name = 'alibaba'
    allowed_domains = ['www.machinio.com']
    start_urls = ['https://www.machinio.com/']

    base_url = 'https://www.machinio.com'

    logger = None

    def __init__(self, param):
        super(MachinioSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='machinio.log').logger

        settings = get_project_settings()
        self.default_headers = settings.get('DEFAULT_REQUEST_HEADERS')

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
        category_url = 'https://www.machinio.com/oil-gas-mining'
        headers = self.default_headers
        headers['referer'] = response.request.url

        yield scrapy.Request(
            url=category_url, callback=self.parse_categories, headers=headers
        )

    def parse_categories(self, response):
        if self.action_type == ACTION_GET_CATEGORY:
            categories = []
            category_selectors = response.css('.filters-block')[0].css('li')
            for selector in category_selectors:
                name = selector.css('a::text').get()
                url = selector.css('a::attr(href)').get()
                url = f'{self.base_url}{url}'

                modified_name = name.replace(' ', '-').replace('&', '-')
                category = {'name': modified_name, 'url': url}
                categories.append(category)

            for category in categories:
                yield category

            # write_results_to_json(feed_uri=self.feed_uri, item_urls=categories)

        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                with open(self.category_file_path) as f:
                    categories = json.load(f)
                for category in categories:
                    category_name = category['name']
                    category_url = category['url']
                    if category_name == self.target_category:
                        category_full_url = f'{category_url}'

                        driver = initialize_chrome_driver()
                        driver.get(url=category_full_url)
                        page_source = scroll_to_bottom(driver, time_delay=5)
                        scrapy_selector = Selector(text=page_source)

                        driver.close()

                        item_selectors = scrapy_selector.css(
                            '.search-results-page > ul > li'
                        )
                        item_urls = []
                        for item_selector in item_selectors:
                            item_url = item_selector.css(
                                '.offer-listing__image-wrapper > a::attr(href)'
                            ).get()

                            if item_url in item_urls:
                                continue

                            item_urls.append(item_url)

                            yield {
                                'item_url': response.urljoin(item_url)
                            }

                        # write_results_to_json(feed_uri=self.feed_uri, item_urls=item_urls)

            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                headers = self.default_headers
                headers['referer'] = response.request.url

                # url = "https://www.machinio.com/listings/32272671-pot-mixer-nikko-concrete-fertilizer-ngm-2-5-capacity-70-l-200-v-in-tsuruoka-japan"

                # yield scrapy.Request(
                #     url=url, callback=self.parse_items, headers=headers,
                #     meta={'category': self.target_category}
                # )

                with open(self.list_file_path) as f:
                    item_urls = json.load(f)
                    for item_url_dict in item_urls:
                        url = item_url_dict['item_url']

                        yield scrapy.Request(
                            url=url, callback=self.parse_items, headers=headers,
                            meta={'category': self.target_category}
                        )

                        time.sleep(3)
        else:
            pass

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        category = response.meta['category']
        name = response.css('h1::text').get()
        country = response.css('.listing-details .listing-info .spec > dd::text').get()
        quick_details = ''
        specification = response.css('.specifications-box .specification-list > div').get()
        description = response.css('.description-box .description').get()

        thumb_img_selectors = response.css('ul.carousel__content > li img')
        thumb_img_urls = []
        for img_selector in thumb_img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            lazy_img_url = img_selector.css('::attr(lazy-src)').get()

            img_url = img_url if img_url else lazy_img_url

            if img_url:
                if img_url in thumb_img_urls:
                    continue

                thumb_img_urls.append(img_url)

        img_urls = thumb_img_urls
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

        yield item

    def download_files(self, response):
        self.logger.info('File Saving Handler !!!')
        file_name = os.path.split(response.request.url)[1]

        file_save_path = os.path.join(OUTPUT_DIR, file_name)

        with open(file_save_path, 'wb') as f:
            f.write(response.body)
            self.logger.info('Saving File %s', file_save_path)
