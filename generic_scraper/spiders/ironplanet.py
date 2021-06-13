import json
import time

import requests
import scrapy
from scraper_api import ScraperAPIClient
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium.common.exceptions import NoSuchElementException

from generic_scraper.items import FarmMachineryItem
from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver
from utils.logging import ScraperLogger


class IronPlanetSpider(scrapy.Spider):
    name = 'ironplanet'
    allowed_domains = ['www.ironplanet.com']
    start_urls = ['https://www.ironplanet.com/equipment-types.ips#ctag2']

    base_url = 'https://www.ironplanet.com'

    logger = None

    def __init__(self, param):
        super(IronPlanetSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file='ironplanet.log').logger

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
            category_selectors = response.css('.row.sr-ctgry-box')[0].css('div.sr-ctgry-links')
            for selector in category_selectors:
                name = selector.css('a::text').get()
                url = selector.css('a::attr(href)').get()
                url = f'{self.base_url}{url}'

                modified_name = name.replace(' ', '-').replace('&', '-').replace('/', '-')
                category = {'name': modified_name, 'url': url}
                categories.append(category)
            for category in categories:
                yield category

        elif self.action_type == ACTION_SCRAPPING:
            if self.scraping_target == SCRAPPING_TARGET_LIST:
                with open(self.category_file_path) as f:
                    categories = json.load(f)
                for category in categories:
                    category_name = category['name']
                    category_url = category['url']
                    if category_name == self.target_category:
                        while True:
                            headers['referer'] = category_url

                            res = requests.get(url=category_url, headers=headers)
                            scrapy_selector = Selector(text=res.text)
                            item_selectors = scrapy_selector.css(
                                'div.sr_grid_container > div:not(#sr_next_elem_links) > div.sr_grid_tile.sr_item'
                            )

                            item_urls = []
                            for item_selector in item_selectors:
                                item_url = item_selector.css(
                                    '.sr_grid_photo > .sr_photo_container > a::attr(href)'
                                ).get()

                                if 'https://www.rbauction.com' in item_url:
                                    continue

                                item_url = f'{self.base_url}{item_url}'

                                item_img = item_selector.css(
                                    '.sr_grid_photo > .sr_photo_container > a img::attr(data-original)'
                                ).get()

                                if 'space.gif' in item_img:
                                    continue

                                if item_url in item_urls:
                                    continue

                                item_urls.append(item_url)

                                yield {
                                    'item_url': response.urljoin(item_url)
                                }

                            next_page_elem = scrapy_selector.css(
                                '.sr_page_number_controls span.sr_page_numbers > a.sr_pagination:last-child'
                            ).get()

                            if not next_page_elem:
                                break

                            next_page_url = scrapy_selector.css(
                                '.sr_page_number_controls span.sr_page_numbers > a.sr_pagination:last-child::attr(href)'
                            ).get()

                            category_url = self.base_url + next_page_url

                            time.sleep(1)

            elif self.scraping_target == SCRAPPING_TARGET_ITEM:
                headers = self.default_headers
                headers['referer'] = response.request.url

                driver = initialize_chrome_driver()

                with open(self.list_file_path) as f:
                    item_urls = json.load(f)
                    for item_url_dict in item_urls:
                        url = item_url_dict['item_url']

                        item = self.get_items(request_url=url, category=self.target_category, driver=driver)

                        yield item

                        time.sleep(1)

                driver.close()
        else:
            pass

    def get_items(self, request_url, category, driver):
        self.logger.info(f'Parse Items - {request_url}')
        driver.get(url=request_url)
        try:
            driver.find_element_by_css_selector('div.nopadding.smallPhotoMore').click()
        except NoSuchElementException as exception:
            self.logger.info(f"Exception - {exception}")

        scrapy_selector = Selector(text=driver.page_source)

        name = scrapy_selector.css('h1.itemdesc::text').get()
        country = scrapy_selector.xpath(
            '//*[@id="content"]/div[3]/div/div[1]/div/div[3]/div[2]/div[4]/div/div/div[2]/div/text()'
        ).get()

        quick_details = ''
        specification = ''
        description = scrapy_selector.css('#inspectreportdiv').get()

        img_count = len(scrapy_selector.css('ul.carousel-items > li > img'))
        for i in range(0, img_count):
            try:
                driver.find_element_by_css_selector('a.next.next-stage').click()
            except NoSuchElementException as exception:
                self.logger.info(f"Exception - {exception}")

            time.sleep(0.5)

        scrapy_selector = Selector(text=driver.page_source)

        if img_count > 0:
            thumb_img_selectors = scrapy_selector.css('ul.carousel-items > li > img')
        else:
            thumb_img_selectors = scrapy_selector.css('div.row.smallPhotos > div > img.thumbnailImage')

        thumb_img_urls = []
        for img_selector in thumb_img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            lazy_img_url = img_selector.css('::attr(lazy-src)').get()

            img_url = img_url if img_url else lazy_img_url

            if img_url:
                if img_url in thumb_img_urls:
                    continue

                normal_img_url = img_url.replace('-small', '')
                thumb_img_urls.append(normal_img_url)

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



        return item
