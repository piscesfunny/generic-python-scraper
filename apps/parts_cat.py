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
    if action_type == ACTION_GET_CATEGORY:
        feed_uri = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    elif action_type == ACTION_SCRAPPING:
        if scraping_target == SCRAPPING_TARGET_LIST:
            feed_uri = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
        else:
            feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_result.{feed_format}')
    else:
        pass

    logger.info(f'feed_uri: {feed_uri}')

    category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    # list_file_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
    result_list_suc_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
    result_list_err_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list_err.{feed_format}')
    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls.txt')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    if os.path.exists(media_urls_file_path):
        os.remove(media_urls_file_path)

    process = CrawlerProcess()

    process.crawl(PartsCatSpider, param={
        'action_type': action_type,
        'target_category': target_category,
        'scraping_target': scraping_target,
        'category_file_path': category_file_path,
        'result_list_suc_f_path': result_list_suc_f_path,
        'result_list_err_f_path': result_list_err_f_path,
        'media_urls_file_path': media_urls_file_path,
        'feed_uri': feed_uri
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
