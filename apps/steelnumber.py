from scrapy.crawler import CrawlerProcess

from farm_machinery.spiders.steelnumber import SteelNumbersSpider
from utils.config import *
from utils.logging import ScraperLogger


def start_scrapper(site_name, target_category=None):
    logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger

    feed_format = 'json'
    feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_result.{feed_format}')

    logger.info(f'feed_uri: {feed_uri}')

    error_file_path = os.path.join(OUTPUT_FAILED_DIR, f'{site_name}_{target_category}_error_urls.txt')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    settings = {
        'FEED_FORMAT': feed_format,
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    process = CrawlerProcess(settings=settings)

    process.crawl(SteelNumbersSpider, param={
        'target_category': target_category,
        'feed_uri': feed_uri,
        'error_file_path': error_file_path
    })

    process.start()
