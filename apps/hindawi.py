from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.hindawi import HindawiSpider
from utils.config import *
from utils.logging import ScraperLogger


def start_scrapper(site_name, target_category=None):
    logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger

    feed_format = 'csv'
    feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_result.{feed_format}')

    logger.info(f'feed_uri: {feed_uri}')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    settings = {
        'FEED_FORMAT': feed_format,
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    process = CrawlerProcess(settings=settings)

    process.crawl(HindawiSpider, param={})
    process.start()
