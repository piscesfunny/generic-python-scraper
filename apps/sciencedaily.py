import os
from datetime import datetime

from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.sciencedaily import ScienceDailySpider
from utils.config import OUTPUT_LIST_DIR
from utils.constants import ACTION_SCRAPPING


def start_scrapper(
    site_name,
    action_type,
    target_start_date=None,
    target_end_date=None,
    scraping_target=None
):
    if action_type == ACTION_SCRAPPING:
        feed_format = 'txt'
        target_start_date_dt = datetime.strptime(target_start_date, "%Y-%m-%d")
        target_end_date_dt = datetime.strptime(target_end_date, "%Y-%m-%d")
        result_list_f_path = os.path.join(
            OUTPUT_LIST_DIR,
            f'{site_name}_list_{target_start_date}_{target_end_date}.{feed_format}'
        )

        process = CrawlerProcess()
        process.crawl(ScienceDailySpider, param={
            'target_start_date': target_start_date_dt,
            'target_end_date': target_end_date_dt,
            'scraping_target': scraping_target,
            'result_list_f_path': result_list_f_path
        })

        process.start()
    else:
        pass
