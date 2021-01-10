import os

from scrapy.crawler import CrawlerProcess
from utils.config import *
from utils.constants import *
from farm_machinery.spiders.alibaba import AlibabaSpider


def start_scrapper(existing_fns, action_type, target_category=None, scraping_target=None):
    site_name = 'alibaba'
    if action_type == ACTION_GET_CATEGORY:
        feed_format = 'json'
        feed_uri = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    elif action_type == ACTION_SCRAPPING:
        if scraping_target == SCRAPPING_TARGET_LIST:
            feed_format = 'json'
            feed_uri = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
        else:
            feed_format = 'json'
            feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_result_{target_category}.{feed_format}')
    else:
        pass

    list_file_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls.txt')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    if os.path.exists(media_urls_file_path):
        os.remove(media_urls_file_path)

    settings = {
        'FEED_FORMAT': feed_format,
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    process = CrawlerProcess(settings=settings)

    process.crawl(AlibabaSpider, param={
        'existing_fns': existing_fns,
        'action_type': action_type,
        'target_category': target_category,
        'scraping_target': scraping_target,
        'list_file_path': list_file_path,
        'media_urls_file_path': media_urls_file_path,
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
