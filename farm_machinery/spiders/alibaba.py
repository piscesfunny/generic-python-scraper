import time
import scrapy

from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers
            )

    def parse(self, response):
        url = 'https://www.alibaba.com/machinery/agricultural-machinery-equipment/p43_p100010631?spm=a27aq.13891069.scGlobalHomeHeader.381.5e015736OReuU7'
        headers = self.default_headers
        headers['referer'] = response.request.url

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

        category_selectors = response.css('.industry-category-tree > .nav')
        for selector in category_selectors:
            name = selector.css('.name > a::text').get()
            url = selector.css('.name > a::attr(href)').get()

            if name in non_target_category_names:
                continue

            categories.append({
                'name': name,
                'url': url,
            })

        headers = self.default_headers
        headers['referer'] = response.request.url

        for category in categories:
            category_name = category['name']
            category_url = category['url']
            if category_name == 'Tractors':
                category_full_url = f'{category_url}?spm=a27aq.13891069.1148563840.43.31fe5df94lgO5F'

                # driver = self.initialize_chrome_driver()
                # driver.get(url=category_full_url)
                # page_source = self.scrollToBottom(driver)
                # page_source = driver.page_source

                # scrapy_selector = Selector(text=page_source)

                # driver.close()

                # item_selectors = scrapy_selector.css('.listbase > .grid-list-flex .grid-col-item-wrapper')

                # for item_selector in item_selectors:
                #     _item_url = item_selector.css('.grid-col-item > .hg-product > a.product-detail::attr(href)').get()
                #     item_url = response.urljoin(_item_url)
                #
                #     yield scrapy.Request(
                #         url=item_url, callback=self.parse_items, headers=headers,
                #         meta={'category': category_name}
                #     )

                item_url = 'https://www.alibaba.com/product-detail/High-efficiency-tractors-price-120HP-4wd_62520569148.html?spm=a27aq.13891069.2.1.138b5736ERnxoY'
                yield scrapy.Request(
                        url=item_url, callback=self.parse_items, headers=headers,
                        meta={'category': category_name}
                    )

    def parse_items(self, response):
        category = response.meta['category']
        name = response.css('.ma-title::text').get()

        thumb_img_selectors = response.css('.widget-detail-booth-image .thumb img')
        thumb_img_urls = []
        for img_selector in thumb_img_selectors:
            img_url = img_selector.css('::attr(src)').get()
            img_url.replace('.jpg_50x50', '')
            thumb_img_urls.append(img_url)

        thumb_video_selectors = response.css('.widget-detail-booth-image video')
        thumb_video_urls = []
        for video_selector in thumb_video_selectors:
            video_url = video_selector.css('::attr(src)').get()
            thumb_video_urls.append(video_url)

        quick_detail = response.css('.widget-detail-overview .do-entry-separate').get()

        detail_img_selectors = response.css('.richtext-detail.rich-text-description img')
        detail_img_urls = []
        for selector in detail_img_selectors:
            img_url = selector.css('::attr(data-src)').get()
            if img_url:
                detail_img_urls.append(img_url)

        specification = response.css('.richtext-detail.rich-text-description table').get()

        pass

    def initialize_chrome_driver(self):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        desired_capabilities = options.to_capabilities()

        # driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', chrome_options=options)
        driver = webdriver.Chrome(desired_capabilities=desired_capabilities)

        return driver

    def scrollToBottom(self, driver, scroll_pause_time=5):
        total_height = 0
        distance = 600

        while True:
            # Get scroll height
            last_height = driver.execute_script("return document.body.scrollHeight")
            # Scroll down to bottom
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            driver.execute_script("window.scrollBy({left: 0, top: 600, behavior: 'smooth'});")
            total_height += distance

            # Wait to load page
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with last scroll height
            # new_height = driver.execute_script("return document.body.scrollHeight")
            # if new_height == last_height:
            #     # If heights are the same it will exit the function
            #     break
            # last_height = new_height

            if total_height > last_height:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                break

        return driver.page_source
