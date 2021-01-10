import os

from scrapy.crawler import CrawlerProcess
from utils.config import *
from utils.constants import *
from farm_machinery.spiders.alibaba import AlibabaSpider


def start_scrapper(existing_fns, action_type, target_category=None, scraping_target=None):
    if action_type == ACTION_GET_CATEGORY:
        feed_uri = os.path.join(OUTPUT_DIR, 'alibaba_categories.json')
    elif action_type == ACTION_SCRAPPING:
        if scraping_target == SCRAPPING_TARGET_LIST:
            feed_uri = os.path.join(OUTPUT_DIR, f'alibaba_{target_category}_list.json')
        else:
            feed_uri = os.path.join(OUTPUT_DIR, 'alibaba.json')
    else:
        pass

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    })

    process.crawl(AlibabaSpider, param={
        'existing_fns': existing_fns,
        'action_type': action_type,
        'target_category': target_category,
        'scraping_target': scraping_target,
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
