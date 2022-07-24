import time

import requests
import scrapy
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver, write_results_to_csv, read_file, \
    write_results_to_txt, download_image_by_wget
from utils.logging import ScraperLogger


class GeneralKinematicsSpider(scrapy.Spider):
    name = 'generalkinematics'
    allowed_domains = ['www.generalkinematics.com']
    start_urls = ['https://www.generalkinematics.com/']

    base_url = 'https://www.generalkinematics.com'

    logger = None

    def __init__(self, param):
        super(GeneralKinematicsSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        settings = get_project_settings()
        self.default_headers = self.default_headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.scraping_target = param['scraping_target']
        self.category_file_path = param['category_file_path']
        self.result_list_suc_f_path = param['result_list_suc_f_path']
        self.result_list_err_f_path = param['result_list_err_f_path']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url

        category_urls = [
            'https://www.generalkinematics.com/vibrating-conveyors',
            'https://www.generalkinematics.com/cooling-and-drying',
            'https://www.generalkinematics.com/vibrating-feeders',
            'https://www.generalkinematics.com/grinding',
            'https://www.generalkinematics.com/gk-rotary-equipment',
            'https://www.generalkinematics.com/vibrating-screens',
            'https://www.generalkinematics.com/product/de-stoner',
            'https://www.generalkinematics.com/product/finger-screen-primary-vibratory-screen',
            'https://www.generalkinematics.com/product/stm-screens',
            'https://www.generalkinematics.com/product/sand-casting-equipment'
        ]

        if self.scraping_target == SCRAPPING_TARGET_LIST:
            items = []
            for category_url in category_urls:
                category_name = os.path.split(category_url)[1]
                res = requests.get(url=category_url, headers=headers)
                scrapy_selector = Selector(text=res.text)
                item_selectors = scrapy_selector.css(
                    'div.entry-content > div.cat_image > div.wpb_column.vc_column_container.vc_col-sm-3')
                for item_selector in item_selectors:
                    item_url = item_selector.css('div.vc_column-inner > div.wpb_wrapper > div.wpb_single_image a::attr(href)').get()
                    if item_url:
                        items.append({'category': category_name, 'item_url': item_url})
                self.logger.info(f'Get list - category: {category_name} - item count: {len(item_selectors)}')
                print(f'Get list - category: {category_name} - item count: {len(item_selectors)}')
                time.sleep(1)

            write_results_to_csv(self.result_list_suc_f_path, items)
        elif self.scraping_target == SCRAPPING_TARGET_ITEM:
            items = read_file(self.result_list_suc_f_path)

            self.get_items(items)
        else:
            pass

    def get_items(self, items):
        driver = None
        progress_f_path = os.path.join(OUTPUT_DIR, 'progress_drugs.txt')
        processed_item_urls = read_file(progress_f_path, file_format="txt")

        for item in items:
            category = item.get('category')
            item_url = item.get('item_url')

            if item_url in processed_item_urls:
                self.logger.info(f'Skipped url: {item_url}')
                print(f'Skipped url: {item_url}')
                continue

            item_name = item_url.split('/')[-2]

            category_dir = os.path.join(OUTPUT_RESULT_DIR, category)
            save_dir = os.path.join(category_dir, item_name)
            os.makedirs(save_dir, exist_ok=True)

            driver = initialize_chrome_driver(maximized=False, printable=True, save_dir=save_dir)

            driver.get(item_url)
            time.sleep(2)

            scrapy_selector = Selector(text=driver.page_source)

            img_selectors = scrapy_selector.css('div.imgdiv ol li img')
            img_urls = []
            for img_selector in img_selectors:
                url = img_selector.css('::attr(src)').get()
                if url:
                    url = url.replace('-100x100', '')
                img_urls.append(url)

            video_selectors = scrapy_selector.css('div.video-container')
            video_urls = []
            for video_selector in video_selectors:
                url = video_selector.css('iframe::attr(src)').get()
                video_urls.append(url)

            driver.execute_script('window.print();')

            time.sleep(5)

            # f_path = os.path.join(save_dir, 'videos.txt')
            # if len(video_urls) > 0:
            #     write_results_to_txt(f_path, video_urls, f_open_mode="w")

            img_failed_f_path = os.path.join(save_dir, 'img_failed.txt')
            if len(img_urls) > 0:
                download_image_by_wget(img_urls, save_dir, img_failed_f_path)

            item_urls = [item_url]
            write_results_to_txt(progress_f_path, item_urls, f_open_mode="a")

            self.logger.info(f'success_url: {item_url}')
            print(f'success_url: {item_url}')

            driver.close()