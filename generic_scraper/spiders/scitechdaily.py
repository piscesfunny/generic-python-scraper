import time

import pyautogui as pyautogui
import scrapy

from utils.constants import ACTION_DOWNLOAD, ACTION_GET_LIST
from utils.helpers import initialize_chrome_driver, write_results_to_txt
from utils.logging import ScraperLogger


class SciTechDailySpider(scrapy.Spider):
    name = 'scitechdaily'
    allowed_domains = ['scitechdaily.com']
    start_urls = []

    base_url = 'https://scitechdaily.com'

    logger = None

    def __init__(self, param):
        super(SciTechDailySpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger
        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.target_category = param['target_category']
        self.list_file_path = param['list_file_path']
        self.failed_file_path = param['failed_file_path']
        self.success_file_path = param['success_file_path']

        self.category_url = f'{self.base_url}/news/{self.target_category}'
        self.start_urls.append(self.category_url)
        self.category_item_count = 1
        self.failed_urls = []

    def start_requests(self):
        if self.action_type == ACTION_GET_LIST:
            for url in self.start_urls:
                yield scrapy.Request(url=url, callback=self.parse, headers=self.default_headers)
        elif self.action_type == ACTION_DOWNLOAD:
            with open(self.list_file_path, 'r') as f:
                urls = f.readlines()

                self.get_items(urls)

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        archive_list_selector = response.css('#main-content article.content-list')

        urls = []
        for archive_selector in archive_list_selector:
            date = archive_selector.css('.content-list-header .entry-meta .entry-meta-date::text').get()
            if date:
                year = date.split(', ')[-1]
                year = int(year)
            else:
                year = 1900

            if year < 2016:
                return

            url = archive_selector.css('.content-thumb a::attr(href)').get()
            urls.append(url)

        write_results_to_txt(feed_uri=self.list_file_path, item_urls=urls, f_open_mode='a')

        next_page_selector = response.css('div.pagination a.next.page-numbers')
        if next_page_selector:
            next_page_url = next_page_selector.css('::attr(href)').get()
            yield scrapy.Request(url=next_page_url, callback=self.parse, headers=headers)

    def get_items(self, urls):
        failed_urls = []
        headers = self.default_headers
        headers['referer'] = self.category_url

        driver = initialize_chrome_driver(maximized=False, printable=True)

        for url in urls:
            try:
                driver.get(url)
                time.sleep(5)

                all_iframes = driver.find_elements_by_tag_name("iframe")
                if len(all_iframes) > 0:
                    print("Ad Found\n")
                    driver.execute_script("""
                        var elems = document.getElementsByTagName("iframe"); 
                        for(var i = 0, max = elems.length; i < max; i++)
                             {
                                 elems[i].hidden=true;
                             }
                                          """)
                    print('Total Ads: ' + str(len(all_iframes)))
                else:
                    print('No frames found')

                time.sleep(2)

                driver.execute_script('window.print();')

                time.sleep(5)

                self.logger.info(f'success_url: {url}')
                print(f'success_url: {url}')

            except Exception as e:
                self.logger.info(f'Error: {url}')
                self.logger.info(str(e))
                failed_urls.append(url)

        if len(failed_urls) > 0:
            write_results_to_txt(feed_uri=self.failed_file_path, item_urls=failed_urls, f_open_mode="a")
