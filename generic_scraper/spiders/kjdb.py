import random
import re
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


class KJDBSpider(scrapy.Spider):
    name = 'kjbd'
    allowed_domains = ['www.kjdb.org']
    start_urls = ['http://www.kjdb.org/']

    base_url = 'http://www.kjdb.org'

    logger = None

    def __init__(self, param):
        super(KJDBSpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        settings = get_project_settings()
        self.default_headers = self.default_headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.target_start_num = int(param['target_start_num'])
        self.target_end_num = int(param['target_end_num'])
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

        category_urls = []
        for i in range(self.target_start_num, self.target_end_num + 1):
            category_urls.append(f"http://www.kjdb.org/CN/volumn/volumn_{i}.shtml")

        if self.scraping_target == SCRAPPING_TARGET_LIST:
            for category_url in category_urls:
                items = []
                res = requests.get(url=category_url, headers=headers)
                scrapy_selector = Selector(text=res.text)
                year_issue_str = scrapy_selector.css('span.STYLE36 > strong::text').get()
                year_issue_str = re.sub(r"[\u4e00-\u9fff]+", "", year_issue_str)
                year_issue_str = year_issue_str.replace(" ", "-")

                item_selectors = scrapy_selector.css('div.noselectrow')
                for item_selector in item_selectors:
                    item_str = item_selector.css('a.txt_zhaiyao1::attr(onclick)').get()
                    item_ids = re.findall(r'\d+', item_str)
                    if len(item_ids) > 0:
                        item_id = item_ids[0]
                        items.append(f"{self.base_url}/CN/article/downloadArticleFile.do?attachType=PDF&id={item_id}")
                self.logger.info(f'Get list - year_issue: {year_issue_str}')
                print(f'Get list - year_issue: {year_issue_str}')
                time.sleep(random.randint(3, 5))

                f_path = os.path.join(OUTPUT_LIST_DIR, f"{year_issue_str}.txt")
                write_results_to_txt(f_path, items)
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