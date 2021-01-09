import os

from scrapy.crawler import CrawlerProcess
from utils.config import OUTPUT_DIR
from farm_machinery.spiders.alibaba import AlibabaSpider


def start_scrapper():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    feed_uri = os.path.join(OUTPUT_DIR, 'alibaba.json')
    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    })

    process.crawl(AlibabaSpider, param={})

    process.start()


if __name__ == '__main__':
    start_scrapper()
