import scrapy
from scrapy.loader import ItemLoader

from farm_machinery.items import SteelNumberItem
from utils.logging import ScraperLogger


class SteelGradingSpider(scrapy.Spider):
    name = 'steel_grading'
    allowed_domains = ['steeljis.com']
    start_urls = [
        'http://steeljis.com/jis_steel_designation.php'
    ]

    base_url = 'http://steeljis.com'

    logger = None

    def __init__(self, param):
        super(SteelGradingSpider, self).__init__()

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

        category_selector = response.css(
            'body > center:nth-child(4) > table:nth-child(1) > tr > td a'
        )

        for selector in category_selector:
            url = selector.css('::attr(href)').get()
            sub_category = selector.css('::text').get()

            yield scrapy.Request(
                url=url, callback=self.parse_list, headers=headers, meta={'sub_category': sub_category}
            )

    def parse_list(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        category = response.meta['sub_category']

        selectors = response.css('body > form > center > table:nth-child(4) > tr')
        selectors.pop(0)
        for selector in selectors:
            grade = selector.css('td:nth-child(1) > a > b::text').get()
            standards = selector.css('td:nth-child(2) > table > tr > td::text').get()
            item_url = selector.css('a::attr(href)').get()

            yield scrapy.Request(
                url=item_url, callback=self.parse_items, headers=headers,
                meta={'category': category, 'grade': grade, 'standards': standards}
            )

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        category = response.meta['category']
        grade = response.meta['grade']
        standards = response.meta['standards']

        description1 = response.css('body > center:nth-child(5)').get()
        description2 = response.css('body > center:nth-child(6)').get()
        description = description1 + description2

        raw_item = {
            'category': category, 'grade': grade, 'standards': standards, 'description': description
        }

        for (k, v) in raw_item.items():
            if v is None:
                raw_item[k] = ''

        loader = ItemLoader(item=SteelNumberItem())
        loader.add_value('category', category)
        loader.add_value('grade', grade)
        loader.add_value('standards', standards)
        loader.add_value('description', description)
        loader.add_value('item_url', request_url)
        loader.add_value('website', self.base_url)

        item = loader.load_item()

        yield item
