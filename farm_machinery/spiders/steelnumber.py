import scrapy
from scrapy.loader import ItemLoader
from scrapy.utils.project import get_project_settings

from farm_machinery.items import SteelNumberItem
from utils.logging import ScraperLogger


class SteelNumbersSpider(scrapy.Spider):
    name = 'steelnumber'
    allowed_domains = ['www.steelnumber.com']
    start_urls = [
        'http://www.steelnumber.com/en/number_en10027_eu.php'
    ]

    base_url = 'http://www.steelnumber.com'

    logger = None

    def __init__(self, param):
        super(SteelNumbersSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'referer': 'http://www.steelnumber.com/index.php',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.target_category = param['target_category']
        self.feed_uri = param['feed_uri']
        self.error_file_path = param['error_file_path']

    def start_requests(self):
        url = self.start_urls[0]

        yield scrapy.Request(
            url=url, callback=self.parse, headers=self.default_headers
        )

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        sub_category_selectors = response.css(
            'body > center:nth-child(5) > center:nth-child(7) > table:nth-child(1) > tr'
        )

        for selector in sub_category_selectors:
            sub_category_name = selector.css('td:nth-child(2) > b::text').get()
            serials_selector = selector.css('td:nth-child(3) > table > tr')
            for serial_selector in serials_selector:
                serial_url = serial_selector.css('td > a::attr(href)').get()
                full_serial_url = response.urljoin(serial_url)

                yield scrapy.Request(
                    url=full_serial_url, callback=self.parse_list, headers=headers,
                    meta={'sub_category': sub_category_name}
                )

            # full_serial_url = 'http://www.steelnumber.com/en/number_steel_eu.php?number_kod=1.00'
            # yield scrapy.Request(
            #     url=full_serial_url, callback=self.parse_list, headers=headers,
            #     meta={'sub_category': sub_category_name}
            # )

    def parse_list(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        sub_category = response.meta['sub_category']

        selectors = response.css('form table > tr > td')
        for selector in selectors:
            item_url = selector.css('a::attr(href)').get()

            if item_url:
                full_item_url = response.urljoin(item_url)

                yield scrapy.Request(
                    url=full_item_url, callback=self.parse_items, headers=headers,
                    meta={'sub_category': sub_category}
                )

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        sub_category = response.meta['sub_category']

        scrapy_selector = response.css('body > center:nth-child(9) > center')

        _grade = scrapy_selector.css('table > tr:nth-child(1) > td:nth-child(2)::text').get()
        grade = _grade.strip() if _grade else ''
        _number = scrapy_selector.css('table > tr:nth-child(2) > td:nth-child(2)::text').get()
        number = _number.strip() if _number else ''

        description = response.css('body > center:nth-child(9) > center').get()

        category = self.target_category

        raw_item = {
            'category': category, 'sub_category': sub_category,
            'grade': grade, 'number': number, 'description': description
        }

        for (k, v) in raw_item.items():
            if v is None:
                raw_item[k] = ''

        loader = ItemLoader(item=SteelNumberItem())
        loader.add_value('category', category)
        loader.add_value('sub_category', sub_category)
        loader.add_value('grade', grade)
        loader.add_value('number', number)
        loader.add_value('description', description)
        loader.add_value('item_url', request_url)
        loader.add_value('website', self.base_url)

        item = loader.load_item()

        yield item
