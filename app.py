from scrapy.crawler import CrawlerProcess
from utils.config import *
from generic_scraper.spiders.machinio import MachinioSpider
from settings import CATEGORY_URL, SUB_CATEGORY, SUB_CATEGORY_URLS

os.makedirs(OUTPUT_RESULT_DIR, exist_ok=True)
os.makedirs(OUTPUT_MEDIA_URL_LIST_DIR, exist_ok=True)
os.makedirs(OUTPUT_LIST_DIR, exist_ok=True)


def start_scrapper(category_url, sub_category_url, sub_category, site_name="machinio"):
    # logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger

    feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{sub_category}_result.json')
    processed_url_file = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{sub_category}_processed_urls.csv')

    # logger.info(f'feed_uri: {feed_uri}')
    print(f'feed_uri: {feed_uri}')

    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{sub_category}_media_urls.txt')
    item_url_file_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{sub_category}_list.csv')

    # if os.path.exists(feed_uri):
    #     os.remove(feed_uri)
    #
    # if os.path.exists(media_urls_file_path):
    #     os.remove(media_urls_file_path)

    settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    process = CrawlerProcess(settings=settings)

    process.crawl(MachinioSpider, param={
        'category_url': category_url,
        'sub_category': sub_category,
        'sub_category_url': sub_category_url,
        'media_urls_file_path': media_urls_file_path,
        'processed_url_path': processed_url_file,
        'item_url_file_path': item_url_file_path,
        'feed_uri': feed_uri
    })

    process.start()


if __name__ == '__main__':
    for sub_category_ in SUB_CATEGORY_URLS:
        start_scrapper(category_url=CATEGORY_URL, sub_category=SUB_CATEGORY, sub_category_url=sub_category_)
