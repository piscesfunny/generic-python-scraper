from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.sweets_construction import SweetsConstructionSpider
from utils.config import *
from utils.logging import ScraperLogger


def start_scrapper(site_name, action_type=None, target_category=None, scraping_target=None):
    logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger

    feed_format = 'json'
    feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_result.{feed_format}')

    logger.info(f'feed_uri: {feed_uri}')

    category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.json')
    list_file_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list.{feed_format}')
    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_media_urls.txt')

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

    process.crawl(SweetsConstructionSpider, param={
        'category_file_path': category_file_path,
        'list_file_path': list_file_path,
        'media_urls_file_path': media_urls_file_path,
        'feed_uri': feed_uri
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()

