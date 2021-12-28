from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.scitechdaily import SciTechDailySpider
from utils.config import *
from utils.constants import ACTION_GET_LIST


def start_scrapper(site_name, action_type, target_category=None):
    list_dir = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, target_category)
    list_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, target_category, 'urls.txt')
    success_file_path = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_success.txt')
    failed_file_path = os.path.join(OUTPUT_FAILED_DIR, f'{site_name}_{target_category}_failed.txt')

    os.makedirs(list_dir, exist_ok=True)

    f_paths = [list_file_path, failed_file_path]

    for f_path in f_paths:
        if os.path.exists(f_path):
            if action_type == ACTION_GET_LIST:
                os.remove(f_path)
            else:
                if f_path == failed_file_path:
                    os.remove(f_path)

    process = CrawlerProcess()

    process.crawl(SciTechDailySpider, param={
        'action_type': action_type,
        'target_category': target_category,
        'list_file_path': list_file_path,

        'success_file_path': success_file_path,
        'failed_file_path': failed_file_path
    })
    process.start()
