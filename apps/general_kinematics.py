import os
import threading

import wget
from scrapy.crawler import CrawlerProcess
from utils.config import *
from utils.constants import *
from generic_scraper.spiders.parts_cat import PartsCatSpider
from utils.logging import ScraperLogger


def start_scrapper(site_name, action_type, target_category=None, scraping_target=None):
    logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger
    feed_format = 'csv'

    if scraping_target == SCRAPPING_TARGET_LIST:
        feed_uri = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
    else:
        feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_result.{feed_format}')

    logger.info(f'feed_uri: {feed_uri}')

    category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    result_list_suc_f_path = os.path.join(OUTPUT_DIR, f'{site_name}_list.{feed_format}')
    result_list_err_f_path = os.path.join(OUTPUT_DIR, f'{site_name}_list_err.{feed_format}')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    process = CrawlerProcess()

    process.crawl(PartsCatSpider, param={
        'action_type': action_type,
        'target_category': target_category,
        'scraping_target': scraping_target,
        'category_file_path': category_file_path,
        'result_list_suc_f_path': result_list_suc_f_path,
        'result_list_err_f_path': result_list_err_f_path
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
