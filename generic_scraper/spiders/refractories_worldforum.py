import scrapy
from scrapy.loader import ItemLoader

from generic_scraper.items import RefractoryWorldFormItem
from utils.logging import ScraperLogger


class RefractoriesWorldForumSpider(scrapy.Spider):
    name = 'refractories_worldforum'
    allowed_domains = ['www.refractories-worldforum.com']
    start_urls = [
        'https://www.refractories-worldforum.com'
    ]

    base_url = 'https://www.refractories-worldforum.com'

    logger = None

    def __init__(self, param):
        super(RefractoriesWorldForumSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'referer': 'http://www.steelnumber.com/index.php',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.target_category = f"/departments/{param['target_category']}"
        self.feed_uri = param['feed_uri']
        self.error_file_path = param['error_file_path']
        self.page_count = int(param['page_count'])

        self.item_urls = []

    def start_requests(self):
        url = self.start_urls[0]

        yield scrapy.Request(
            url=url, callback=self.parse, headers=self.default_headers
        )

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        category_selector = response.css(
            '#navbarContent1 > li.nav-item.item-107.deeper.parent.dropdown > div > a'
        )

        for selector in category_selector:
            url = selector.css('::attr(href)').get()
            department = selector.css('::text').get()

            if url == self.target_category:
                full_url = response.urljoin(url) + '?page=1'

                yield scrapy.Request(
                    url=full_url, callback=self.parse_list, headers=headers, meta={'department': department}
                )

    def parse_list(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        department = response.meta['department']

        selectors = response.css('div.content-left > div > div > div > div > div.col-lg-8.col-sm-12 > div.news-item')
        for selector in selectors:
            title = selector.css('h2::text').get()
            quick_description = selector.css('p::text').get()
            item_url = selector.css('a::attr(href)').get()
            full_item_url = response.urljoin(item_url)

            self.item_urls.append(full_item_url)

            yield scrapy.Request(
                url=full_item_url, callback=self.parse_items, headers=headers,
                meta={'department': department, 'title': title, 'quick_description': quick_description}
            )

        current_page_number = int(response.request.url.split('page=')[1])
        if current_page_number < self.page_count:
            next_page_number = current_page_number + 1
            next_page_url = response.request.url.replace(f'page={current_page_number}', f'page={next_page_number}')

            yield scrapy.Request(
                url=next_page_url, callback=self.parse_list, headers=headers,
                meta={'department': department}
            )

    def parse_items(self, response):
        request_url = response.request.url
        self.logger.info(f'Parse Items - {request_url}')

        department = response.meta['department']
        title = response.meta['title']
        quick_description = response.meta['quick_description']

        description = response.css('div.news-item-full > p.news-date + p::text').get()

        _doc_path = response.css('div.news-item-full > p:last-child > a::attr(href)').get()
        doc_path = response.urljoin(_doc_path)

        raw_item = {
            'department': department, 'title': title, 'quick_description': quick_description, 'description': description,
            'doc_path': doc_path
        }

        for (k, v) in raw_item.items():
            if v is None:
                raw_item[k] = ''

        loader = ItemLoader(item=RefractoryWorldFormItem())
        loader.add_value('department', department)
        loader.add_value('title', title)
        loader.add_value('quick_description', quick_description)
        loader.add_value('description', description)
        loader.add_value('doc_path', doc_path)
        loader.add_value('item_url', request_url)
        loader.add_value('website', self.base_url)

        item = loader.load_item()

        yield item
