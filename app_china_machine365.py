from scrapy.crawler import CrawlerProcess
from generic_scraper.spiders.china_machine365 import ChinaMachine365Spider
from utils.config import *
from settings import SUB_CATEGORY, SUB_CATEGORY_URLS, PAGE_NUM


def start_scrapper(sub_category_url, sub_category, page_num, site_name="china_machin365"):
    # logger = ScraperLogger(label='APPS', log_file=f'{site_name}.log').logger
    feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{sub_category}_result.json')
    processed_url_file = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{sub_category}_processed_urls.csv')
    processed_page_file = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{sub_category}_processed_pages.csv')

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

    process.crawl(ChinaMachine365Spider, param={
        'sub_category': sub_category,
        'sub_category_url': sub_category_url,
        'media_urls_file_path': media_urls_file_path,
        'processed_url_path': processed_url_file,
        'processed_page_path': processed_page_file,
        'item_url_file_path': item_url_file_path,
        'total_page_num': page_num,
        'feed_uri': feed_uri
    })

    process.start()


if __name__ == '__main__':
    for sub_category_ in SUB_CATEGORY_URLS:
        start_scrapper(sub_category=SUB_CATEGORY, sub_category_url=sub_category_, page_num=PAGE_NUM)
